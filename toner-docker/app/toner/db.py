"""PostgreSQL storage. The app keeps a working copy in memory and writes
changes in small batches, so the database is touched a few times per poll."""
import asyncio
import json

import asyncpg

from . import config
from .logbuf import log

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   text PRIMARY KEY,
    value jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS admins (
    username      text PRIMARY KEY,
    password_hash text NOT NULL,
    must_change   boolean NOT NULL DEFAULT false,
    updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash text PRIMARY KEY,
    id         text UNIQUE NOT NULL,
    username   text NOT NULL,
    created    bigint NOT NULL,
    exp        bigint NOT NULL,
    ip         text,
    ua         text,
    last       bigint NOT NULL
);
CREATE TABLE IF NOT EXISTS printers (
    id        text PRIMARY KEY,
    ip        text,
    source    text,
    record    jsonb NOT NULL,
    last_seen bigint NOT NULL
);
CREATE TABLE IF NOT EXISTS overrides (
    id       text PRIMARY KEY,
    name     text NOT NULL DEFAULT '',
    location text NOT NULL DEFAULT '',
    hidden   boolean NOT NULL DEFAULT false
);
CREATE TABLE IF NOT EXISTS supply_history (
    key text     NOT NULL,
    ts  bigint   NOT NULL,
    pct smallint NOT NULL,
    PRIMARY KEY (key, ts)
);
CREATE INDEX IF NOT EXISTS supply_history_ts ON supply_history (ts);
"""


async def _init_conn(conn):
    await conn.set_type_codec('jsonb', encoder=lambda v: json.dumps(v, ensure_ascii=False),
                              decoder=json.loads, schema='pg_catalog')


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        delay = 1
        while True:
            try:
                self.pool = await asyncpg.create_pool(
                    host=config.DB_HOST, port=config.DB_PORT, database=config.DB_NAME,
                    user=config.DB_USER, password=config.db_password(),
                    min_size=1, max_size=4, init=_init_conn, command_timeout=30,
                    max_inactive_connection_lifetime=300)
                break
            except (OSError, asyncpg.PostgresError, asyncio.TimeoutError) as e:
                log.info('database not ready (%s), retry in %s s', e.__class__.__name__, delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 15)
        async with self.pool.acquire() as c:
            await c.execute(SCHEMA)
        log.info('database connected')

    async def close(self):
        if self.pool:
            await self.pool.close()

    # ---- settings
    async def load_settings(self):
        rows = await self.pool.fetch('SELECT key, value FROM settings')
        return {r['key']: r['value'] for r in rows}

    async def save_settings(self, changes):
        async with self.pool.acquire() as c, c.transaction():
            await c.executemany(
                'INSERT INTO settings(key, value) VALUES($1, $2) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value',
                list(changes.items()))

    # ---- admin
    async def get_admin(self):
        return await self.pool.fetchrow('SELECT username, password_hash, must_change FROM admins ORDER BY username LIMIT 1')

    async def set_admin(self, username, pw_hash, must_change):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute('DELETE FROM admins WHERE username <> $1', username)
            await c.execute(
                'INSERT INTO admins(username, password_hash, must_change, updated_at) VALUES($1, $2, $3, now()) '
                'ON CONFLICT (username) DO UPDATE SET password_hash = $2, must_change = $3, updated_at = now()',
                username, pw_hash, must_change)

    # ---- sessions
    async def load_sessions(self, now):
        await self.pool.execute('DELETE FROM sessions WHERE exp <= $1', now)
        return await self.pool.fetch('SELECT * FROM sessions')

    async def add_session(self, h, s):
        await self.pool.execute(
            'INSERT INTO sessions(token_hash, id, username, created, exp, ip, ua, last) VALUES($1,$2,$3,$4,$5,$6,$7,$8)',
            h, s['id'], s['user'], s['created'], s['exp'], s['ip'], s['ua'], s['last'])

    async def delete_sessions(self, hashes):
        if hashes:
            await self.pool.execute('DELETE FROM sessions WHERE token_hash = ANY($1::text[])', list(hashes))

    async def touch_sessions(self, items):
        if items:
            await self.pool.executemany('UPDATE sessions SET last = $2, ip = $3 WHERE token_hash = $1', items)

    # ---- printers (last known state)
    async def load_printers(self):
        return await self.pool.fetch('SELECT id, record, last_seen FROM printers')

    async def save_printers(self, recs):
        if recs:
            await self.pool.executemany(
                'INSERT INTO printers(id, ip, source, record, last_seen) VALUES($1,$2,$3,$4,$5) '
                'ON CONFLICT (id) DO UPDATE SET ip = EXCLUDED.ip, source = EXCLUDED.source, '
                'record = EXCLUDED.record, last_seen = EXCLUDED.last_seen',
                [(r['id'], r.get('ip'), r.get('source'), r, int(r.get('lastSeen') or 0)) for r in recs])

    async def delete_printers(self, ids):
        if ids:
            await self.pool.execute('DELETE FROM printers WHERE id = ANY($1::text[])', list(ids))

    # ---- overrides
    async def load_overrides(self):
        rows = await self.pool.fetch('SELECT id, name, location, hidden FROM overrides')
        return {r['id']: {'name': r['name'], 'location': r['location'], 'hidden': r['hidden']} for r in rows}

    async def set_override(self, pid, o):
        if o is None:
            await self.pool.execute('DELETE FROM overrides WHERE id = $1', pid)
        else:
            await self.pool.execute(
                'INSERT INTO overrides(id, name, location, hidden) VALUES($1,$2,$3,$4) '
                'ON CONFLICT (id) DO UPDATE SET name = $2, location = $3, hidden = $4',
                pid, o['name'], o['location'], o['hidden'])

    # ---- history
    async def load_history(self, since):
        return await self.pool.fetch('SELECT key, ts, pct FROM supply_history WHERE ts >= $1 ORDER BY key, ts', since)

    async def apply_history(self, ops):
        if not ops:
            return
        async with self.pool.acquire() as c, c.transaction():
            for op in ops:
                if op[0] == 'ins':
                    await c.execute('INSERT INTO supply_history(key, ts, pct) VALUES($1,$2,$3) '
                                    'ON CONFLICT (key, ts) DO UPDATE SET pct = EXCLUDED.pct', op[1], op[2], op[3])
                else:
                    await c.execute('UPDATE supply_history SET ts = $3, pct = $4 WHERE key = $1 AND ts = $2',
                                    op[1], op[2], op[3], op[4])

    async def prune_history(self, before):
        await self.pool.execute('DELETE FROM supply_history WHERE ts < $1', before)

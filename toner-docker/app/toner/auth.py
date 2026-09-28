"""One admin account, cookie sessions and an API token for scripts.

* Passwords: scrypt (N=2^15, r=8, p=1), only the hash is stored.
* Session cookie: 256-bit random token, only its SHA-256 is stored in the DB.
* API token: shown once when issued, only its SHA-256 is stored.
* Brute force: 5 wrong passwords from one address -> 5 min lock;
  20 wrong passwords from anywhere within 15 min -> login locked for 5 min.
"""
import asyncio
import base64
import hashlib
import hmac
import secrets
import time

from . import config
from .logbuf import log

SCRYPT_N, SCRYPT_R, SCRYPT_P = 2 ** 15, 8, 1
COOKIE = 'td_session'
PW_ALPHABET = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def _b64(b):
    return base64.b64encode(b).decode('ascii')


def hash_password(pw):
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(pw.encode('utf-8'), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, maxmem=64 * 1024 * 1024, dklen=32)
    return f'scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64(salt)}${_b64(dk)}'


def verify_password(pw, stored):
    try:
        alg, n, r, p, salt, want = stored.split('$')
        n, r, p = int(n), int(r), int(p)
        if alg != 'scrypt' or n > 2 ** 17 or r > 16 or p > 4:
            return False
        got = hashlib.scrypt(pw.encode('utf-8'), salt=base64.b64decode(salt), n=n, r=r, p=p,
                             maxmem=256 * 1024 * 1024, dklen=32)
        return hmac.compare_digest(got, base64.b64decode(want))
    except Exception:
        return False


def sha256(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def random_password(n=12):
    return ''.join(secrets.choice(PW_ALPHABET) for _ in range(n))


_DUMMY = None


class Auth:
    def __init__(self, db, mon):
        self.db, self.mon = db, mon
        self.admin = None
        self.sessions = {}
        self.touched = {}
        self.fails = {}
        self.global_fails = []
        self.global_until = 0
        self.token_hash = None
        self.token_hint = None

    @property
    def hours(self):
        return max(1, min(720, int(self.mon.cfg.get('sessionHours') or 12)))

    async def run_hash(self, fn, *args):
        return await asyncio.get_running_loop().run_in_executor(None, fn, *args)

    async def load(self):
        global _DUMMY
        _DUMMY = await self.run_hash(hash_password, secrets.token_hex(8))
        row = await self.db.get_admin()
        if row:
            self.admin = dict(row)
        else:
            await self.create_admin(config.ADMIN_USER, config.ADMIN_PASSWORD or None)
        for r in await self.db.load_sessions(int(time.time())):
            self.sessions[r['token_hash']] = {'id': r['id'], 'user': r['username'], 'created': r['created'], 'exp': r['exp'],
                                              'ip': r['ip'], 'ua': r['ua'], 'last': r['last']}
        s = await self.db.load_settings()
        self.token_hash = s.get('apiTokenHash')
        self.token_hint = s.get('apiTokenHint')

    async def create_admin(self, user, password=None):
        """New admin (or password reset). Without a password a one-time start password is generated."""
        must = password is None
        pw = password or random_password()
        h = await self.run_hash(hash_password, pw)
        await self.db.set_admin(user, h, must)
        self.admin = {'username': user, 'password_hash': h, 'must_change': must}
        if must:
            bar = '=' * 64
            log.info(bar)
            log.info('  Start password for "%s":  %s', user, pw)
            log.info('  You will be asked to set your own one at the first login.')
            log.info(bar)
        return pw

    @property
    def user(self):
        return self.admin['username'] if self.admin else config.ADMIN_USER

    @property
    def must_change(self):
        return bool(self.admin and self.admin['must_change'])

    async def check_credentials(self, user, pw):
        ok_user = bool(self.admin) and hmac.compare_digest((user or '').strip().encode(), self.admin['username'].encode())
        stored = self.admin['password_hash'] if ok_user else _DUMMY
        ok = await self.run_hash(verify_password, pw or '', stored)
        return ok and ok_user

    # ---------------------------------------------------------- brute force
    def locked(self, ip, now):
        if self.global_until > now:
            return self.global_until - now
        f = self.fails.get(ip)
        if f and f['until'] > now:
            return f['until'] - now
        return 0

    def register_fail(self, ip, now):
        f = self.fails.get(ip)
        if not f or now - f['first'] > 900:
            f = {'n': 0, 'first': now, 'until': 0}
        f['n'] += 1
        left = 5 - f['n']
        if f['n'] >= 5:
            f.update(until=now + 300, n=0, first=now)
            left = 0
        self.fails[ip] = f
        self.global_fails = [t for t in self.global_fails if now - t < 900] + [now]
        if len(self.global_fails) >= 20:
            self.global_until = now + 300
            self.global_fails = []
            log.info('too many failed logins from different addresses: login locked for 5 min')
        if len(self.fails) > 10000:
            self.fails = {k: v for k, v in self.fails.items() if v['until'] > now}
        return left

    def clear_fails(self, ip):
        self.fails.pop(ip, None)

    # ---------------------------------------------------------- sessions
    async def new_session(self, ip, ua):
        tok = secrets.token_urlsafe(32)
        now = int(time.time())
        s = {'id': secrets.token_hex(6), 'user': self.user, 'created': now, 'exp': now + self.hours * 3600,
             'ip': ip, 'ua': (ua or '')[:200], 'last': now}
        h = sha256(tok)
        self.sessions[h] = s
        await self.db.add_session(h, s)
        return tok, s

    def session_key(self, token, ip):
        if not token or len(token) > 100:
            return None
        k = sha256(token)
        s = self.sessions.get(k)
        if not s:
            return None
        now = int(time.time())
        if s['exp'] <= now:
            self.sessions.pop(k, None)
            asyncio.create_task(self.db.delete_sessions([k]))
            return None
        if now - s['last'] > 60 or s['ip'] != ip:
            s['last'], s['ip'] = now, ip
            self.touched[k] = (k, now, ip)
        return k

    async def flush_touched(self):
        items, self.touched = list(self.touched.values()), {}
        await self.db.touch_sessions(items)

    async def drop_sessions(self, keys):
        keys = [k for k in keys if k in self.sessions]
        for k in keys:
            self.sessions.pop(k, None)
        await self.db.delete_sessions(keys)

    async def change_password(self, new, keep_key):
        h = await self.run_hash(hash_password, new)
        await self.db.set_admin(self.user, h, False)
        self.admin.update(password_hash=h, must_change=False)
        await self.drop_sessions([k for k in list(self.sessions) if k != keep_key])

    # ---------------------------------------------------------- API token
    def check_token(self, tok):
        return bool(self.token_hash and tok) and hmac.compare_digest(sha256(tok), self.token_hash)

    async def new_token(self):
        tok = 'tdk_' + secrets.token_urlsafe(30)
        self.token_hash, self.token_hint = sha256(tok), tok[:8] + '…' + tok[-4:]
        await self.db.save_settings({'apiTokenHash': self.token_hash, 'apiTokenHint': self.token_hint})
        return tok

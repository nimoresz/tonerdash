"""Entry point.

    python -m toner                  run the dashboard (default in the container)
    python -m toner reset-password   new one-time start password, all sessions logged out
"""
import asyncio
import signal
import sys

from aiohttp import web

from . import config
from .auth import Auth
from .db import Database
from .logbuf import log, setup
from .monitor import Monitor
from .server import Server


async def housekeeping(auth):
    while True:
        await asyncio.sleep(120)
        try:
            await auth.flush_touched()
        except Exception as e:
            log.info('session flush failed: %s', e)


async def serve():
    db = Database()
    await db.connect()
    mon = Monitor(db)
    await mon.load()
    auth = Auth(db, mon)
    await auth.load()
    srv = Server(mon, auth)
    srv.load_static()

    runner = web.AppRunner(srv.build(), access_log=None, handle_signals=False)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', config.LISTEN_PORT, backlog=128)
    await site.start()
    mon.start()
    hk = asyncio.create_task(housekeeping(auth))

    log.info('Toner Dashboard %s', config.VERSION)
    log.info('  open http://localhost:%s/  (published on %s:%s)', config.PUBLIC_PORT, config.BIND_ADDR, config.PUBLIC_PORT)
    log.info('  login: %s%s', auth.user, '  (start password is printed above)' if auth.must_change else '')
    if config.DEMO:
        log.info('  DEMO MODE: fake data')

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass
    await stop.wait()
    log.info('stopping...')
    hk.cancel()
    await mon.stop()
    try:
        await auth.flush_touched()
    except Exception:
        pass
    await runner.cleanup()
    await db.close()
    log.info('stopped')


async def reset_password():
    db = Database()
    await db.connect()
    row = await db.get_admin()
    user = row['username'] if row else config.ADMIN_USER
    mon = Monitor(db)
    auth = Auth(db, mon)
    await auth.create_admin(user)
    await db.pool.execute('DELETE FROM sessions')
    print('All sessions were logged out. The running dashboard picks the new password up after a restart:')
    print('  docker compose restart app')
    await db.close()


def main():
    setup()
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'serve'
    if cmd == 'serve':
        asyncio.run(serve())
    elif cmd == 'reset-password':
        asyncio.run(reset_password())
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()

"""HTTP server: dashboard page, JSON API (same paths as the PowerShell version), security."""
import asyncio
import gzip
import hashlib
import json
import os
import re
import time
from collections import Counter
from urllib.parse import unquote, urlsplit

from aiohttp import web

from . import config
from .auth import COOKIE
from .logbuf import BUFFER, log
from .monitor import allowed_target, iso, valid_ip

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'")
CTYPES = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
          '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
          '.woff2': 'font/woff2', '.ico': 'image/x-icon', '.json': 'application/json; charset=utf-8'}
JSON_CT = 'application/json; charset=utf-8'
RX_SUBNET = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(/(1[6-9]|2\d|3[0-2]))?$')

API_DOCS = [
    ('GET', '/api/printers', 'state=crit,warn  q=text  location=  model=  subnet=192.168.3.  vendor=HP,Canon', 'All printers with supplies (supports ETag / If-None-Match)'),
    ('GET', '/api/printers/{id}', '', 'One printer, id = IP address'),
    ('GET', '/api/printers/{id}/supplies', '', 'Supplies of one printer'),
    ('GET', '/api/printers/{id}/history', 'days=30', 'Level history per supply: [[unixTime, percent], ...]'),
    ('POST', '/api/printers/{id}/refresh', '', 'Poll this printer right now'),
    ('GET', '/api/supplies', 'state=crit,warn  kind=toner,drum,fuser,waste,belt,roller,kit,dev,ink,staple,other  q=  printer=  location=', 'Flat list of all supplies'),
    ('GET', '/api/replace', 'days=14', 'What needs replacing: low supplies'),
    ('GET', '/api/summary', '', 'Counters and low supplies'),
    ('GET', '/api/stats', '', 'Fleet statistics: pages, average toner, by model / location / subnet'),
    ('GET', '/api/metrics', '', 'Prometheus metrics (for Grafana / Zabbix)'),
    ('GET', '/api/export.csv', 'same filters as /api/supplies', 'CSV for Excel (semicolon, UTF-8 BOM)'),
    ('GET', '/api/config', '', 'Effective configuration (without SNMP community)'),
    ('GET', '/api/health', '', 'Poller status and progress'),
    ('POST', '/api/refresh', '', 'Poll all printers now'),
    ('POST', '/api/discover', '', 'Rescan subnets now, then poll'),
    ('POST', '/api/auth/login', '', 'Log in: {"user":"admin","password":"..."} -> session cookie'),
    ('POST', '/api/auth/logout', '', 'Log out (drops the session cookie)'),
    ('GET', '/api/auth/me', '', 'Current session: user, expiry'),
    ('POST', '/api/auth/password', '', 'Change password: {"current":"...","new":"..."}'),
    ('GET', '/api/auth/sessions', '', 'Active sessions; POST /api/auth/sessions/{id}/revoke to end one'),
    ('POST', '/api/auth/token', '', 'Issue a new API token (shown once, the old one stops working)'),
    ('GET', '/api/admin/status', '', 'Server status: uptime, memory, last poll, sessions'),
    ('POST', '/api/admin/probe', '', 'SNMP request to any LAN IP: {"ip":"192.168.3.40","community":"public"} -> job id'),
    ('GET', '/api/admin/probe/{job}', '', 'Probe result: printer record + raw OID values'),
    ('POST', '/api/admin/printers', '', 'Add printer to monitoring: {"ip":"..."}'),
    ('POST', '/api/admin/printers/{id}/override', '', 'Rename / set location / hide: {"name","location","hidden"}'),
    ('POST', '/api/admin/printers/{id}/remove', '', 'Remove a manually added printer, {"exclude":true} to ignore it in scans'),
    ('GET', '/api/admin/config', '', 'Settings; POST the same fields to change them live'),
    ('GET', '/api/admin/log', 'lines=300', 'Poller log'),
]


def dumps(o):
    return json.dumps(o, ensure_ascii=False, separators=(',', ':'), default=str)


def accepts_gzip(request):
    return 'gzip' in request.headers.get('Accept-Encoding', '')


def respond(request, body, ctype=JSON_CT, status=200, headers=None, gz=None):
    if isinstance(body, str):
        body = body.encode('utf-8')
    h = dict(headers or {})
    if accepts_gzip(request) and len(body) > 1024 and status != 304:
        body = gz if gz is not None else gzip.compress(body, 5)
        h['Content-Encoding'] = 'gzip'
        h['Vary'] = 'Accept-Encoding'
    h['Content-Type'] = ctype
    return web.Response(body=body, status=status, headers=h)


def jr(request, obj, status=200, headers=None):
    return respond(request, dumps(obj), JSON_CT, status, headers)


def err(request, status, msg, **extra):
    return jr(request, dict({'error': msg}, **extra), status)


def to_int(v, default):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


async def read_json(request):
    try:
        b = await request.json()
        return b if isinstance(b, dict) else {}
    except Exception:
        return {}


class Server:
    def __init__(self, mon, auth):
        self.mon, self.auth = mon, auth
        self.static = {}
        self.pcache = (None, None, None)
        self.tasks = set()

    def spawn(self, coro):
        t = asyncio.create_task(coro)
        self.tasks.add(t)
        t.add_done_callback(self.tasks.discard)

    # ------------------------------------------------------------ static
    def load_static(self):
        for root, _, files in os.walk(config.STATIC_DIR):
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, config.STATIC_DIR).replace(os.sep, '/')
                ext = os.path.splitext(f)[1].lower()
                with open(p, 'rb') as fh:
                    data = fh.read()
                gz = gzip.compress(data, 9) if ext in ('.js', '.css', '.html', '.svg', '.json') else None
                self.static[rel] = (data, gz, CTYPES.get(ext, 'application/octet-stream'),
                                    '"' + hashlib.sha256(data).hexdigest()[:20] + '"')
        log.info('static files: %d', len(self.static))

    def serve_static(self, request, rel):
        item = self.static.get(rel)
        if not item:
            return err(request, 404, 'not found')
        data, gz, ctype, etag = item
        cache = 'public, max-age=604800' if rel.startswith('fonts/') else 'no-cache'
        h = {'ETag': etag, 'Cache-Control': cache}
        if request.headers.get('If-None-Match') == etag:
            return web.Response(status=304, headers=h)
        if gz is not None and accepts_gzip(request):
            h.update({'Content-Encoding': 'gzip', 'Vary': 'Accept-Encoding', 'Content-Type': ctype})
            return web.Response(body=gz, headers=h)
        h['Content-Type'] = ctype
        return web.Response(body=data, headers=h)

    def logo(self, request):
        for ext in ('svg', 'png', 'jpg', 'jpeg', 'webp'):
            p = os.path.join(config.BRANDING_DIR, 'logo.' + ext)
            if os.path.isfile(p) and os.path.getsize(p) < 2 * 1024 * 1024:
                with open(p, 'rb') as fh:
                    data = fh.read()
                return web.Response(body=data, headers={
                    'Content-Type': CTYPES['.' + ext], 'Cache-Control': 'no-cache',
                    'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; sandbox"})
        return err(request, 404, 'no logo')

    # ------------------------------------------------------------ plumbing
    @staticmethod
    async def on_prepare(request, response):
        h = response.headers
        h['X-Content-Type-Options'] = 'nosniff'
        h['X-Frame-Options'] = 'DENY'
        h['Referrer-Policy'] = 'no-referrer'
        h['Cross-Origin-Opener-Policy'] = 'same-origin'
        h['Cross-Origin-Resource-Policy'] = 'same-origin'
        h['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()'
        h.setdefault('Content-Security-Policy', CSP)
        h['Server'] = 'toner'
        if config.COOKIE_SECURE:
            h['Strict-Transport-Security'] = 'max-age=31536000'
        if request.path.startswith('/api'):
            h['Cache-Control'] = 'no-store'

    @staticmethod
    def csrf_ok(request):
        """State-changing requests must come from our own page (custom header + same origin) or carry a token."""
        hd = request.headers
        if hd.get('Authorization') or hd.get('X-Api-Key'):
            return True
        if hd.get('X-Requested-With') != 'fetch':
            return False
        sfs = hd.get('Sec-Fetch-Site')
        if sfs and sfs not in ('same-origin', 'none'):
            return False
        origin = hd.get('Origin')
        if origin and origin != 'null' and urlsplit(origin).netloc.lower() != (request.host or '').lower():
            return False
        return True

    @staticmethod
    def bearer(request):
        h = request.headers.get('Authorization', '')
        m = re.match(r'^\s*Bearer\s+(\S+)\s*$', h)
        if m:
            return m.group(1)
        return request.headers.get('X-Api-Key', '').strip() or None

    async def handle(self, request):
        try:
            return await self.dispatch(request)
        except web.HTTPException:
            raise
        except Exception:
            log.exception('request %s %s failed', request.method, request.path)
            return err(request, 500, 'internal')

    async def dispatch(self, request):
        path = request.path
        if len(path) > 1:
            path = path.rstrip('/')
        method = request.method
        if method == 'HEAD':
            method = 'GET'
        if path in ('/', '/index.html'):
            return self.serve_static(request, 'index.html')
        if path.startswith('/static/'):
            return self.serve_static(request, path[8:])
        if path == '/healthz':
            return web.Response(text='ok', content_type='text/plain')
        if path == '/logo':
            return self.logo(request)
        if path == '/favicon.ico':
            return web.Response(status=204)
        if not (path == '/api' or path.startswith('/api/')):
            return err(request, 404, 'not found')
        if method not in ('GET', 'POST'):
            return err(request, 405, 'method not allowed')
        if method == 'POST' and not self.csrf_ok(request):
            return err(request, 403, 'cross-site request refused')

        ip = request.remote or '?'
        if path.startswith('/api/auth/'):
            return await self.auth_api(request, path, method, ip)

        key = self.auth.session_key(request.cookies.get(COOKIE), ip)
        if not key:
            if not self.auth.check_token(self.bearer(request)):
                return err(request, 401, 'login required')
            if path.startswith('/api/admin/') and method == 'POST':
                return err(request, 403, 'admin changes need a browser session')
        elif self.auth.must_change:
            return err(request, 403, 'password change required')

        if path.startswith('/api/admin/'):
            return await self.admin_api(request, path, method)
        return await self.main_api(request, path, method)

    # ------------------------------------------------------------ helpers
    def meta(self):
        m = self.mon
        c = m.cfg
        return {'version': config.VERSION, 'server': config.SERVER_NAME, 'orgName': c['orgName'], 'siteName': c['siteName'],
                'updated': iso(m.updated), 'polling': m.polling, 'pollSeconds': max(30, int(c['pollSeconds'])),
                'warnPct': c['warnPct'], 'critPct': c['critPct'], 'demo': m.demo, 'subnets': list(c['subnets']),
                'lastError': m.last_error, 'progress': m.progress}

    def with_meta(self, key, obj):
        return dict(self.meta(), **{key: obj})

    @staticmethod
    def printer_match(r, q):
        if q.get('state') and r['state'] not in q['state'].split(','):
            return False
        if q.get('q'):
            hay = ' '.join(str(x or '') for x in [r['name'], r['model'], r['ip'], r['location'], r['serial']]
                           + [s['name'] for s in r['supplies']]).lower()
            if q['q'].lower() not in hay:
                return False
        if q.get('location') and q['location'].lower() not in str(r['location'] or '').lower():
            return False
        if q.get('model') and q['model'].lower() not in str(r['model'] or '').lower():
            return False
        if q.get('subnet') and not str(r['ip'] or '').startswith(q['subnet']):
            return False
        if q.get('vendor') and str(r['vendor'] or '') not in q['vendor'].split(','):
            return False
        return True

    def flat_supplies(self, q):
        out = []
        for r in self.mon.records:
            if r.get('hidden'):
                continue
            if q.get('vendor') and str(r['vendor'] or '') not in q['vendor'].split(','):
                continue
            if q.get('printer') and q['printer'].lower() not in f"{r['name']} {r['ip']}".lower():
                continue
            if q.get('location') and q['location'].lower() not in str(r['location'] or '').lower():
                continue
            for s in r['supplies']:
                if q.get('state') and s['state'] not in q['state'].split(','):
                    continue
                if q.get('kind') and s['kind'] not in q['kind'].split(','):
                    continue
                if q.get('q') and q['q'].lower() not in f"{r['name']} {s['name']} {s.get('code') or ''}".lower():
                    continue
                out.append({'printerId': r['id'], 'printer': r['name'], 'ip': r['ip'], 'location': r['location'],
                            'model': r['model'], 'vendor': r['vendor'], 'supply': s['name'], 'kind': s['kind'],
                            'kindName': s['kindName'], 'color': s['tint'], 'code': s.get('code'), 'pct': s['pct'],
                            'state': s['state'], 'daysLeft': s.get('daysLeft'), 'perDay': s.get('perDay')})
        return out

    @staticmethod
    def by_pct(lst):
        return sorted(lst, key=lambda s: 999 if s['pct'] is None else s['pct'])

    # ------------------------------------------------------------ main API
    async def main_api(self, request, path, method):
        q = {k.lower(): v.strip() for k, v in request.query.items()}
        m = self.mon
        if path == '/api':
            return jr(request, {'name': 'Toner Dashboard API', 'version': config.VERSION, 'endpoints': [
                dict({'method': a, 'path': b, 'description': d}, **({'query': c} if c else {})) for a, b, c, d in API_DOCS]})
        if path == '/api/health':
            return jr(request, self.meta())
        if path == '/api/config':
            c = m.cfg
            return jr(request, {k: c[k] for k in ('orgName', 'siteName', 'subnets', 'extraIps', 'excludeIps', 'pollSeconds',
                                                 'discoveryMinutes', 'warnPct', 'critPct', 'historyDays', 'forgetDays', 'hideWaste')})
        if path == '/api/printers':
            if not q:
                p = m.progress
                etag = f'"{m.seq}-{int(m.polling)}' + (f"-{p['phase']}{p['done']}" if p else '') + '"'
                if request.headers.get('If-None-Match') == etag:
                    return web.Response(status=304, headers={'ETag': etag})
                if self.pcache[0] != etag:
                    meta = dumps(self.meta())
                    body = (meta[:-1] + ',"printers":' + m.printers_json + '}').encode('utf-8')
                    self.pcache = (etag, body, gzip.compress(body, 5))
                return respond(request, self.pcache[1], headers={'ETag': etag}, gz=self.pcache[2])
            lst = sorted((r for r in m.records if self.printer_match(r, q)), key=lambda r: r['name'])
            return jr(request, self.with_meta('printers', lst))

        mm = re.match(r'^/api/printers/([^/]+)(?:/(supplies|history|refresh))?$', path)
        if mm:
            pid, sub = unquote(mm.group(1)), mm.group(2)
            r = m.by_id.get(pid)
            if not r:
                return err(request, 404, 'printer not found')
            if not sub:
                return jr(request, r)
            if sub == 'supplies':
                return jr(request, r['supplies'])
            if sub == 'history':
                days = max(1, min(3650, to_int(q.get('days'), 30)))
                cut = int(time.time()) - days * 86400
                series = []
                for s in r['supplies']:
                    pts = [p for p in m.hist.get(f"{r['ip']}|{s['index']}|{s.get('rawName', s['name'])}", []) if p[0] >= cut]
                    series.append({'supply': s['name'], 'kind': s['kind'], 'color': s['tint'], 'code': s.get('code'),
                                   'points': pts or s.get('spark') or []})
                return jr(request, {'id': r['id'], 'printer': r['name'], 'days': days, 'series': series})
            if method != 'POST':
                return err(request, 405, 'use POST')
            self.spawn(m.poll_one(pid))
            return jr(request, {'ok': True, 'queued': True}, 202)

        if path == '/api/supplies':
            return jr(request, self.with_meta('supplies', self.by_pct(self.flat_supplies(q))))
        if path == '/api/replace':
            days = to_int(q.get('days'), -1)
            q2 = {k: v for k, v in q.items() if k not in ('days', 'state')}
            lst = [s for s in self.flat_supplies(q2) if s['state'] in ('crit', 'warn')
                   or (days >= 0 and s['daysLeft'] is not None and s['daysLeft'] <= days)]
            return jr(request, self.with_meta('replace', self.by_pct(lst)))
        if path == '/api/summary':
            counts = {'total': 0, 'crit': 0, 'warn': 0, 'ok': 0, 'nodata': 0, 'offline': 0, 'noip': 0}
            for r in m.records:
                counts['total'] += 1
                if r['state'] in counts:
                    counts[r['state']] += 1
            return jr(request, dict(self.meta(), counts=counts, low=self.by_pct(self.flat_supplies({'state': 'crit,warn'}))))
        if path == '/api/stats':
            return jr(request, self.with_meta('stats', self.stats()))
        if path == '/api/metrics':
            return respond(request, self.metrics(), 'text/plain; version=0.0.4; charset=utf-8')
        if path in ('/api/export.csv', '/api/export'):
            return respond(request, self.csv(q), 'text/csv; charset=utf-8',
                           headers={'Content-Disposition': 'attachment; filename="toner.csv"'})
        if path in ('/api/refresh', '/api/discover'):
            if method != 'POST':
                return err(request, 405, 'use POST')
            if path == '/api/discover':
                m.force_discovery = True
            m.force_poll.set()
            return jr(request, {'ok': True}, 202)
        return err(request, 404, 'not found', help='/api')

    def stats(self):
        ps = [r for r in self.mon.records if not r.get('hidden')]
        states = {'total': len(ps), 'crit': 0, 'warn': 0, 'ok': 0, 'nodata': 0, 'offline': 0, 'noip': 0}
        pages = 0
        for r in ps:
            if r['state'] in states:
                states[r['state']] += 1
            pages += int(r.get('pages') or 0)

        def group(fn, name, by_count=True):
            c = Counter(fn(r) for r in ps)
            items = sorted(c.items(), key=(lambda x: -x[1]) if by_count else (lambda x: x[0]))
            return [{name: k, 'count': v} for k, v in items]

        sup = self.flat_supplies({})
        kinds = dict(Counter(s['kind'] for s in sup))
        tn = [s['pct'] for s in sup if s['kind'] in ('toner', 'ink') and s['pct'] is not None]
        subnet = lambda r: '.'.join(r['ip'].split('.')[:3]) + '.0/24' if valid_ip(r.get('ip') or '') else '?'
        return {
            'printers': states, 'totalPages': pages, 'avgTonerPct': round(sum(tn) / len(tn), 1) if tn else None,
            'supplies': {'crit': sum(s['state'] == 'crit' for s in sup), 'warn': sum(s['state'] == 'warn' for s in sup), 'total': len(sup)},
            'supplyKinds': kinds, 'nearestReplacement': None,
            'byVendor': group(lambda r: r['vendor'] or '?', 'vendor'),
            'byModel': group(lambda r: r['model'] or '?', 'model'),
            'byLocation': group(lambda r: str(r['location'] or '').split(',')[0].strip() or '?', 'location', False),
            'bySubnet': group(subnet, 'subnet', False),
        }

    def metrics(self):
        def L(v):
            return '"' + str(v if v is not None else '').replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ') + '"'
        rs = self.mon.records
        out = ['# HELP toner_printer_up 1 if the printer answers', '# TYPE toner_printer_up gauge']
        out += [f"toner_printer_up{{id={L(r['id'])},printer={L(r['name'])},ip={L(r['ip'])},location={L(r['location'])},state={L(r['state'])}}} {int(bool(r['online']))}" for r in rs]
        out += ['# HELP toner_printer_pages_total Page counter', '# TYPE toner_printer_pages_total counter']
        out += [f"toner_printer_pages_total{{id={L(r['id'])},printer={L(r['name'])}}} {r['pages']}" for r in rs if r.get('pages') is not None]
        out += ['# HELP toner_supply_level_percent Remaining supply level, percent', '# TYPE toner_supply_level_percent gauge']
        out += [f"toner_supply_level_percent{{id={L(s['printerId'])},printer={L(s['printer'])},supply={L(s['supply'])},kind={L(s['kind'])},color={L(s['color'])},code={L(s['code'])}}} {s['pct']}"
                for s in self.flat_supplies({}) if s['pct'] is not None]
        if self.mon.updated:
            out.append(f'toner_last_poll_timestamp_seconds {self.mon.updated}')
        return '\n'.join(out) + '\n'

    def csv(self, q):
        def Q(v):
            x = '' if v is None else str(v)
            if x[:1] in ('=', '+', '-', '@'):     # no formula injection when opened in Excel
                x = "'" + x
            return '"' + x.replace('"', '""') + '"' if re.search(r'[;"\r\n]', x) else x
        rows = ['\ufeff' + ';'.join(['Принтер', 'Расположение', 'IP', 'Модель', 'Расходник', 'Тип', 'Артикул', 'Остаток, %', 'Состояние'])]
        for s in sorted(self.flat_supplies(q), key=lambda s: (s['printer'] or '', s['supply'] or '')):
            rows.append(';'.join(Q(s[k]) for k in ('printer', 'location', 'ip', 'model', 'supply', 'kindName', 'code', 'pct', 'state')))
        return '\r\n'.join(rows) + '\r\n'

    # ------------------------------------------------------------ auth API
    def cookie(self, resp, value, max_age):
        resp.set_cookie(COOKIE, value, max_age=max_age, path='/', httponly=True, samesite='Strict', secure=config.COOKIE_SECURE)
        return resp

    async def auth_api(self, request, path, method, ip):
        a = self.auth
        now = int(time.time())
        if path == '/api/auth/login':
            if method != 'POST':
                return err(request, 405, 'use POST')
            wait = a.locked(ip, now)
            if wait:
                return jr(request, {'ok': False, 'error': 'locked', 'retry': wait}, 429)
            b = await read_json(request)
            user, pw = str(b.get('user') or '')[:64], str(b.get('password') or '')[:256]
            if user and pw and await a.check_credentials(user, pw):
                a.clear_fails(ip)
                tok, s = await a.new_session(ip, request.headers.get('User-Agent', ''))
                log.info('login: %s from %s', a.user, ip)
                resp = jr(request, {'ok': True, 'user': a.user, 'exp': s['exp'], 'hours': a.hours, 'mustChange': a.must_change})
                return self.cookie(resp, tok, a.hours * 3600)
            left = a.register_fail(ip, now)
            log.info('failed login from %s', ip)
            await asyncio.sleep(0.6)
            if a.locked(ip, now):
                return jr(request, {'ok': False, 'error': 'locked', 'retry': a.locked(ip, now)}, 429)
            return jr(request, {'ok': False, 'error': 'wrong', 'attemptsLeft': left}, 401)
        if path == '/api/auth/info':
            return jr(request, {'hours': a.hours})
        key = a.session_key(request.cookies.get(COOKIE), ip)
        if path == '/api/auth/logout':
            if key:
                await a.drop_sessions([key])
            return self.cookie(jr(request, {'ok': True}), '', 0)
        if not key:
            return err(request, 401, 'login required')
        s = a.sessions[key]
        if path == '/api/auth/me':
            return jr(request, {'user': s['user'], 'exp': s['exp'], 'created': s['created'], 'hours': a.hours,
                                'mustChange': a.must_change, 'session': s['id']})
        if path == '/api/auth/password' and method == 'POST':
            b = await read_json(request)
            cur, new = str(b.get('current') or ''), str(b.get('new') or '')
            if a.locked(ip, now):
                return jr(request, {'ok': False, 'error': 'locked'}, 429)
            if not await a.check_credentials(a.user, cur):
                a.register_fail(ip, now)
                await asyncio.sleep(0.6)
                return jr(request, {'ok': False, 'error': 'current'}, 400)
            if len(new) < 8:
                return jr(request, {'ok': False, 'error': 'short'}, 400)
            if len(new) > 256:
                return jr(request, {'ok': False, 'error': 'long'}, 400)
            if new == cur or new.lower() == a.user.lower():
                return jr(request, {'ok': False, 'error': 'weak'}, 400)
            await a.change_password(new, key)
            log.info('password changed from %s', ip)
            return jr(request, {'ok': True})
        if a.must_change:
            return err(request, 403, 'password change required')
        if path == '/api/auth/sessions':
            lst = [{'id': v['id'], 'ip': v['ip'], 'ua': v['ua'], 'created': v['created'], 'exp': v['exp'],
                    'last': v['last'], 'current': k == key} for k, v in a.sessions.items()]
            return jr(request, sorted(lst, key=lambda x: -x['last']))
        mm = re.match(r'^/api/auth/sessions/([0-9a-f]{1,32})/revoke$', path)
        if mm and method == 'POST':
            await a.drop_sessions([k for k, v in a.sessions.items() if v['id'] == mm.group(1) and k != key])
            return jr(request, {'ok': True})
        if path == '/api/auth/sessions/revoke-others' and method == 'POST':
            await a.drop_sessions([k for k in a.sessions if k != key])
            return jr(request, {'ok': True})
        if path == '/api/auth/token':
            if method == 'POST':
                tok = await a.new_token()
                log.info('new API token issued from %s', ip)
                return jr(request, {'token': tok, 'exists': True, 'hint': a.token_hint})
            return jr(request, {'exists': bool(a.token_hash), 'hint': a.token_hint})
        return err(request, 404, 'not found')

    # ------------------------------------------------------------ admin API
    def admin_config(self):
        c = self.mon.cfg
        out = {k: c[k] for k in ('orgName', 'siteName', 'warnPct', 'critPct', 'pollSeconds', 'discoveryMinutes', 'community',
                                 'subnets', 'extraIps', 'excludeIps', 'forgetDays', 'hideWaste', 'sessionHours', 'historyDays')}
        out.update(adminUser=self.auth.user, port=config.PUBLIC_PORT, bind=config.BIND_ADDR, storage='PostgreSQL',
                   demo=self.mon.demo)
        return out

    async def admin_api(self, request, path, method):
        m = self.mon
        if path == '/api/admin/status':
            rs = m.records
            mem = None
            try:
                with open('/proc/self/status') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            mem = round(int(line.split()[1]) / 1024)
            except OSError:
                pass
            return jr(request, {
                'version': config.VERSION, 'server': config.SERVER_NAME, 'started': iso(int(m.started)),
                'uptimeSec': int(time.time() - m.started), 'memoryMB': mem, 'lastCycleSec': m.last_cycle_sec,
                'lastDiscovery': iso(int(m.last_discovery)) if m.last_discovery else None, 'discovered': len(m.discovered),
                'printers': len(rs), 'online': sum(1 for r in rs if r['online']),
                'offline': sum(1 for r in rs if r['state'] == 'offline'), 'hidden': sum(1 for r in rs if r.get('hidden')),
                'pollSeconds': max(30, int(m.cfg['pollSeconds'])), 'discoveryMinutes': m.cfg['discoveryMinutes'],
                'sessions': len(self.auth.sessions), 'polling': m.polling, 'lastError': m.last_error})

        if path == '/api/admin/probe' and method == 'POST':
            b = await read_json(request)
            ip, com = str(b.get('ip') or '').strip(), str(b.get('community') or '').strip()
            if not valid_ip(ip) or not allowed_target(ip):
                return err(request, 400, 'bad ip: only private LAN addresses are allowed')
            if len(com) > 64 or not com.isprintable():
                return err(request, 400, 'bad community')
            jid = m.start_probe(ip, com)
            if not jid:
                return err(request, 429, 'too many probes, wait a bit')
            return jr(request, {'id': jid, 'queued': True}, 202)
        mm = re.match(r'^/api/admin/probe/([0-9a-f]{1,32})$', path)
        if mm:
            r = m.probes.get(mm.group(1))
            if not r:
                return err(request, 404, 'unknown job')
            return jr(request, {k: v for k, v in r.items() if not k.startswith('_')})

        if path == '/api/admin/printers' and method == 'POST':
            b = await read_json(request)
            ip = str(b.get('ip') or '').strip()
            if not valid_ip(ip) or not allowed_target(ip):
                return err(request, 400, 'bad ip: only private LAN addresses are allowed')
            extra = [x for x in m.cfg['extraIps'] if x != ip] + [ip]
            if len(extra) > 2000:
                return err(request, 400, 'too many printers')
            await m.save_settings({'extraIps': extra, 'excludeIps': [x for x in m.cfg['excludeIps'] if x != ip]})
            self.spawn(m.poll_one(ip))
            return jr(request, {'ok': True})
        mm = re.match(r'^/api/admin/printers/([^/]+)/(remove|override)$', path)
        if mm and method == 'POST':
            pid, act = unquote(mm.group(1))[:64], mm.group(2)
            b = await read_json(request)
            if act == 'remove':
                ch = {'extraIps': [x for x in m.cfg['extraIps'] if x != pid]}
                if b.get('exclude') and valid_ip(pid):
                    ch['excludeIps'] = [x for x in m.cfg['excludeIps'] if x != pid] + [pid]
                await m.save_settings(ch)
                await m.remove(pid)
                return jr(request, {'ok': True})
            o = {'name': str(b.get('name') or '').strip()[:120], 'location': str(b.get('location') or '').strip()[:200],
                 'hidden': bool(b.get('hidden'))}
            if not o['name'] and not o['location'] and not o['hidden']:
                m.overrides.pop(pid, None)
                await m.db.set_override(pid, None)
            else:
                m.overrides[pid] = o
                await m.db.set_override(pid, o)
            m.republish()
            return jr(request, {'ok': True})

        if path == '/api/admin/config':
            if method == 'POST':
                b = await read_json(request)
                if not b:
                    return err(request, 400, 'bad json')
                bad = await self.apply_config(b)
                if isinstance(bad, dict):
                    return jr(request, bad, 400)
            return jr(request, self.admin_config())

        if path == '/api/admin/log':
            n = max(1, min(2000, to_int(request.query.get('lines'), 300)))
            return jr(request, {'file': 'docker compose logs app', 'lines': list(BUFFER)[-n:]})
        if path == '/api/admin/discover' and method == 'POST':
            m.force_discovery = True
            m.force_poll.set()
            return jr(request, {'ok': True}, 202)
        return err(request, 404, 'not found')

    async def apply_config(self, b):
        m = self.mon
        c, ch = m.cfg, {}

        def num(k, lo, hi):
            try:
                ch[k] = max(lo, min(hi, int(b[k])))
            except (TypeError, ValueError):
                pass
        for k, n in (('orgName', 120), ('siteName', 120)):
            if k in b:
                ch[k] = str(b[k] or '').strip()[:n]
        if 'warnPct' in b:
            num('warnPct', 1, 99)
        if 'critPct' in b:
            num('critPct', 0, 99)
            ch['critPct'] = min(ch.get('critPct', c['critPct']), ch.get('warnPct', c['warnPct']))
        if 'pollSeconds' in b:
            num('pollSeconds', 30, 86400)
        if 'discoveryMinutes' in b:
            num('discoveryMinutes', 5, 10080)
        if 'forgetDays' in b:
            num('forgetDays', 1, 3650)
        if 'historyDays' in b:
            num('historyDays', 7, 3650)
        if 'sessionHours' in b:
            num('sessionHours', 1, 720)
        if b.get('community'):
            com = str(b['community']).strip()
            if len(com) > 64 or not com.isprintable():
                return {'error': 'bad community'}
            ch['community'] = com
        if 'hideWaste' in b:
            ch['hideWaste'] = bool(b['hideWaste'])
            m.force_poll.set()
        if 'subnets' in b:
            items = [str(x).strip() for x in (b['subnets'] or []) if str(x).strip()]
            bad = [x for x in items if not RX_SUBNET.match(x) or not allowed_target(x.split('/')[0])]
            if bad or len(items) > 64:
                return {'error': 'bad subnet', 'items': bad}
            ch['subnets'] = list(dict.fromkeys(items))
            m.force_discovery = True
        if 'excludeIps' in b:
            ch['excludeIps'] = [str(x).strip() for x in (b['excludeIps'] or []) if valid_ip(str(x).strip())][:5000]
        if ch:
            if ch.keys() & {'warnPct', 'critPct'}:
                m.force_poll.set()
            await m.save_settings(ch)
            m.republish()
        return None

    # ------------------------------------------------------------ app
    def build(self):
        app = web.Application(client_max_size=64 * 1024)
        app.on_response_prepare.append(self.on_prepare)
        app.router.add_route('*', '/{tail:.*}', self.handle)
        return app

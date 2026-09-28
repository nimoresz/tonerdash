"""Printer poller: subnet discovery, SNMP polling, web-page fallback,
level history, last known state and demo data."""
import asyncio
import datetime
import ipaddress
import json
import math
import secrets
import time

from . import classify as C
from . import config
from .logbuf import log
from .snmp import V1, V2C, SnmpSession, SnmpTimeout, SnmpUnreachable
from .webscrape import WebScraper

OID = {
    'SysDescr': '1.3.6.1.2.1.1.1.0', 'SysName': '1.3.6.1.2.1.1.5.0', 'SysLocation': '1.3.6.1.2.1.1.6.0',
    'SysObjectId': '1.3.6.1.2.1.1.2.0', 'Model': '1.3.6.1.2.1.25.3.2.1.3.1', 'DevStatus': '1.3.6.1.2.1.25.3.2.1.5.1',
    'PrnStatus': '1.3.6.1.2.1.25.3.5.1.1.1', 'ErrState': '1.3.6.1.2.1.25.3.5.1.2.1',
    'PrtName': '1.3.6.1.2.1.43.5.1.1.16.1', 'Serial': '1.3.6.1.2.1.43.5.1.1.17.1', 'Pages': '1.3.6.1.2.1.43.10.2.1.4.1.1',
}
CONSOLE = '1.3.6.1.2.1.43.16.5.1.2.1.'
SUP = {
    'colorant': '1.3.6.1.2.1.43.11.1.1.3.1.', 'cls': '1.3.6.1.2.1.43.11.1.1.4.1.', 'type': '1.3.6.1.2.1.43.11.1.1.5.1.',
    'desc': '1.3.6.1.2.1.43.11.1.1.6.1.', 'unit': '1.3.6.1.2.1.43.11.1.1.7.1.', 'max': '1.3.6.1.2.1.43.11.1.1.8.1.',
    'level': '1.3.6.1.2.1.43.11.1.1.9.1.',
}
COLORANT_VAL = '1.3.6.1.2.1.43.12.1.1.4.1.'
# Pantum keeps supplies in its own enterprise branch, not in Printer-MIB
PANTUM = {
    'toner': '1.3.6.1.4.1.40093.6.3.1', 'tonerModel': '1.3.6.1.4.1.40093.10.1.5.2.1.5.4',
    'drum': '1.3.6.1.4.1.40093.8.1.4', 'drumModel': '1.3.6.1.4.1.40093.8.1.3', 'pages': '1.3.6.1.4.1.40093.10.3.1.1',
}
DISCOVERY_OIDS = ['1.3.6.1.2.1.43.5.1.1.1.1', '1.3.6.1.2.1.43.11.1.1.6.1.1', PANTUM['toner'], PANTUM['toner'] + '.0']
RAW_LIST = [
    ('sysDescr', '1.3.6.1.2.1.1.1.0'), ('sysObjectID', '1.3.6.1.2.1.1.2.0'), ('sysName', '1.3.6.1.2.1.1.5.0'),
    ('sysLocation', '1.3.6.1.2.1.1.6.0'), ('sysUpTime', '1.3.6.1.2.1.1.3.0'), ('hrDeviceDescr', '1.3.6.1.2.1.25.3.2.1.3.1'),
    ('hrDeviceStatus', '1.3.6.1.2.1.25.3.2.1.5.1'), ('hrPrinterStatus', '1.3.6.1.2.1.25.3.5.1.1.1'),
    ('hrPrinterDetectedErrorState', '1.3.6.1.2.1.25.3.5.1.2.1'), ('prtGeneralPrinterName', '1.3.6.1.2.1.43.5.1.1.16.1'),
    ('prtGeneralSerialNumber', '1.3.6.1.2.1.43.5.1.1.17.1'), ('prtMarkerLifeCount', '1.3.6.1.2.1.43.10.2.1.4.1.1'),
    ('prtConsoleDisplayBufferText.1', '1.3.6.1.2.1.43.16.5.1.2.1.1'),
    ('Pantum toner %', '1.3.6.1.4.1.40093.6.3.1.0'), ('Pantum drum %', '1.3.6.1.4.1.40093.8.1.4.0'),
]
REACH_PORTS = (9100, 80, 443, 631, 515)
MAX_SCAN_ADDRESSES = 131072


def now_ts():
    return int(time.time())


def iso(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).isoformat(timespec='seconds') if ts else None


def valid_ip(ip):
    try:
        return isinstance(ip, str) and ipaddress.IPv4Address(ip) is not None and ip.count('.') == 3
    except ValueError:
        return False


def allowed_target(ip):
    """Printers live in private LANs. Refuse loopback, link-local, multicast and public ranges."""
    try:
        a = ipaddress.IPv4Address(ip)
    except ValueError:
        return False
    return a.is_private and not (a.is_loopback or a.is_link_local or a.is_multicast or a.is_unspecified)


def expand_cidr(cidr):
    net = ipaddress.IPv4Network(cidr.strip(), strict=False)
    if net.prefixlen < 16:
        log.info('subnet %s is too large, use /16 or smaller', cidr)
        return []
    if net.prefixlen >= 31:
        return [str(a) for a in net]
    return [str(a) for a in net.hosts()]


async def tcp_open(ip, port, timeout):
    """True = connected, 'refused' = host up but port closed, False = no answer."""
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
    except ConnectionRefusedError:
        return 'refused'
    except (OSError, asyncio.TimeoutError):
        return False
    w.close()
    try:
        await asyncio.wait_for(w.wait_closed(), 0.3)
    except Exception:
        pass
    return True


async def test_reach(ip, timeout=0.45):
    res = await asyncio.gather(*(tcp_open(ip, p, timeout) for p in REACH_PORTS))
    out = {'alive': False, 'port': None}
    for p, r in zip(REACH_PORTS, res):
        if r is True:
            out['alive'] = True
            out['port'] = out['port'] or p
        elif r == 'refused':
            out['alive'] = True
    return out


class Monitor:
    def __init__(self, db):
        self.db = db
        self.cfg = dict(config.DEFAULTS)
        self.demo = config.DEMO
        self.web = WebScraper()
        self.records = []
        self.by_id = {}
        self.printers_json = '[]'
        self.seq = 0
        self.updated = None
        self.polling = True
        self.progress = None
        self.last_error = None
        self.discovered = []
        self.last_discovery = None
        self.last_cycle_sec = None
        self.started = time.time()
        self.hist = {}
        self.hist_ops = []
        self.last_good = {}
        self.lg_dirty = set()
        self.overrides = {}
        self.targets = {}
        self.no_snmp = {}
        self.snmp_ver = {}
        self.probes = {}
        self.probe_sem = asyncio.Semaphore(2)
        self.force_poll = asyncio.Event()
        self.force_discovery = False
        self._flush_lock = asyncio.Lock()
        self._last_prune = 0
        self._task = None

    # ------------------------------------------------------------ lifecycle
    async def load(self):
        stored = await self.db.load_settings()
        for k, v in stored.items():
            if k in self.cfg:
                self.cfg[k] = v
        self.overrides = await self.db.load_overrides()
        if self.demo:
            return
        cut = now_ts() - int(self.cfg['forgetDays']) * 86400
        for r in await self.db.load_printers():
            if r['last_seen'] >= cut:
                self.last_good[r['id']] = r['record']
        since = now_ts() - int(self.cfg['historyDays']) * 86400
        for r in await self.db.load_history(since):
            self.hist.setdefault(r['key'], []).append([r['ts'], r['pct']])
        log.info('loaded: %d known printers, %d history series', len(self.last_good), len(self.hist))

    def start(self):
        self._task = asyncio.create_task(self.run())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        try:
            await self.flush()
        except Exception:
            pass
        await self.web.close()

    async def save_settings(self, changes):
        self.cfg.update(changes)
        await self.db.save_settings(changes)

    # ------------------------------------------------------------ SNMP
    async def snmp_info(self, ip, community=None, timeout=1.2, retries=1):
        community = community or self.cfg['community']
        info = {'online': False, 'supplies': [], 'alerts': []}
        known = self.snmp_ver.get(ip)
        order = [known, V1 if known == V2C else V2C] if known is not None else [V2C, V1]
        for n, ver in enumerate(order):
            try:
                async with SnmpSession(ip, community, ver, timeout, retries if n == 0 else 0) as s:
                    base = await s.get(list(OID.values()) + [CONSOLE + str(i) for i in range(1, 5)])
                    self.snmp_ver[ip] = ver
                    return await self._fill_info(s, base, info)
            except SnmpTimeout:
                continue
            except (SnmpUnreachable, OSError):
                break
        return info

    async def _fill_info(self, s, b, info):
        sys_descr = C.clean(b.get(OID['SysDescr']))
        hr = C.clean(b.get(OID['Model']))
        if not sys_descr and not hr:
            return info
        prt = C.clean(b.get(OID['PrtName']))
        texts = [prt, hr, sys_descr]
        info.update(
            online=True, model=C.select_model(texts), vendor=C.get_vendor(b.get(OID['SysObjectId']), texts),
            sysDescr=sys_descr, alerts=C.error_flags(b.get(OID['ErrState'])), sysName=C.clean(b.get(OID['SysName'])),
            location=C.clean(b.get(OID['SysLocation'])), serial=C.clean(b.get(OID['Serial'])),
            pages=C.to_int(b.get(OID['Pages'])), deviceStatus=C.to_int(b.get(OID['DevStatus'])),
            printerStatus=C.to_int(b.get(OID['PrnStatus'])))
        lines = []
        for i in range(1, 5):
            t = C.clean(b.get(CONSOLE + str(i)))
            if t:
                lines.append(t)
            elif i >= 2:
                break
        info['display'] = lines

        n = max(1, min(64, int(self.cfg['maxSupplies'])))
        descs = await s.get([SUP['desc'] + str(i) for i in range(1, n + 1)])
        idx = []
        for i in range(1, n + 1):
            d = C.clean(descs.get(SUP['desc'] + str(i)))
            if d is None:
                break
            idx.append((i, d))
        sup = []
        if idx:
            fields = ('colorant', 'cls', 'type', 'unit', 'max', 'level')
            det = await s.get([SUP[f] + str(i) for i, _ in idx for f in fields])
            cis = sorted({c for c in (C.to_int(det.get(SUP['colorant'] + str(i))) for i, _ in idx) if c and c > 0})
            cvals = await s.get([COLORANT_VAL + str(c) for c in cis]) if cis else {}
            for i, d in idx:
                ci = C.to_int(det.get(SUP['colorant'] + str(i)))
                item = {'index': i, 'name': d}
                for f in ('type', 'cls', 'unit', 'max', 'level'):
                    item[f] = C.to_int(det.get(SUP[f] + str(i)))
                item['colorant'] = C.clean(cvals.get(COLORANT_VAL + str(ci))) if ci and ci > 0 else None
                sup.append(item)
        if not any(has_level(x) for x in sup):
            p = await s.get([o + sfx for o in PANTUM.values() for sfx in ('', '.0')])
            anyv = lambda k: p.get(PANTUM[k]) if p.get(PANTUM[k]) is not None else p.get(PANTUM[k] + '.0')
            tp = C.to_int(anyv('toner'))
            if tp is not None and 0 <= tp <= 100:
                tm = C.clean(anyv('tonerModel'))
                sup = [{'index': 1, 'name': f'Toner Cartridge {tm}' if tm else 'Toner Cartridge', 'type': 3, 'cls': 3,
                        'unit': 19, 'max': 100, 'level': tp, 'colorant': 'black'}]
                dp = C.to_int(anyv('drum'))
                if dp is not None and 0 <= dp <= 100:
                    dm = C.clean(anyv('drumModel'))
                    sup.append({'index': 2, 'name': f'Drum Unit {dm}' if dm else 'Drum Unit', 'type': 9, 'cls': 3,
                                'unit': 19, 'max': 100, 'level': dp, 'colorant': None})
                if info.get('pages') is None:
                    info['pages'] = C.to_int(anyv('pages'))
        info['supplies'] = sup
        return info

    async def raw_oids(self, ip, community):
        out = []
        for ver in (V2C, V1):
            try:
                async with SnmpSession(ip, community, ver, 1.5, 0) as s:
                    b = await s.get([o for _, o in RAW_LIST])
                    for name, oid in RAW_LIST:
                        v = b.get(oid)
                        if name == 'hrPrinterDetectedErrorState':
                            v = (', '.join(C.error_flags(v)) or 'ok') if v is not None else None
                        else:
                            v = C.clean(v)
                        out.append({'name': name, 'oid': '.' + oid, 'value': v})
                    out.append({'name': 'SNMP version', 'oid': '', 'value': 'v2c' if ver == V2C else 'v1'})
                    d = await s.get([SUP['desc'] + str(i) for i in range(1, 9)])
                    lv = await s.get([SUP[f] + str(i) for i in range(1, 9) for f in ('level', 'max')])
                    for i in range(1, 9):
                        desc = C.clean(d.get(SUP['desc'] + str(i)))
                        if desc is None:
                            break
                        out.append({'name': f'supply {i}', 'oid': '.' + SUP['desc'] + str(i),
                                    'value': f"{desc}  (level {lv.get(SUP['level'] + str(i))} / max {lv.get(SUP['max'] + str(i))})"})
                    return out
            except SnmpTimeout:
                continue
            except (SnmpUnreachable, OSError):
                break
        return out

    # ------------------------------------------------------------ records
    def base_record(self, t):
        ip = t['ip']
        return {
            'id': ip, 'ip': ip, 'host': t.get('host') or ip, 'name': '', 'location': t.get('location'),
            'source': t.get('source', 'scan'), 'queues': [], 'jobs': 0,
            'online': False, 'state': 'offline', 'error': False,
            'model': None, 'sysName': None, 'serial': None, 'pages': None,
            'deviceStatus': None, 'printerStatus': None, 'display': [],
            'supplies': [], 'minPct': None, 'daysLeft': None,
            'stale': False, 'lastSeen': None, 'vendor': None, 'alerts': [], 'hidden': False, 'noCartridge': False,
            'via': None, 'webUrl': f'http://{ip}/', 'reach': None, 'reachPort': None, 'polledAt': now_ts(),
        }

    @staticmethod
    def complete(rec, supplies):
        rank = {'crit': 0, 'warn': 1, 'ok': 2}
        worst, min_pct, min_days = 2, None, None
        for s in supplies:
            if s['waste']:
                continue
            worst = min(worst, rank.get(s['state'], 2))
            if s['pct'] is not None and (min_pct is None or s['pct'] < min_pct):
                min_pct = s['pct']
            if s['daysLeft'] is not None and (min_days is None or s['daysLeft'] < min_days):
                min_days = s['daysLeft']
        rec['supplies'] = list(supplies)
        rec['minPct'], rec['daysLeft'] = min_pct, min_days
        rec['state'] = ('crit', 'warn', 'ok')[worst]
        if not supplies:
            rec['state'] = 'nodata'
        if rec['deviceStatus'] == 5:
            rec['error'], rec['state'] = True, 'crit'
        if 'noToner' in rec['alerts'] or 'supplyMissing' in rec['alerts']:
            rec['noCartridge'], rec['state'] = True, 'crit'

    def make_supply(self, s, k, pct, spark):
        return {
            'index': s['index'], 'name': C.repair_supply_name(s['name'], k), 'rawName': s['name'],
            'type': s.get('type'), 'cls': s.get('cls'), 'unit': s.get('unit'),
            'kind': k['kind'], 'kindName': k['kindName'], 'tint': k['tint'], 'code': C.supply_code(s['name']),
            'color': k['color'], 'colorant': s.get('colorant'), 'max': s.get('max'), 'level': s.get('level'), 'pct': pct,
            'state': C.supply_state(pct, int(self.cfg['warnPct']), int(self.cfg['critPct'])),
            'waste': k['kind'] == 'waste', 'daysLeft': None, 'perDay': None, 'spark': spark,
        }

    def apply_last_good(self, rec):
        rec['state'] = 'offline'
        lg = self.last_good.get(rec['id'])
        if not lg:
            return rec
        for k in ('model', 'sysName', 'serial', 'pages', 'via', 'vendor'):
            if rec.get(k) in (None, ''):
                rec[k] = lg.get(k)
        if not rec['location'] and lg.get('location'):
            rec['location'] = lg['location']
        if (not rec['name'] or rec['name'] == rec['ip']) and lg.get('name'):
            rec['name'] = lg['name']
        hide = self.cfg['hideWaste']
        rec['supplies'] = [dict(s, daysLeft=None, perDay=None) for s in (lg.get('supplies') or [])
                           if s and not (hide and s.get('kind') == 'waste' and s.get('pct') is None)]
        rec['minPct'] = lg.get('minPct')
        rec['daysLeft'] = None
        rec['lastSeen'] = lg.get('lastSeen')
        rec['stale'] = True
        return rec

    async def new_record(self, t, side=True, community=None):
        rec = self.base_record(t)
        ip = t['ip']
        info = await self.snmp_info(ip, community)
        reach = None
        if not info['online']:
            # silent over SNMP: is the host up? Canon and others in deep sleep wake up on TCP
            reach = await test_reach(ip)
            ns = self.no_snmp.get(ip)
            if reach['port'] and (ns is None or time.time() - ns >= 6 * 3600):
                info = await self.snmp_info(ip, community, 2.5, 1)
                if info['online']:
                    self.no_snmp.pop(ip, None)
                else:
                    self.no_snmp[ip] = time.time()
        rec['name'] = info.get('sysName') or info.get('model') or ip

        rec['via'] = 'snmp'
        if not any(has_level(x) for x in info['supplies']) and not (reach and not reach['alive']):
            web = None
            try:
                web = await self.web.get_toner(t.get('host') or ip)
            except Exception as e:
                log.info('web read %s failed: %s', ip, e)
            if web:
                rec['via'] = 'web'
                if not info['online']:
                    info['online'] = True
                    info['model'] = web['model']
                    if rec['name'] == ip and web['model']:
                        rec['name'] = web['model']
                info['supplies'] = [{'index': 1, 'name': 'Toner Cartridge', 'type': 3, 'cls': 3, 'unit': 19,
                                     'max': 100, 'level': web['toner'], 'colorant': 'black'}]
                if web.get('missing'):
                    info['alerts'] = list(info.get('alerts') or []) + ['supplyMissing']
                if not info.get('vendor'):
                    info['vendor'] = C.vendor_from_text(web['model'])

        if not info['online']:
            if reach:
                if reach['port']:
                    rec['reach'], rec['reachPort'] = 'port', reach['port']
                else:
                    rec['reach'] = 'up' if reach['alive'] else 'down'
            if side:
                return self.apply_last_good(rec)
            rec['state'] = 'offline'
            return rec

        rec['online'] = True
        for k in ('model', 'sysName', 'serial', 'pages', 'deviceStatus', 'printerStatus', 'vendor'):
            rec[k] = info.get(k)
        rec['alerts'] = [a for a in info.get('alerts') or [] if a]
        if not rec['vendor']:
            rec['vendor'] = C.vendor_from_text(f"{rec['model'] or ''} {rec['name']}")
        rec['display'] = info.get('display') or []
        loc = info.get('location')
        if not rec['location'] and loc and loc.lower() not in ('unknown', 'none', 'n/a', '-', 'location'):
            rec['location'] = loc

        now = now_ts()
        lst = []
        for s in info['supplies']:
            k = C.supply_kind(s['name'], s.get('colorant'), s.get('type'), s.get('cls'))
            pct = None
            if has_level(s):
                pct = int(round(min(100.0, s['level'] * 100.0 / s['max'])))
            # waste container without a level ("some space left") tells nothing useful
            if self.cfg['hideWaste'] and k['kind'] == 'waste' and pct is None:
                continue
            key = f"{ip}|{s['index']}|{s['name']}"
            if pct is not None and side:
                self.add_hist(key, now, pct)
            lst.append(self.make_supply(s, k, pct, self.spark(self.hist.get(key), now)))
        self.complete(rec, lst)
        rec['lastSeen'] = now
        if side:
            self.last_good[rec['id']] = dict(rec)
            self.lg_dirty.add(rec['id'])
        return rec

    # ------------------------------------------------------------ history
    def add_hist(self, key, t, pct):
        lst = self.hist.setdefault(key, [])
        if lst:
            lt, lp = lst[-1]
            if t - lt < 3600 and lp == pct:
                return
            if t - lt < 600:
                self.hist_ops.append(('upd', key, lt, t, pct))
                lst[-1] = [t, pct]
                return
        lst.append([t, pct])
        self.hist_ops.append(('ins', key, t, pct))

    @staticmethod
    def spark(lst, now):
        if not lst or len(lst) < 2:
            return []
        cut = now - 30 * 86400
        pts = [p for p in lst if p[0] >= cut]
        if not pts:
            return []
        step = max(1, math.ceil(len(pts) / 60.0))
        out = [[p[0], p[1]] for p in pts[::step]]
        if (len(pts) - 1) % step:
            out.append([pts[-1][0], pts[-1][1]])
        return out

    async def flush(self):
        if self.demo:
            self.hist_ops.clear()
            self.lg_dirty.clear()
            return
        async with self._flush_lock:
            ops, self.hist_ops = self.hist_ops, []
            ids, self.lg_dirty = self.lg_dirty, set()
            await self.db.apply_history(ops)
            await self.db.save_printers([self.last_good[i] for i in ids if i in self.last_good])
            if time.time() - self._last_prune > 3600:
                self._last_prune = time.time()
                cut = now_ts() - int(self.cfg['historyDays']) * 86400
                for k in list(self.hist):
                    self.hist[k] = [p for p in self.hist[k] if p[0] >= cut]
                    if not self.hist[k]:
                        del self.hist[k]
                await self.db.prune_history(cut)
                fcut = now_ts() - int(self.cfg['forgetDays']) * 86400
                gone = [k for k, v in self.last_good.items() if (v.get('lastSeen') or 0) < fcut]
                for k in gone:
                    del self.last_good[k]
                await self.db.delete_printers(gone)

    # ------------------------------------------------------------ discovery
    async def _disc_one(self, ip, community):
        async def snmp(ver):
            try:
                async with SnmpSession(ip, community, ver, 0.8, 0) as s:
                    r = await s.get(DISCOVERY_OIDS)
                    return any(v is not None for v in r.values())
            except Exception:
                return False
        a, b = await asyncio.gather(snmp(V2C), snmp(V1))
        if a or b:
            return True
        # no SNMP answer: an open JetDirect port 9100 almost always means a printer
        return await tcp_open(ip, 9100, 0.35) is True

    async def discovery(self):
        ips = []
        for s in self.cfg['subnets']:
            try:
                ips.extend(expand_cidr(s))
            except ValueError:
                log.info('bad subnet %s', s)
            if len(ips) > MAX_SCAN_ADDRESSES:
                log.info('too many addresses to scan, first %d taken', MAX_SCAN_ADDRESSES)
                ips = ips[:MAX_SCAN_ADDRESSES]
                break
        ips = list(dict.fromkeys(ips))
        total, done, found = len(ips), 0, []
        self.progress = {'phase': 'scan', 'done': 0, 'total': total, 'found': 0, 'current': ''}
        community = self.cfg['community']
        it = iter(ips)

        async def worker():
            nonlocal done
            for ip in it:
                if await self._disc_one(ip, community):
                    found.append(ip)
                done += 1
                if done % 16 == 0 or done == total:
                    self.progress = {'phase': 'scan', 'done': done, 'total': total, 'found': len(found), 'current': ''}

        await asyncio.gather(*(worker() for _ in range(max(1, min(192, total)))))
        return sorted(found, key=lambda x: ipaddress.IPv4Address(x))

    def get_targets(self):
        ex = set(self.cfg['excludeIps'])
        extra = list(self.cfg['extraIps'])
        targets = {}
        for ip in self.discovered + extra:
            if not ip or ip in ex or ip in targets:
                continue
            targets[ip] = {'ip': ip, 'host': ip, 'location': None, 'source': 'manual' if ip in extra else 'scan'}
        for lg in list(self.last_good.values()):
            ip = str(lg.get('ip') or '')
            if not ip or ip in targets or ip in ex:
                continue
            targets[ip] = {'ip': ip, 'host': lg.get('host') or ip, 'location': lg.get('location'),
                           'source': lg.get('source') or 'scan'}
        return targets

    # ------------------------------------------------------------ publish
    def apply_overrides(self, r):
        if 'origName' not in r:
            r['origName'], r['origLocation'] = r['name'], r['location']
        o = self.overrides.get(r['id'])
        r['name'], r['location'], r['hidden'], r['renamed'] = r['origName'], r['origLocation'], False, False
        if o:
            if o.get('name'):
                r['name'], r['renamed'] = o['name'], True
            if o.get('location'):
                r['location'] = o['location']
            if o.get('hidden'):
                r['hidden'] = True

    def publish(self, records):
        records = [r for r in records if r]
        for r in records:
            self.apply_overrides(r)
        self.records = records
        self.by_id = {r['id']: r for r in records}
        self.printers_json = json.dumps(records, ensure_ascii=False, separators=(',', ':'))
        self.updated = now_ts()
        self.seq += 1

    def republish(self):
        self.publish(self.records)

    # ------------------------------------------------------------ main loop
    async def cycle(self):
        if self.demo:
            self.publish(demo_records(self))
            return
        cfg = self.cfg
        if cfg['subnets'] and (self.force_discovery or self.last_discovery is None
                               or time.time() - self.last_discovery >= int(cfg['discoveryMinutes']) * 60):
            self.force_discovery = False
            t0 = time.time()
            self.discovered = await self.discovery()
            self.last_discovery = time.time()
            log.info('discovery: %d printers in %s (%.1f s)', len(self.discovered), ', '.join(cfg['subnets']), time.time() - t0)
        targets = list(self.get_targets().values())
        first = self.updated is None
        records = [None] * len(targets)
        total, done = len(targets), 0
        self.progress = {'phase': 'poll', 'done': 0, 'total': total, 'found': 0, 'current': ''}
        sem = asyncio.Semaphore(16)

        async def one(i, t):
            nonlocal done
            async with sem:
                self.progress = {'phase': 'poll', 'done': done, 'total': total, 'found': 0, 'current': t['ip']}
                try:
                    records[i] = await self.new_record(t)
                except Exception as e:
                    log.info('poll %s failed: %s', t['ip'], e)
            done += 1
            if first:
                self.publish(records)   # on the very first run show printers as soon as they are polled

        await asyncio.gather(*(one(i, t) for i, t in enumerate(targets)))
        self.targets = {t['ip']: t for t in targets}
        self.publish(records)
        await self.flush()

    async def run(self):
        await self.web.start()
        log.info('poller started, demo=%s, subnets=%s', self.demo, ','.join(self.cfg['subnets']) or '-')
        while True:
            self.polling = True
            self.last_error = None
            t0 = time.time()
            try:
                await self.cycle()
                self.last_cycle_sec = round(time.time() - t0, 1)
                log.info('polled %d printers in %.1f s', len(self.records), time.time() - t0)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.last_error = str(e)
                log.exception('cycle failed: %s', e)
            finally:
                self.polling = False
                self.progress = None
            self.force_poll.clear()
            wait = max(1.0, t0 + max(30, int(self.cfg['pollSeconds'])) - time.time())
            try:
                await asyncio.wait_for(self.force_poll.wait(), wait)
            except asyncio.TimeoutError:
                pass

    # ------------------------------------------------------------ on demand
    async def poll_one(self, pid):
        t = self.targets.get(pid)
        if not t:
            if not valid_ip(pid):
                return
            t = {'ip': pid, 'host': pid, 'location': None, 'source': 'manual'}
            self.targets[pid] = t
        try:
            if self.demo:
                self.republish()
                return
            rec = await self.new_record(t)
            recs = [r for r in self.records if r['id'] != pid] + [rec]
            if any(r['id'] == pid for r in self.records):
                recs = [rec if r['id'] == pid else r for r in self.records]
            self.publish(recs)
            await self.flush()
            log.info('refreshed %s', pid)
        except Exception as e:
            log.info('refresh %s failed: %s', pid, e)

    async def remove(self, pid):
        self.last_good.pop(pid, None)
        self.targets.pop(pid, None)
        if not self.demo:
            await self.db.delete_printers([pid])
        if any(r['id'] == pid for r in self.records):
            self.publish([r for r in self.records if r['id'] != pid])

    def start_probe(self, ip, community):
        pending = sum(1 for p in self.probes.values() if not p.get('done'))
        if pending >= 4:
            return None
        # forget old results
        cut = time.time() - 900
        for k in [k for k, v in self.probes.items() if v.get('_t', 0) < cut]:
            del self.probes[k]
        jid = secrets.token_hex(6)
        self.probes[jid] = {'id': jid, 'ip': ip, 'done': False, '_t': time.time()}
        asyncio.create_task(self._probe(jid, ip, community))
        return jid

    async def _probe(self, jid, ip, community):
        async with self.probe_sem:
            t0 = time.time()
            res = {'id': jid, 'ip': ip, 'done': True, 'ok': False, 'record': None, 'raw': [], 'ms': 0,
                   'monitored': False, 'error': None, '_t': time.time()}
            try:
                com = community or self.cfg['community']
                res['record'] = await self.new_record({'ip': ip, 'host': ip, 'location': None, 'source': 'probe'},
                                                      side=False, community=com)
                res['raw'] = await self.raw_oids(ip, com)
                res['ok'] = bool(res['record']['online'])
                res['monitored'] = ip in self.by_id
            except Exception as e:
                res['error'] = str(e)
            res['ms'] = int((time.time() - t0) * 1000)
            self.probes[jid] = res
            log.info('probe %s: online=%s in %d ms', ip, res['ok'], res['ms'])


def has_level(x):
    return bool(x.get('max')) and x['max'] > 0 and x.get('level') is not None and x['level'] >= 0


# ---------------------------------------------------------------- demo data
def _demo_supply(m, i, name, pct, per_day, typ, now, colorant=None):
    spark, d = [], 30.0
    while d >= 0:
        v = pct + per_day * d + math.sin(d * 1.7 + i) * min(2.0, per_day * 1.5)
        while v > 100:
            v -= 92
        spark.append([int(now - d * 86400), int(round(max(0, v)))])
        d -= 0.5
    k = C.supply_kind(name, colorant, typ, 3)
    s = {'index': i, 'name': name, 'type': typ, 'cls': 4 if k['kind'] == 'waste' else 3, 'unit': 19,
         'max': 100, 'level': pct, 'colorant': None}
    return m.make_supply(s, k, pct, spark)


DEMO_DEFS = [
    ('Бухгалтерия', 'HP Color LaserJet Pro M479fdw', '192.168.3.51', 'Корпус 1, каб. 104', 2, 48210, {}, [
        ('Black Cartridge HP 415A W2030A', 41, 1.2, 3), ('Cyan Cartridge HP 415A W2031A', 6, 0.8, 3),
        ('Magenta Cartridge HP 415A W2033A', 58, 0.7, 3), ('Yellow Cartridge HP 415A W2032A', 33, 0.9, 3)]),
    ('Учительская', 'Kyocera ECOSYS M2540dn', '192.168.1.52', 'Корпус 1, каб. 210', 0, 112904, {}, [
        ('TK-1170 Black Toner', 18, 1.6, 3), ('Waste Toner Box', 70, 0, 4)]),
    ('Библиотека', 'HP LaserJet Pro M404dn', '192.168.91.53', 'Корпус 2, 1 этаж', 1, 67330, {'lcd': True}, [
        ('Black Cartridge HP 59A CF259A', 8, 1.1, 3)]),
    ('Лаборатория 305', 'Pantum M6700DW', '192.168.91.55', 'Корпус 2, каб. 305', 0, 9437, {'web': True}, [
        ('Toner Cartridge TL-420X', 39, 0.9, 3)]),
    ('Xerox VersaLink B7035', 'Xerox VersaLink B7035', '192.168.3.57', 'Преподавательская', 0, 318120, {}, [
        ('Black Toner Cartridge 106R03396', 74, 0.8, 3), ('Drum Cartridge 113R00779', 12, 0.3, 9),
        ('Waste Toner Container 115R00129', 55, 0, 4), ('Fuser 115R00115', 81, 0.1, 15)]),
    ('Компьютерный класс 118', 'Kyocera ECOSYS P3145dn', '192.168.2.58', 'Корпус 1, каб. 118', 4, 201455, {}, [
        ('TK-3160 Black Toner', 23, 2.4, 3), ('Maintenance Kit MK-3150', 81, 0.1, 1)]),
    ('Методический кабинет', 'Canon i-SENSYS MF655Cdw', '192.168.77.59', 'Корпус 2, каб. 212', 0, 15870, {}, [
        ('Black Toner 067H', 64, 0.6, 3), ('Cyan Toner 067H', 88, 0.3, 3), ('Magenta Toner 067H', 19, 0.5, 3),
        ('Yellow Toner 067H', 71, 0.3, 3), ('Transfer Belt', 72, 0.1, 20), ('Fuser Unit', 58, 0.15, 15)]),
    ('211', 'Canon MF750C Series', '192.168.2.211', 'Корпус 1, каб. 211', 0, 7340, {'alerts': ['supplyMissing']}, [
        ('Black Toner', 0, 0, 3), ('Cyan Toner', 62, 0.4, 3), ('Magenta Toner', 57, 0.4, 3), ('Yellow Toner', 66, 0.4, 3)]),
    ('Приёмная', 'Pantum BM5100FDN', '192.168.0.188', 'Корпус 1, каб. 100', 0, 23456, {'web': True}, [
        ('Toner Cartridge TL-5120', 55, 0.7, 3), ('Drum Unit DL-5120', 64, 0.2, 9)]),
    ('Аудитория 213', 'Canon i-SENSYS MF445dw', '192.168.99.60', 'Корпус 2, каб. 213', 0, 41230, {'off': True}, [
        ('Black Toner Cartridge 057H', 14, 1.3, 3), ('Drum Unit 070', 61, 0.2, 9)]),
    ('NPI600F17', 'HP Color LaserJet CP5520 Series', '192.168.0.215', 'Корпус 1, каб. 115', 0, 20122, {}, [
        ('?????? ???????? 650A HP CE270A', 50, 0.4, 3, 'black'), ('??????? ???????? 650A HP CE271A', 18, 0.6, 3, 'cyan'),
        ('????????? ???????? 650A HP CE273A', 0, 0, 3, 'magenta'), ('?????? ???????? 650A HP CE272A', 2, 0.5, 3, 'yellow'),
        ('????? ????????????? HP CE979A', 79, 0.1, 20), ('????? ????????????? HP 110V-CE977A, 220V-CE978A', 80, 0.1, 15),
        ('?????? ????? ?????? HP CE980A', -1, 0, 4)]),
    ('212', 'Canon MF750C Series', '192.168.2.212', 'Корпус 1, каб. 212', 0, 0, {'down': 'port'}, []),
    ('Кабинет 007', '', '192.168.4.17', '', 0, 0, {'down': 'down'}, []),
]


def demo_records(m):
    now = now_ts()
    out = []
    for name, model, ip, loc, jobs, pages, opt, sups in DEMO_DEFS:
        rec = m.base_record({'ip': ip, 'host': ip, 'location': loc, 'source': 'scan'})
        tail = ip.split('.')[3]
        rec.update(name=name, online=True, model=model, pages=pages, via='web' if opt.get('web') else 'snmp',
                   serial=f'DEMO{tail}X7Q2', sysName=f'NPI{tail}', deviceStatus=2, printerStatus=3, jobs=jobs)
        lst, i = [], 1
        for s in sups:
            s = list(s)
            if s[1] < 0:
                if m.cfg['hideWaste']:
                    continue
                s = [s[0], 50, 0, s[3]]
            lst.append(_demo_supply(m, i, s[0], s[1], s[2], s[3], now, s[4] if len(s) > 4 else None))
            i += 1
        if opt.get('lcd'):
            rec.update(display=['Toner Low', 'Order Cartridge'], deviceStatus=3, alerts=['lowToner'])
        if opt.get('alerts'):
            rec['alerts'] = list(opt['alerts'])
        rec['vendor'] = C.vendor_from_text(model)
        m.complete(rec, lst)
        rec['lastSeen'] = now
        if opt.get('down'):
            rec.update(online=False, state='offline', supplies=[], minPct=None, daysLeft=None, lastSeen=None,
                       model=None, pages=None, serial=None, sysName=None, deviceStatus=None, printerStatus=None,
                       reach=opt['down'])
            if opt['down'] == 'port':
                rec.update(reachPort=80, vendor='Canon')
            else:
                rec['vendor'] = None
        if opt.get('off'):
            rec.update(online=False, state='offline', stale=True, lastSeen=now - 3 * 3600 - 1260,
                       deviceStatus=None, printerStatus=None)
        out.append(rec)
    return out

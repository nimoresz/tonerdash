"""Fallback: read the toner level from the printer's own web page
(Pantum and others that show supplies in the web UI but not over SNMP)."""
import asyncio
import html
import re
from urllib.parse import urljoin, urlsplit

import aiohttp

MAX_BYTES = 1024 * 1024
MAX_PAGES = 12

RX_LINKS = [
    re.compile(r'(?i)<(?:frame|iframe|script)[^>]+src\s*=\s*["\']?([^"\'\s>]+)'),
    re.compile(r'(?i)location(?:\.href)?\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'(?i)["\']([\w\-\./]+\.(?:xml|json|cgi|htm|html|js|asp|php)(?:\?[^"\']*)?)["\']'),
]
RX_SKIP = re.compile(r'(?i)^(javascript|mailto|data):|jquery|\.min\.js')
RX_MISSING = re.compile(r'(?i)(cartridge|картридж)[^.%]{0,60}?(missing|not installed|none|отсутств|не установлен)')
RX_PLAIN = re.compile(r'(?i)(?:toner|тонер)[^%\d]{0,80}?(\d{1,3})\s*%')
RX_VAR = re.compile(r'(?i)(?:toner\w*(?:remain|level|percent|rest|life|value)\w*|(?:remain|level|percent)\w*toner\w*)\s*[=:]\s*["\']?(\d{1,3})\b')
RX_TITLE = re.compile(r'(?is)<title>\s*([^<]{2,80}?)\s*</title>')
RX_CHARSET = re.compile(rb'(?i)charset\s*=\s*["\']?([\w\-]+)')


def plain_text(src):
    t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', src)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', html.unescape(t))


def find_toner(pages):
    if not pages:
        return None
    title = None
    for _, text in pages:
        m = RX_TITLE.search(text)
        if m:
            title = m.group(1)
            break
    for url, text in pages:
        plain = plain_text(text)
        missing = bool(RX_MISSING.search(plain))
        m = RX_PLAIN.search(plain)
        if m and int(m.group(1)) <= 100:
            return {'toner': int(m.group(1)), 'model': title, 'url': url, 'missing': missing}
        if missing:
            return {'toner': 0, 'model': title, 'url': url, 'missing': True}
    for url, text in pages:
        m = RX_VAR.search(text)
        if m and int(m.group(1)) <= 100:
            return {'toner': int(m.group(1)), 'model': title, 'url': url, 'missing': False}
    return None


class WebScraper:
    def __init__(self):
        self.session = None
        self.hint = {}

    async def start(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5, sock_connect=2.5, sock_read=3),
            headers={'User-Agent': 'Mozilla/5.0 (Toner-Dashboard)'},
            connector=aiohttp.TCPConnector(limit=32, force_close=True),
            trust_env=False,
            cookie_jar=aiohttp.DummyCookieJar(),
        )

    async def close(self):
        if self.session:
            await self.session.close()

    async def fetch(self, url):
        """-> (text or None, redirect url or None)"""
        try:
            async with self.session.get(url, allow_redirects=False) as r:
                if r.status in (301, 302, 303, 307, 308):
                    loc = r.headers.get('Location')
                    return None, urljoin(url, loc) if loc else None
                if r.status >= 400:
                    return None, None
                buf = bytearray()
                async for chunk in r.content.iter_chunked(65536):
                    buf += chunk
                    if len(buf) >= MAX_BYTES:
                        break
                data = bytes(buf[:MAX_BYTES])
                cs = r.charset
                if not cs:
                    m = RX_CHARSET.search(data[:2048])
                    cs = m.group(1).decode('ascii', 'ignore') if m else None
                try:
                    return data.decode(cs or 'utf-8', 'replace'), None
                except LookupError:
                    return data.decode('utf-8', 'replace'), None
        except (aiohttp.ClientError, asyncio.TimeoutError, UnicodeError, ValueError):
            return None, None

    async def pages(self, host):
        prefix = f'http://{host}/'
        pages, seen, queue = [], set(), [prefix]
        fetched = 0
        while queue and len(pages) < MAX_PAGES and fetched < MAX_PAGES * 2:
            u = queue.pop(0)
            if u in seen:
                continue
            seen.add(u)
            fetched += 1
            text, redirect = await self.fetch(u)
            if text is None:
                if redirect and redirect.startswith(prefix) and redirect not in seen:
                    queue.insert(0, redirect)
                    continue
                if not pages:
                    break               # no web interface at all
                continue
            pages.append((u, text))
            for rx in RX_LINKS:
                for m in rx.finditer(text):
                    src = m.group(1)
                    if RX_SKIP.search(src):
                        continue
                    try:
                        absu = urljoin(u, src)
                    except ValueError:
                        continue
                    if absu.startswith(prefix) and urlsplit(absu).scheme == 'http' and absu not in seen:
                        queue.append(absu)
        return pages

    async def get_toner(self, host):
        u = self.hint.get(host)
        if u:
            text, _ = await self.fetch(u)
            if text:
                w = find_toner([(u, text)])
                if w:
                    return w
        w = find_toner(await self.pages(host))
        if w:
            self.hint[host] = w['url']
        return w

"""Vendor, supply kind and colour detection (ported 1:1 from the PowerShell version)."""
import re

RX_WASTE = re.compile(r'waste|collect|отраб')
RX_DRUM = re.compile(r'drum|opc|imaging|photoconductor|барабан|фотобар')
RX_FUSER = re.compile(r'fuser|fixing|фьюзер|закреп')
RX_C = re.compile(r'cyan|голуб|циан')
RX_M = re.compile(r'magenta|пурпур|маджент')
RX_Y = re.compile(r'yellow|желт|жёлт')
RX_K = re.compile(r'black|\bbk\b|\bk\b|черн|чёрн')
RX_BELT = re.compile(r'belt|\bitb\b|transfer unit|transfer kit|ремень|узел перен')
RX_ROLLER = re.compile(r'roller|ролик')
RX_KIT = re.compile(r'maintenance|\bkit\b|ремкомплект|сервисн')
RX_DEV = re.compile(r'developer|девелопер|проявит')
RX_STAPLE = re.compile(r'staple|скоб')
RX_INK = re.compile(r'\bink\b|чернил')
RX_TONER = re.compile(r'toner|cartridge|тонер|картридж')

KIND_NAME = {
    'toner': 'Тонер', 'ink': 'Чернила', 'drum': 'Фотобарабан', 'dev': 'Девелопер',
    'waste': 'Контейнер отработки', 'fuser': 'Фьюзер (печка)', 'belt': 'Ремень переноса',
    'roller': 'Ролик переноса', 'kit': 'Ремкомплект', 'staple': 'Скобы', 'other': 'Расходник',
}
COLOR_NAME = {'k': 'чёрный', 'c': 'голубой', 'm': 'пурпурный', 'y': 'жёлтый'}
BASE_NAME = {
    'toner': 'Картридж', 'ink': 'Картридж', 'drum': 'Фотобарабан', 'dev': 'Девелопер',
    'waste': 'Контейнер отработки', 'fuser': 'Фьюзер', 'belt': 'Ремень переноса',
    'roller': 'Ролик переноса', 'kit': 'Ремкомплект', 'staple': 'Скобы', 'other': 'Расходник',
}

VENDOR_ENT = {11: 'HP', 1602: 'Canon', 253: 'Xerox', 40093: 'Pantum', 1347: 'Kyocera', 2435: 'Brother',
              367: 'Ricoh', 1248: 'Epson', 641: 'Lexmark', 18334: 'Konica Minolta', 236: 'Samsung',
              2001: 'OKI', 2385: 'Sharp', 1129: 'Toshiba', 674: 'Dell'}
VENDOR_RX = [(k, re.compile(v)) for k, v in [
    ('Pantum', r'pantum'), ('Canon', r'canon|i-sensys|imagerunner|imageclass|\bmf\d{3}|\blbp\d'),
    ('Xerox', r'xerox|versalink|altalink|workcentre|phaser|primelink'),
    ('HP', r'\bhp\b|hewlett|laserjet|officejet|deskjet|pagewide'), ('Kyocera', r'kyocera|ecosys|taskalfa'),
    ('Brother', r'brother'), ('Ricoh', r'ricoh|aficio'), ('Epson', r'epson'), ('Lexmark', r'lexmark'),
    ('Konica Minolta', r'konica|minolta|bizhub'), ('Samsung', r'samsung'), ('OKI', r'\boki\b'),
    ('Sharp', r'sharp'), ('Toshiba', r'toshiba|e-studio'), ('Katusha', r'katusha'),
]]

ERR_BITS = [
    (0, 0x80, 'lowPaper'), (0, 0x40, 'noPaper'), (0, 0x20, 'lowToner'), (0, 0x10, 'noToner'), (0, 0x08, 'doorOpen'),
    (0, 0x04, 'jammed'), (0, 0x02, 'offline'), (0, 0x01, 'service'), (1, 0x80, 'trayMissing'), (1, 0x40, 'outTrayMissing'),
    (1, 0x20, 'supplyMissing'), (1, 0x10, 'outNearFull'), (1, 0x08, 'outFull'), (1, 0x04, 'trayEmpty'), (1, 0x02, 'maintenance'),
]

RX_CODE = re.compile(r'\b([A-Z]{1,5}-?\d{2,5}[A-Z]{0,3}|\d{3}R\d{5})\b')
_CTRL = re.compile(r'[\x00-\x1f\x7f]')
_SPACES = re.compile(r'\s{2,}')


def decode_text(b):
    b = b.rstrip(b'\x00')
    if not b:
        return ''
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        pass
    try:
        return b.decode('cp1251')
    except UnicodeDecodeError:
        return b.decode('latin-1')


def clean(v):
    if v is None:
        return None
    if isinstance(v, (bytes, bytearray)):
        v = decode_text(bytes(v))
    s = _SPACES.sub(' ', _CTRL.sub(' ', str(v))).strip()
    return s or None


def to_int(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, (bytes, bytearray)):
        v = bytes(v).decode('latin-1', 'replace')
    try:
        return int(str(v).strip())
    except ValueError:
        return None


def vendor_from_text(t):
    t = str(t or '').lower()
    for k, rx in VENDOR_RX:
        if rx.search(t):
            return k
    return None


def get_vendor(obj_id, texts):
    for x in texts:
        v = vendor_from_text(x)
        if v:
            return v
    m = re.match(r'^\.?1\.3\.6\.1\.4\.1\.(\d+)', str(obj_id or ''))
    if m:
        return VENDOR_ENT.get(int(m.group(1)))
    return None


def error_flags(v):
    if v is None:
        return []
    if isinstance(v, int):
        data = v.to_bytes(max(1, (v.bit_length() + 7) // 8), 'big') if v >= 0 else b''
    elif isinstance(v, (bytes, bytearray)):
        data = bytes(v)
        m = re.fullmatch(rb'(0x)?([0-9A-Fa-f]{2})\s?([0-9A-Fa-f]{2})?', data.strip())
        if m and len(data.strip()) >= 2 and not any(c < 0x20 for c in data):
            data = bytes([int(m.group(2), 16)] + ([int(m.group(3), 16)] if m.group(3) else []))
    else:
        return []
    return [name for i, mask, name in ERR_BITS if len(data) > i and data[i] & mask]


def supply_kind(desc, colorant, typ, cls):
    t = f'{colorant or ""} {desc or ""}'.lower()
    col = None
    for src in (str(colorant or '').lower(), t):
        if col or not src.strip():
            continue
        if RX_C.search(src):
            col = 'c'
        elif RX_M.search(src):
            col = 'm'
        elif RX_Y.search(src):
            col = 'y'
        elif RX_K.search(src):
            col = 'k'
    if typ in (4, 8) or cls == 4 or RX_WASTE.search(t):
        kind = 'waste'
    elif typ == 9 or RX_DRUM.search(t):
        kind = 'drum'
    elif typ == 10 or RX_DEV.search(t):
        kind = 'dev'
    elif typ == 15 or RX_FUSER.search(t):
        kind = 'fuser'
    elif typ == 20 or RX_BELT.search(t):
        kind = 'belt'
    elif RX_ROLLER.search(t):
        kind = 'roller'
    elif typ == 32 or RX_STAPLE.search(t):
        kind = 'staple'
    elif typ == 18 or RX_KIT.search(t):
        kind = 'kit'
    elif typ in (5, 6) or RX_INK.search(t):
        kind = 'ink'
    elif typ in (3, 21) or col or RX_TONER.search(t):
        kind = 'toner'
    else:
        kind = 'other'
    if kind in ('toner', 'ink') and not col:
        col = 'k'
    colored = kind in ('toner', 'ink', 'drum', 'dev')
    fill, name = kind, KIND_NAME[kind]
    if colored and col:
        fill, name = col, f'{name}, {COLOR_NAME[col]}'
    else:
        col = None
    return {'kind': kind, 'color': fill, 'tint': col, 'kindName': name}


def supply_code(name):
    m = RX_CODE.search(str(name or '').upper())
    return m.group(1) if m else None


def repair_supply_name(name, k):
    """HP sends '??????' instead of its localized supply names; build a readable one."""
    if not re.search(r'\?{2,}', str(name or '')):
        return name
    rest = ' '.join(w for w in str(name).split() if '?' not in w)
    base = BASE_NAME.get(k['kind'], BASE_NAME['other'])
    if k.get('tint') and k['tint'] in COLOR_NAME:
        base += ' ' + COLOR_NAME[k['tint']]
    return f'{base} {rest}'.strip()


def format_model(m):
    m = re.split(r'[;,]', m)[0].strip()
    m = re.sub(r'\s*/P$', '', m)
    return m[:60].strip()


def select_model(cands):
    lst = [c for c in cands if c]
    for c in lst:
        if vendor_from_text(c):
            return format_model(c)
    return format_model(lst[0]) if lst else None


def supply_state(pct, warn, crit):
    if pct is None:
        return 'unknown'
    if pct <= crit:
        return 'crit'
    if pct <= warn:
        return 'warn'
    return 'ok'

"""Minimal asyncio SNMP v1 / v2c GET client.

No external dependencies: BER encoding of GetRequest and decoding of the
Response PDU is all we need to read Printer-MIB. Many OIDs travel in one
packet, which makes a full printer poll 3-4 UDP round trips instead of ~80.
"""
import asyncio
import secrets

V1, V2C = 0, 1


class SnmpTimeout(Exception):
    pass


class SnmpUnreachable(Exception):
    """ICMP port unreachable: the host is up but nothing listens on UDP 161."""


# ---------------------------------------------------------------- BER encode
def _len(n):
    if n < 0x80:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, 'big')
    return bytes([0x80 | len(b)]) + b


def _tlv(tag, payload):
    return bytes([tag]) + _len(len(payload)) + payload


def _int(v):
    return _tlv(0x02, v.to_bytes(max(1, (v.bit_length() + 8) // 8), 'big', signed=True))


def _oid(oid):
    parts = [int(x) for x in oid.strip('.').split('.')]
    body = bytearray([parts[0] * 40 + parts[1]])
    for p in parts[2:]:
        chunk = [p & 0x7F]
        p >>= 7
        while p:
            chunk.append(0x80 | (p & 0x7F))
            p >>= 7
        body.extend(reversed(chunk))
    return _tlv(0x06, bytes(body))


def build_get(version, community, reqid, oids):
    vbs = b''.join(_tlv(0x30, _oid(o) + b'\x05\x00') for o in oids)
    pdu = _tlv(0xA0, _int(reqid) + _int(0) + _int(0) + _tlv(0x30, vbs))
    return _tlv(0x30, _int(version) + _tlv(0x04, community.encode('utf-8')) + pdu)


# ---------------------------------------------------------------- BER decode
def _read(buf, pos):
    tag = buf[pos]
    n = buf[pos + 1]
    pos += 2
    if n & 0x80:
        k = n & 0x7F
        n = int.from_bytes(buf[pos:pos + k], 'big')
        pos += k
    end = pos + n
    if end > len(buf):
        raise ValueError('truncated packet')
    return tag, pos, end


def decode_oid(data):
    if not data:
        return ''
    first = data[0]
    parts = [min(first // 40, 2), first - 40 * min(first // 40, 2)]
    v = 0
    for b in data[1:]:
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            parts.append(v)
            v = 0
    return '.'.join(map(str, parts))


def _value(tag, data):
    if tag == 0x02:
        return int.from_bytes(data, 'big', signed=True) if data else 0
    if tag in (0x41, 0x42, 0x43, 0x46):          # Counter32, Gauge32, TimeTicks, Counter64
        return int.from_bytes(data, 'big', signed=False)
    if tag == 0x04:
        return bytes(data)
    if tag == 0x06:
        return decode_oid(data)
    if tag == 0x40:
        return '.'.join(str(b) for b in data)
    if tag in (0x05, 0x80, 0x81, 0x82):          # NULL, noSuchObject, noSuchInstance, endOfMibView
        return None
    return bytes(data)


def parse_response(buf):
    _, p, _ = _read(buf, 0)
    _, s, e = _read(buf, p)                      # version
    p = e
    _, s, e = _read(buf, p)                      # community
    p = e
    tag, p, _ = _read(buf, p)                    # PDU
    if tag != 0xA2:
        raise ValueError('not a response')
    vals = []
    for _ in range(3):                           # request-id, error-status, error-index
        _, s, e = _read(buf, p)
        vals.append(int.from_bytes(buf[s:e], 'big', signed=True))
        p = e
    _, p, vend = _read(buf, p)
    vbs = []
    while p < vend:
        _, s, e = _read(buf, p)
        _, s1, e1 = _read(buf, s)
        t2, s2, e2 = _read(buf, e1)
        vbs.append((decode_oid(buf[s1:e1]), _value(t2, buf[s2:e2])))
        p = e
    return vals[0], vals[1], vals[2], vbs


# ---------------------------------------------------------------- transport
class _Proto(asyncio.DatagramProtocol):
    def __init__(self):
        self.waiters = {}

    def datagram_received(self, data, addr):
        try:
            res = parse_response(data)
        except Exception:
            return
        f = self.waiters.pop(res[0], None)
        if f and not f.done():
            f.set_result(res)

    def error_received(self, exc):
        for f in list(self.waiters.values()):
            if not f.done():
                f.set_exception(SnmpUnreachable(str(exc)))
        self.waiters.clear()


def norm(oid):
    return oid.strip('.')


class SnmpSession:
    """async with SnmpSession(ip, 'public') as s: values = await s.get([...])"""

    CHUNK = 20

    def __init__(self, host, community='public', version=V2C, timeout=1.2, retries=1, port=161):
        self.host, self.community, self.version = host, community, version
        self.timeout, self.retries, self.port = timeout, retries, port
        self.transport = self.proto = None

    async def __aenter__(self):
        loop = asyncio.get_running_loop()
        self.transport, self.proto = await loop.create_datagram_endpoint(_Proto, remote_addr=(self.host, self.port))
        return self

    async def __aexit__(self, *exc):
        if self.transport:
            self.transport.close()

    async def _request(self, oids):
        loop = asyncio.get_running_loop()
        for _ in range(self.retries + 1):
            reqid = secrets.randbits(30) + 1
            fut = loop.create_future()
            self.proto.waiters[reqid] = fut
            self.transport.sendto(build_get(self.version, self.community, reqid, oids))
            try:
                return await asyncio.wait_for(fut, self.timeout)
            except asyncio.TimeoutError:
                self.proto.waiters.pop(reqid, None)
        raise SnmpTimeout(self.host)

    async def get(self, oids):
        """Returns {oid: value}; missing OIDs map to None. Raises SnmpTimeout."""
        oids = [norm(o) for o in oids]
        out = {}
        for i in range(0, len(oids), self.CHUNK):
            await self._get_chunk(oids[i:i + self.CHUNK], out)
        return out

    async def _get_chunk(self, oids, out):
        pending = list(oids)
        for _ in range(len(oids) + 1):
            if not pending:
                return
            _, err, idx, vbs = await self._request(pending)
            if err == 0:
                for o, (_, v) in zip(pending, vbs):
                    out[o] = v
                for o in pending[len(vbs):]:
                    out[o] = None
                return
            if err == 2 and 1 <= idx <= len(pending):      # v1 noSuchName: drop that OID, ask again
                out[pending.pop(idx - 1)] = None
                continue
            if err == 1 and len(pending) > 1:              # tooBig: split
                mid = len(pending) // 2
                await self._get_chunk(pending[:mid], out)
                await self._get_chunk(pending[mid:], out)
                return
            break
        for o in pending:
            out[o] = None

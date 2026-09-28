"""Logging to stdout (docker logs) plus a ring buffer shown in the web UI."""
import collections
import datetime
import logging
import os
import sys

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(os.environ.get('TZ') or 'UTC')
except Exception:  # unknown zone name
    TZ = datetime.timezone.utc

BUFFER = collections.deque(maxlen=2000)
log = logging.getLogger('toner')


class _Fmt(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.datetime.fromtimestamp(record.created, TZ).strftime('%Y-%m-%d %H:%M:%S')


class _Buf(logging.Handler):
    def emit(self, record):
        try:
            BUFFER.append(self.format(record))
        except Exception:
            pass


def setup():
    fmt = _Fmt('%(asctime)s  %(message)s')
    out = logging.StreamHandler(sys.stdout)
    out.setFormatter(fmt)
    buf = _Buf()
    buf.setFormatter(fmt)
    log.handlers[:] = [out, buf]
    log.setLevel(logging.INFO)
    log.propagate = False
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

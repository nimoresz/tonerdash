"""Infrastructure settings come from the environment (docker-compose / .env).
Everything you can change in the web UI lives in the database (table settings)."""
import os
import re
import socket

VERSION = '4.0'


def env(name, default=''):
    return os.environ.get(name, default).strip()


def env_bool(name, default=False):
    v = env(name)
    return default if not v else v.lower() in ('1', 'true', 'yes', 'on')


def split_list(v):
    return [x for x in re.split(r'[,;\s]+', v or '') if x]


DEMO = env_bool('DEMO')
ADMIN_USER = env('ADMIN_USER', 'admin') or 'admin'
ADMIN_PASSWORD = env('ADMIN_PASSWORD')
COOKIE_SECURE = env_bool('COOKIE_SECURE')
LISTEN_PORT = 8080
PUBLIC_PORT = env('WEB_PORT', '8080')
BIND_ADDR = env('BIND_ADDR', '127.0.0.1')
SERVER_NAME = env('SERVER_NAME') or socket.gethostname()
BRANDING_DIR = env('BRANDING_DIR', '/app/branding')
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')

DB_HOST = env('DB_HOST', 'db')
DB_PORT = int(env('DB_PORT', '5432') or 5432)
DB_NAME = env('DB_NAME', 'toner')
DB_USER = env('DB_USER', 'toner')
DB_PASSWORD_FILE = env('DB_PASSWORD_FILE', '/run/secrets/toner/db_password')


def db_password():
    v = env('DB_PASSWORD')
    if v:
        return v
    with open(DB_PASSWORD_FILE, encoding='utf-8') as f:
        return f.read().strip()


# Defaults for settings editable in the UI. Used until you save your own values.
DEFAULTS = {
    'orgName': '',
    'siteName': '',
    'subnets': split_list(env('SUBNETS')),
    'extraIps': split_list(env('EXTRA_IPS')),
    'excludeIps': [],
    'community': env('SNMP_COMMUNITY', 'public') or 'public',
    'pollSeconds': 300,
    'discoveryMinutes': 60,
    'warnPct': 25,
    'critPct': 10,
    'historyDays': 60,
    'forgetDays': 30,
    'hideWaste': True,
    'sessionHours': 12,
    'maxSupplies': 16,
}

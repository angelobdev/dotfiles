#!/usr/bin/env python3
"""Locale selection and shared message catalogs for desktop helpers."""
import functools
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ASSIGNMENT = re.compile(r'''^\s*(LANG|LC_MESSAGES)\s*=\s*(?:"([^"\n]*)"|'([^'\n]*)'|([^\s#"']+))\s*(?:\#.*)?$''')


def normalize(value):
    base = re.split(r'[.@]', str(value or '').strip().replace('-', '_'))[0].lower()
    return 'it_IT' if base == 'it' or base.startswith('it_') else 'en_US'


def language_from_config(text, environment=None):
    values = {}
    for line in text.splitlines():
        match = ASSIGNMENT.fullmatch(line)
        if match:
            values[match[1]] = next(value for value in match.groups()[1:] if value is not None)
    fallback = environment if environment is not None else os.environ
    return normalize(values.get('LC_MESSAGES') or values.get('LANG') or fallback.get('LC_ALL')
                     or fallback.get('LC_MESSAGES') or fallback.get('LANG'))


def language():
    try:
        text = Path('/etc/locale.conf').read_text()
    except OSError:
        text = ''
    return language_from_config(text)


@functools.lru_cache(maxsize=4)
def read_catalog(path, mtime_ns):
    try:
        data = json.loads(Path(path).read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def catalog(lang):
    path = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'quickshell/desktop/i18n' / (lang + '.json')
    try:
        return read_catalog(str(path), path.stat().st_mtime_ns)
    except OSError:
        return {}


def tr(message, args=()):
    translated = catalog(language()).get(message, catalog('en_US').get(message, message))
    return re.sub(r'%([1-9][0-9]*)', lambda m: str(args[int(m[1]) - 1]) if int(m[1]) <= len(args) else m[0], translated)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Usage: i18n.py MESSAGE [ARGUMENTS...]')
    if sys.argv[1] == '--notify':
        if len(sys.argv) != 4:
            sys.exit('Usage: i18n.py --notify TITLE MESSAGE')
        sys.exit(subprocess.run(['notify-send', tr(sys.argv[2]), tr(sys.argv[3])]).returncode)
    print(tr(sys.argv[1], sys.argv[2:]))

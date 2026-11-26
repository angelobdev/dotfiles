#!/usr/bin/env python3
"""The system time zone for the calendar panel: list prints the current zone and every zone with its offset from
UTC now, set ZONE changes it through timedated, which asks for an administrator through polkit."""
from i18n import tr
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones


def run(command, timeout):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def current():
    result = run(['timedatectl', 'show', '--property=Timezone', '--value'], 5)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    # Without timedated (a container): the zone /etc/localtime points to.
    target = str(Path('/etc/localtime').resolve())
    return target.split('/zoneinfo/', 1)[1] if '/zoneinfo/' in target else 'UTC'


def zones():
    result = run(['timedatectl', 'list-timezones'], 10)
    names = result.stdout.split() if result.returncode == 0 else []
    return names or sorted(available_timezones())


def offset(name, now=None):
    """Minutes east of UTC at now; None for a zone the zone database does not know."""
    now = now or datetime.now(timezone.utc)
    try:
        delta = now.astimezone(ZoneInfo(name)).utcoffset()
    except (ZoneInfoNotFoundError, ValueError):
        return None
    return round(delta.total_seconds() / 60)


def listing(now=None):
    zone = current()
    found = [{'name': name, 'offset': offset(name, now)} for name in zones()]
    return {'current': zone, 'offset': offset(zone, now), 'zones': [entry for entry in found if entry['offset'] is not None]}


def set_zone(name):
    if name not in zones():
        raise ValueError(tr('timezone.errors.unknown', [name]))
    # The polkit prompt waits for the user: a long timeout.
    result = run(['timedatectl', 'set-timezone', name], 300)
    if result.returncode != 0:
        message = result.stderr.strip()
        if 'access denied' in message.lower() or 'not authorized' in message.lower():
            raise ValueError(tr('timezone.errors.denied'))
        raise ValueError(tr('timezone.errors.failed', [message[:300]]))
    return {'current': current(), 'offset': offset(name)}


def main():
    arguments = sys.argv[1:]
    if arguments == ['list']:
        print(json.dumps(listing(), ensure_ascii=False))
        return 0
    if len(arguments) == 2 and arguments[0] == 'set':
        print(json.dumps(set_zone(arguments[1]), ensure_ascii=False))
        return 0
    print(tr('timezone.errors.usage'), file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

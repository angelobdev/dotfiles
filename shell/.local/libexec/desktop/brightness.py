#!/usr/bin/env python3
"""Read and set hardware brightness without invoking a shell or requiring sudo."""
from i18n import tr
import argparse
import json
import math
from pathlib import Path
import re
import select
import shutil
import subprocess
import sys
import time

BACKLIGHT = Path('/sys/class/backlight')


def run(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=8, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ValueError(tr('brightness.errors.timeout')) from exc
    except OSError as exc:
        raise ValueError(tr('brightness.errors.commandUnavailable')) from exc
    if result.returncode:
        raise ValueError(tr('brightness.errors.accessDenied'))
    return result.stdout.strip()


def validate_backend(backend):
    if not isinstance(backend, dict):
        raise ValueError(tr('brightness.errors.invalidConfiguration'))
    kind = backend.get('type')
    if kind == 'backlight':
        device = backend.get('device', '')
        if not isinstance(device, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]+', device) or device in ('.', '..'):
            raise ValueError(tr('brightness.errors.invalidBacklight'))
        if not (BACKLIGHT / device).is_dir():
            raise ValueError(tr('brightness.errors.backlightUnavailable'))
        return {'type': kind, 'device': device}
    if kind == 'ddc':
        bus = backend.get('bus')
        if not isinstance(bus, int) or isinstance(bus, bool) or not 0 <= bus <= 65535:
            raise ValueError(tr('brightness.errors.invalidDdcBus'))
        if not shutil.which('ddcutil'):
            raise ValueError(tr('brightness.errors.ddcutilMissing'))
        return {'type': kind, 'bus': bus}
    raise ValueError(tr('brightness.errors.configureHardware'))


def read_backend(backend):
    backend = validate_backend(backend)
    if backend['type'] == 'backlight':
        device = BACKLIGHT / backend['device']
        maximum = int((device / 'max_brightness').read_text())
        current = int((device / 'brightness').read_text())
    else:
        output = run(['ddcutil', '--bus', str(backend['bus']), 'getvcp', '10', '--terse'])
        match = re.search(r'^VCP 10 C (\d+) (\d+)\s*$', output, re.M)
        if not match:
            raise ValueError(tr('brightness.errors.ddcUnsupported'))
        current, maximum = map(int, match.groups())
    if maximum <= 0:
        raise ValueError(tr('brightness.errors.invalidMaximum'))
    return max(0, min(100, round(current * 100 / maximum))), maximum


def discover(names, mappings):
    if not isinstance(names, list) or not all(isinstance(n, str) for n in names) or not isinstance(mappings, dict):
        raise ValueError(tr('brightness.errors.invalidDisplayList'))
    backlights = sorted(p.name for p in BACKLIGHT.glob('*') if p.is_dir())
    internal = next((n for n in names if re.match(r'^(eDP|LVDS|DSI)-', n)), None)
    result = []
    for name in dict.fromkeys(names):
        backend = mappings.get(name)
        if backend is None and name == internal and len(backlights) == 1:
            backend = {'type': 'backlight', 'device': backlights[0]}
        row = {'name': name, 'available': False, 'percent': None, 'backend': backend, 'error': ''}
        try:
            if backend is None:
                raise ValueError(tr('brightness.errors.configureBackend'))
            row['percent'], _ = read_backend(backend)
            row['available'] = True
        except (ValueError, OSError) as exc:
            row['error'] = str(exc)
        result.append(row)
    return result


def set_brightness(backend, percent):
    if not math.isfinite(percent):
        raise ValueError(tr('brightness.errors.invalidPercent'))
    percent = max(1, min(100, round(percent)))
    backend = validate_backend(backend)
    if backend['type'] == 'backlight':
        run(['brightnessctl', '--class=backlight', '--device', backend['device'], 'set', f'{percent}%'])
    else:
        _, maximum = read_backend(backend)
        value = max(1, round(percent * maximum / 100))
        run(['ddcutil', '--bus', str(backend['bus']), 'setvcp', '10', str(value)])


def backlight_snapshot():
    levels = {}
    for device in BACKLIGHT.glob('*'):
        try:
            maximum = int((device / 'max_brightness').read_text())
            current = int((device / 'brightness').read_text())
            if maximum > 0:
                levels[device.name] = max(0, min(100, round(current * 100 / maximum)))
        except (OSError, ValueError):
            continue
    return levels


# Without a notification the levels are read again this often, for a driver that never sends one.
FALLBACK_SECONDS = 10


def wait_for_change(timeout):
    # The backlight core notifies actual_brightness (sysfs_notify) on every change, from the keys or a write:
    # waiting on it costs nothing, where reading every 150 ms woke the CPU seven times a second.
    files, poller = [], select.poll()
    try:
        for device in BACKLIGHT.glob('*'):
            try:
                handle = open(device / 'actual_brightness', 'rb', buffering=0)
            except OSError:
                continue
            handle.read()
            files.append(handle)
            poller.register(handle, select.POLLPRI | select.POLLERR)
        if files:
            poller.poll(timeout * 1000)
        else:
            time.sleep(timeout)
    finally:
        for handle in files:
            handle.close()


def watch_backlights():
    # Sysfs reads only: no subprocesses or DDC requests in this path.
    previous = None
    while True:
        levels = backlight_snapshot()
        if levels != previous:
            print(json.dumps(levels), flush=True)
            previous = levels
        wait_for_change(FALLBACK_SECONDS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    read = sub.add_parser('read')
    read.add_argument('monitors')
    read.add_argument('mappings')
    sub.add_parser('watch')
    write = sub.add_parser('set')
    write.add_argument('backend')
    write.add_argument('percent', type=float)
    args = parser.parse_args()
    try:
        if args.action == 'watch':
            watch_backlights()
        elif args.action == 'read':
            print(json.dumps(discover(json.loads(args.monitors), json.loads(args.mappings)), ensure_ascii=False))
        else:
            set_brightness(json.loads(args.backend), args.percent)
            print(json.dumps({'ok': True}))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())

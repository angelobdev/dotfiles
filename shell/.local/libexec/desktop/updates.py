#!/usr/bin/env python3
"""Available system updates (dnf and Flatpak) for the shell's update icon.

check: refresh the metadata and write ~/.local/state/desktop-shell/updates.json, which services/Updates.qml
watches (run by desktop-updates.timer 5 minutes after login and every 6 hours, and from the panel).
status: print that file.
"""
from common import write_atomic
from i18n import tr
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

STATE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'desktop-shell/updates.json'
# Packages whose update needs the Hyprland plugins rebuilt (scripts/install-hypr-plugins.py).
COMPOSITOR = ('hyprland', 'hyprland-devel', 'hyprland-libs')


def dnf_updates(output):
    updates = []
    for line in output.splitlines():
        fields = line.split('\t')
        if len(fields) == 3 and fields[0]:
            updates.append({'name': fields[0], 'version': fields[1], 'repo': fields[2]})
    return sorted(updates, key=lambda update: update['name'])


def flatpak_updates(output):
    updates = []
    for line in output.splitlines():
        fields = line.split('\t')
        if fields and fields[0].strip():
            updates.append({'id': fields[0].strip(), 'version': fields[1].strip() if len(fields) > 1 else '',
                            'origin': fields[2].strip() if len(fields) > 2 else ''})
    return updates


def run(command, timeout):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)


def check():
    errors = []
    packages = []
    try:
        result = run(['dnf', '-q', 'repoquery', '--refresh', '--upgrades', '--latest-limit=1',
                      '--queryformat', '%{name}\t%{evr}\t%{repoid}\n'], 600)
        if result.returncode == 0:
            packages = dnf_updates(result.stdout)
        else:
            errors.append(tr('updates.errors.dnf', [result.stderr.strip()[:200]]))
    except (OSError, subprocess.SubprocessError) as error:
        errors.append(tr('updates.errors.dnf', [str(error)]))
    apps = []
    try:
        result = run(['flatpak', 'remote-ls', '--updates', '--columns=application,version,origin'], 300)
        if result.returncode == 0:
            apps = flatpak_updates(result.stdout)
        else:
            errors.append(tr('updates.errors.flatpak', [result.stderr.strip()[:200]]))
    except FileNotFoundError:
        pass
    except (OSError, subprocess.SubprocessError) as error:
        errors.append(tr('updates.errors.flatpak', [str(error)]))
    return {'checked': round(time.time(), 3), 'packages': packages, 'flatpaks': apps,
            'compositor': any(package['name'] in COMPOSITOR for package in packages), 'errors': errors}


def main():
    arguments = sys.argv[1:]
    if arguments == ['check']:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        # The timer and the panel can start a check at the same time: one runs, the other waits for it.
        with (STATE.parent / '.updates.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            write_atomic(STATE, json.dumps(check(), ensure_ascii=False) + '\n')
        return 0
    if arguments == ['status']:
        try:
            print(STATE.read_text(encoding='utf-8'), end='')
        except OSError:
            print('{}')
        return 0
    print(tr('updates.errors.usage'), file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except OSError as error:
        print(error, file=sys.stderr)
        sys.exit(1)

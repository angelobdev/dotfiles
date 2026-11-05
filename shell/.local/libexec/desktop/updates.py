#!/usr/bin/env python3
"""Available system updates (dnf or pacman, and Flatpak) for the shell's update icon.

check: refresh the metadata and write ~/.local/state/desktop-shell/updates.json, which services/Updates.qml
watches (run by desktop-updates.timer 5 minutes after login and every 6 hours, 30 minutes after a failed check,
and from the panel).
status: print that file.
"""
from common import release_id, write_atomic
from i18n import tr
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

STATE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'desktop-shell/updates.json'
# After a failed source (offline, a mirror down), one more check this much later instead of the next 6-hour run.
RETRY = '30min'
# Packages whose update needs the Hyprland plugins rebuilt (scripts/install-hypr-plugins.py).
COMPOSITOR = ('hyprland', 'hyprland-devel', 'hyprland-libs')


def dnf_updates(output):
    updates = []
    for line in output.splitlines():
        fields = line.split('\t')
        if len(fields) == 3 and fields[0]:
            updates.append({'name': fields[0], 'version': fields[1], 'repo': fields[2]})
    return sorted(updates, key=lambda update: update['name'])


def pacman_updates(output):
    # checkupdates: "name old -> new" lines. pacman keeps no repository per update worth showing.
    updates = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[2] == '->':
            updates.append({'name': fields[0], 'version': fields[3], 'repo': ''})
    return sorted(updates, key=lambda update: update['name'])


def system_updates():
    # (updates, error): the listing of the distribution's package manager, or why it failed.
    if release_id() == 'arch':
        try:
            # checkupdates syncs a copy of the databases as the user: no root, the system's stay as they are.
            result = run(['checkupdates', '--nocolor'], 600)
        except (OSError, subprocess.SubprocessError) as error:
            return None, tr('updates.errors.pacman', [str(error)])
        if result.returncode in (0, 2):  # 2: nothing to update
            return pacman_updates(result.stdout), None
        return None, tr('updates.errors.pacman', [(result.stderr or result.stdout).strip()[:200]])
    try:
        result = run(['dnf', '-q', 'repoquery', '--refresh', '--upgrades', '--latest-limit=1',
                      '--queryformat', '%{name}\t%{evr}\t%{repoid}\n'], 600)
    except (OSError, subprocess.SubprocessError) as error:
        return None, tr('updates.errors.dnf', [str(error)])
    if result.returncode == 0:
        return dnf_updates(result.stdout), None
    return None, tr('updates.errors.dnf', [result.stderr.strip()[:200]])


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


def previous():
    try:
        value = json.loads(STATE.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def check(before=None):
    # A source that fails keeps the list it had: being offline is not "no updates", and the icon stays.
    before = before or {}
    errors = []
    packages = before.get('packages', []) if isinstance(before.get('packages'), list) else []
    listed, error = system_updates()
    if error:
        errors.append(error)
    else:
        packages = listed
    apps = before.get('flatpaks', []) if isinstance(before.get('flatpaks'), list) else []
    try:
        result = run(['flatpak', 'remote-ls', '--updates', '--columns=application,version,origin'], 300)
        if result.returncode == 0:
            apps = flatpak_updates(result.stdout)
        else:
            errors.append(tr('updates.errors.flatpak', [result.stderr.strip()[:200]]))
    except FileNotFoundError:
        apps = []
    except (OSError, subprocess.SubprocessError) as error:
        errors.append(tr('updates.errors.flatpak', [str(error)]))
    # The time of the last check that reached at least one source.
    checked = before.get('checked') if len(errors) == 2 else round(time.time(), 3)
    return {'checked': checked, 'packages': packages, 'flatpaks': apps,
            'compositor': any(package.get('name') in COMPOSITOR for package in packages), 'errors': errors}


def retry_later():
    # A transient timer: systemd-run refuses a second one while it waits, so retries never pile up.
    try:
        subprocess.run(['systemd-run', '--user', '--quiet', '--collect', '--on-active=' + RETRY, '--unit=desktop-updates-retry',
                        str(Path.home() / '.local/bin/desktop-updates'), 'check'], capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def main():
    arguments = sys.argv[1:]
    if arguments == ['check']:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        # The timer and the panel can start a check at the same time: one runs, the other waits for it.
        with (STATE.parent / '.updates.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = check(previous())
            write_atomic(STATE, json.dumps(result, ensure_ascii=False) + '\n')
        if result.get('errors'):
            retry_later()
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

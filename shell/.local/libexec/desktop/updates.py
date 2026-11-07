#!/usr/bin/env python3
"""Available updates (dnf or pacman, Flatpak, and the commits of this repository) for the shell's update icon.

check: refresh the metadata and write ~/.local/state/desktop-shell/updates.json, which services/Updates.qml
watches (run by desktop-updates.timer 5 minutes after login and every 6 hours, 30 minutes after a failed check,
and from the panel).
check repository: only the repository, the other lists as they were (after a pull from the updates screen).
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
# The clone this helper is linked from (Stow links every file, so the path resolves into it).
REPO = Path(__file__).resolve().parents[4]
# The new commits the panel lists; behind counts them all.
COMMITS = 50


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


def flatpak_listing():
    # (updates, error) of Flatpak, like system_updates; without Flatpak installed there is nothing to update.
    try:
        result = run(['flatpak', 'remote-ls', '--updates', '--columns=application,version,origin'], 300)
    except FileNotFoundError:
        return [], None
    except (OSError, subprocess.SubprocessError) as error:
        return None, tr('updates.errors.flatpak', [str(error)])
    if result.returncode == 0:
        return flatpak_updates(result.stdout), None
    return None, tr('updates.errors.flatpak', [result.stderr.strip()[:200]])


def flatpak_updates(output):
    updates = []
    for line in output.splitlines():
        fields = line.split('\t')
        if fields and fields[0].strip():
            updates.append({'id': fields[0].strip(), 'version': fields[1].strip() if len(fields) > 1 else '',
                            'origin': fields[2].strip() if len(fields) > 2 else ''})
    return updates


def git(*arguments):
    # Never a password or passphrase prompt (no one sees this run): ssh fails instead, unless the user set their own
    # command. The same as the updates screen of the guided installer.
    environment = dict(os.environ, GIT_TERMINAL_PROMPT='0', LC_ALL='C')
    command = ['git', '-C', str(REPO)]
    if 'GIT_SSH_COMMAND' not in environment and not subprocess.run(command + ['config', 'core.sshCommand'], capture_output=True,
                                                                   text=True, env=environment, timeout=10).stdout.strip():
        environment['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes'
    return subprocess.run(command + list(arguments), capture_output=True, text=True, env=environment, timeout=120)


def repository_updates():
    """(state, error): this repository against its upstream branch after a fetch, {} for a clone without one."""
    if not (REPO / '.git').exists() or not (REPO / 'scripts/install-desktop.py').is_file():
        return {}, None
    try:
        upstream = git('rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}')
        if upstream.returncode:
            return {}, None
        upstream = upstream.stdout.strip()
        fetched = git('fetch', '--quiet', upstream.split('/', 1)[0])
        if fetched.returncode:
            return None, tr('updates.errors.git', [(fetched.stderr or fetched.stdout).strip()[-200:]])
        behind = int(git('rev-list', '--count', 'HEAD..@{u}').stdout.strip() or 0)
        ahead = int(git('rev-list', '--count', '@{u}..HEAD').stdout.strip() or 0)
        log = git('log', f'--max-count={COMMITS}', '--format=%h%x09%s', 'HEAD..@{u}').stdout
        head = git('rev-parse', '--short', '@{u}').stdout.strip()
        dirty = bool(git('status', '--porcelain', '--untracked-files=no').stdout.strip())
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        return None, tr('updates.errors.git', [str(error)])
    commits = [{'hash': fields[0], 'subject': fields[1]} for fields in (line.split('\t', 1) for line in log.splitlines())
               if len(fields) == 2 and fields[0]]
    return {'upstream': upstream, 'head': head, 'behind': behind, 'ahead': ahead, 'dirty': dirty, 'commits': commits}, None


def run(command, timeout):
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)


def previous():
    try:
        value = json.loads(STATE.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def check(before=None, only=None):
    # A source that fails keeps the list it had: being offline is not "no updates", and the icon stays. only:
    # the sources to ask (a pull asks the repository again); the others keep their lists and errors, and the time
    # of the last check stays.
    before = before or {}
    sources = (
        ('packages', list, system_updates),
        ('flatpaks', list, flatpak_listing),
        ('repository', dict, repository_updates),
    )
    failed = before.get('failed') if isinstance(before.get('failed'), dict) else {}
    result, failures, reached = {}, {}, False
    for name, kind, listing in sources:
        kept = before.get(name) if isinstance(before.get(name), kind) else kind()
        if only is not None and name not in only:
            result[name] = kept
            if isinstance(failed.get(name), str):
                failures[name] = failed[name]
            continue
        listed, error = listing()
        if error:
            failures[name] = error
            result[name] = kept
        else:
            result[name] = listed
            # A clone without an upstream branch (or no clone) was not a check.
            reached = reached or name != 'repository' or bool(listed)
    # The time of the last check that reached at least one source.
    checked = round(time.time(), 3) if reached and only is None else before.get('checked')
    # errors: what the panel shows; failed: the same by source, for a check of only some of them.
    return dict(result, checked=checked, compositor=any(package.get('name') in COMPOSITOR for package in result['packages']),
                errors=list(failures.values()), failed=failures)


def retry_later():
    # A transient timer: systemd-run refuses a second one while it waits, so retries never pile up.
    try:
        subprocess.run(['systemd-run', '--user', '--quiet', '--collect', '--on-active=' + RETRY, '--unit=desktop-updates-retry',
                        str(Path.home() / '.local/bin/desktop-updates'), 'check'], capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def main():
    arguments = sys.argv[1:]
    if arguments in (['check'], ['check', 'repository']):
        STATE.parent.mkdir(parents=True, exist_ok=True)
        # The timer and the panel can start a check at the same time: one runs, the other waits for it.
        with (STATE.parent / '.updates.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = check(previous(), arguments[1:] or None)
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

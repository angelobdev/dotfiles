#!/usr/bin/env python3
"""Available updates (dnf or pacman, Flatpak, and the commits of this repository) for the shell's update icon.

check: refresh the metadata and write ~/.local/state/desktop-shell/updates.json, which services/Updates.qml
watches (run by desktop-updates.timer 5 minutes after login and every 6 hours, 30 minutes after a failed check,
and from the panel).
check repository: only the repository, the other lists as they were (after a pull from the updates screen).
status: print that file.
apply KEYS: apply system, flatpak and/or repository (comma-separated) in the background, as Settings does: the updates
screen's apply without the screen (install-tui.py --apply-updates), behind one pkexec prompt when root is needed
(privileged.py). Its state is in updates-apply.json, its output in updates-apply.log, and a notification gives the result.
apply-status: that state as JSON, with the end of the log.
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
APPLY = STATE.with_name('updates-apply.json')
APPLY_LOG = STATE.with_name('updates-apply.log')
APPLY_LOCK = STATE.with_name('.updates-apply.lock')
APPLY_KEYS = ('system', 'flatpak', 'repository')
# Keys whose apply needs root: the repository is a pull, as the desktop user.
ROOT_KEYS = ('system', 'flatpak')
LOG_LINES = 60
HERE = Path(__file__).resolve().parent


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


def read_apply():
    try:
        value = json.loads(APPLY.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def apply_running():
    # An apply holds the lock for as long as it runs.
    APPLY_LOCK.parent.mkdir(parents=True, exist_ok=True)
    with APPLY_LOCK.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(handle, fcntl.LOCK_UN)
    return False


def log_tail(count=LOG_LINES):
    try:
        lines = APPLY_LOG.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return []
    return [line for line in lines if line.strip()][-count:]


def apply(keys):
    keys = [key for key in APPLY_KEYS if key in keys]
    if not keys:
        print(tr('updates.errors.usage'), file=sys.stderr)
        return 2
    APPLY.parent.mkdir(parents=True, exist_ok=True)
    with APPLY_LOCK.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(tr('updates.apply.running'), file=sys.stderr)
            return 1
        # Hyprland among the packages: the plugins rebuild at the next login, which the result says.
        compositor = 'system' in keys and previous().get('compositor') is True
        started = int(time.time())
        write_atomic(APPLY, json.dumps({'running': True, 'keys': keys, 'started': started}) + '\n')
        command = [sys.executable, str(REPO / 'scripts/install-tui.py'), '--apply-updates', ','.join(keys)]
        if set(keys) & set(ROOT_KEYS):
            command = [sys.executable, str(HERE / 'privileged.py'), 'run', *command]
        with APPLY_LOG.open('w', encoding='utf-8') as log:
            status = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT).returncode
        write_atomic(APPLY, json.dumps({'running': False, 'keys': keys, 'started': started, 'finished': int(time.time()),
                                        'status': status, 'compositor': compositor and status == 0}) + '\n')
    if status == 0:
        body = tr('updates.apply.doneCompositor' if compositor else 'updates.apply.done')
        subprocess.run(['notify-send', '--app-name=' + tr('updates.title'), '--app-icon=system-software-update', tr('updates.title'), body],
                       check=False)
    else:
        lines = log_tail(5)
        subprocess.run(['notify-send', '--app-name=' + tr('updates.title'), '--app-icon=dialog-error', tr('updates.title'),
                        tr('updates.apply.failed', [lines[-1] if lines else str(status)])], check=False)
    return status


def apply_status():
    state = read_apply()
    if state.get('running') and not apply_running():
        state = {**state, 'running': False, 'status': -1}  # Stopped without writing its result.
    return {**state, 'log': log_tail()}


def main():
    return main_with(sys.argv[1:])


def main_with(arguments):
    if len(arguments) == 2 and arguments[0] == 'apply':
        return apply(arguments[1].split(','))
    if arguments == ['apply-status']:
        print(json.dumps(apply_status(), ensure_ascii=False))
        return 0
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

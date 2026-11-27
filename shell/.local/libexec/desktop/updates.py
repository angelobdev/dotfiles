#!/usr/bin/env python3
"""Available updates (dnf or pacman, Flatpak, firmware through fwupd, and the release or commits this repository follows) for
the shell's update icon, and whether a restart is needed for what an update replaced.

check: refresh the metadata and write ~/.local/state/desktop-shell/updates.json, which services/Updates.qml
watches (run by desktop-updates.timer 5 minutes after login and every 6 hours, 30 minutes after a failed check,
and from the panel).
check repository: only the repository, the other lists as they were (after a pull from the updates screen).
status: print that file.
apply KEYS: apply system, flatpak, firmware and/or repository (comma-separated) in the background, as Settings does: the
updates screen's apply without the screen (install-tui.py --apply-updates), behind one pkexec prompt when root is needed
(privileged.py). It refuses to start without room on the root file system, keeps the computer from sleeping while it
runs, and names a known cause when it fails. Its state is in updates-apply.json, its output in updates-apply.log, and
a notification gives the result.
apply-status: that state as JSON, with the end of the log.
"""
from common import last_lines, lock_held, read_json, release_id, write_atomic
from i18n import tr
import channel
import fcntl
import functools
import json
import os
from pathlib import Path
import platform
import re
import shutil
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
APPLY_KEYS = ('system', 'flatpak', 'firmware', 'repository')
# Keys whose apply needs root: the repository is a pull, as the desktop user.
ROOT_KEYS = ('system', 'flatpak', 'firmware')
# Room an update of the system, Flatpak or firmware needs on the root file system before it starts (bytes).
FREE_SPACE = 2 * 1024 ** 3
# What a failed apply says in its log, to name the cause in the notification and the panel: the first that matches.
FAILURES = (
    ('space', r'No space left on device|not enough free disk space|Insufficient space|Disk Requirements'),
    ('network', r'Could not resolve host|Curl error|Cannot download|failed retrieving file|Failed to download|Network is unreachable'),
    ('signature', r'GPG check FAILED|invalid or corrupted package|signature .* is (invalid|unknown trust)|key .* could not be (looked up|imported)'),
    ('conflict', r'exists in filesystem|conflicting files|conflicts with file from package|Problem( \d+)?: '),
    ('lock', r'unable to lock database|Waiting for process with pid|already locked'),
    ('initramfs', r'dracut(-install)?\[?.*(ERROR|[Ff]ailed)|mkinitcpio.*(ERROR|[Ff]ailed)|==> ERROR'),
    ('authorization', r'Not authorized|authentication (failed|dismissed)|Request dismissed|pkexec.*(dismissed|not authorized)'),
)
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


def firmware_listing():
    # (updates, error): devices with a newer firmware in fwupd's metadata (kept current by fwupd-refresh.timer);
    # nothing without fwupd. get-updates exits 2 when there is nothing to update.
    if not shutil.which('fwupdmgr'):
        return [], None
    try:
        result = run(['fwupdmgr', 'get-updates', '--json'], 120)
    except (OSError, subprocess.SubprocessError) as error:
        return None, tr('updates.errors.firmware', [str(error)])
    if result.returncode not in (0, 2):
        return None, tr('updates.errors.firmware', [(result.stderr or result.stdout).strip()[:200]])
    return firmware_updates(result.stdout), None


def firmware_updates(output):
    try:
        devices = json.loads(output or '{}').get('Devices', [])
    except (ValueError, AttributeError):
        return []
    updates = []
    for device in devices if isinstance(devices, list) else []:
        releases = device.get('Releases') if isinstance(device, dict) else None
        if not releases:
            continue
        updates.append({'name': str(device.get('Name', '')), 'version': str(releases[0].get('Version', '')),
                        'current': str(device.get('Version', ''))})
    return updates


def kernel_replaced(modules='/usr/lib/modules'):
    # Arch keeps the modules of the installed kernel only: the running one's gone means a new kernel is installed.
    return not Path(modules, platform.release()).is_dir()


def dnf_restart(output):
    # dnf5 needs-restarting --json: [{"type": "reboot", "reboot_required": true, "packages": [...]}].
    try:
        entries = json.loads(output or '[]')
    except ValueError:
        return []
    reasons = []
    for entry in entries if isinstance(entries, list) else []:
        if isinstance(entry, dict) and entry.get('type') == 'reboot' and entry.get('reboot_required'):
            packages = [str(name) for name in entry.get('packages', [])]
            reasons.append('kernel' if any(name.startswith('kernel') for name in packages) else 'system')
    return sorted(set(reasons))


def compositor_replaced(proc='/proc'):
    # A running Hyprland whose binary an update replaced: the old one keeps running until the next login.
    for status in Path(proc).glob('[0-9]*/comm'):
        try:
            if status.read_text().strip() == 'Hyprland' and os.readlink(status.parent / 'exe').endswith(' (deleted)'):
                return True
        except OSError:
            continue
    return False


# fwupd's UpdateState of a device whose update waits for the reboot (FWUPD_UPDATE_STATE_NEEDS_REBOOT). Its
# "needs-reboot" flag is not that: it says the device is updated through a reboot at all.
NEEDS_REBOOT = (4, 'needs-reboot')


def firmware_waiting(output):
    try:
        devices = json.loads(output or '{}').get('Devices', [])
    except (ValueError, AttributeError):
        return False
    return any(device.get('UpdateState') in NEEDS_REBOOT for device in devices if isinstance(device, dict))


def firmware_pending_reboot():
    # A firmware update staged for the next boot (UEFI capsules).
    if not shutil.which('fwupdmgr'):
        return False
    try:
        return firmware_waiting(run(['fwupdmgr', 'get-devices', '--json'], 60).stdout)
    except (OSError, subprocess.SubprocessError):
        return False


def restart_state():
    """{needed, reasons}: what an update left running in its old version. kernel: a new kernel is installed; system:
    core libraries dnf names; compositor: Hyprland's binary was replaced; firmware: an update waits for the reboot."""
    reasons = []
    if release_id() == 'arch':
        if kernel_replaced():
            reasons.append('kernel')
    elif shutil.which('dnf'):
        try:
            reasons += dnf_restart(run(['dnf', '-q', 'needs-restarting', '--json'], 120).stdout)
        except (OSError, subprocess.SubprocessError):
            pass
    if compositor_replaced():
        reasons.append('compositor')
    if firmware_pending_reboot():
        reasons.append('firmware')
    return {'needed': bool(reasons), 'reasons': reasons}


def flatpak_updates(output):
    updates = []
    for line in output.splitlines():
        fields = line.split('\t')
        if fields and fields[0].strip():
            updates.append({'id': fields[0].strip(), 'version': fields[1].strip() if len(fields) > 1 else '',
                            'origin': fields[2].strip() if len(fields) > 2 else ''})
    return updates


# Never a password or passphrase prompt (no one sees this run): ssh fails instead, unless the user set their own
# command. The same as the updates screen of the guided installer. Worked out once per run: it asks git itself.
@functools.cache
def git_environment():
    environment = dict(os.environ, GIT_TERMINAL_PROMPT='0', LC_ALL='C')
    if 'GIT_SSH_COMMAND' not in environment and not subprocess.run(['git', '-C', str(REPO), 'config', 'core.sshCommand'],
                                                                   capture_output=True, text=True, env=environment,
                                                                   timeout=10).stdout.strip():
        environment['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes'
    return environment


def git(*arguments):
    return subprocess.run(['git', '-C', str(REPO), *arguments], capture_output=True, text=True, env=git_environment(), timeout=120)


def repository_updates():
    """(state, error): this repository against the branch it follows (channel.py: stable, or its upstream for a
    maintainer) after a fetch, {} for a clone without an upstream branch."""
    if not (REPO / '.git').exists() or not (REPO / 'scripts/install-desktop.py').is_file():
        return {}, None
    try:
        upstream, remote = channel.upstream(git)
        if remote is None:
            return {}, None
        fetched = git('fetch', '--quiet', remote)
        if fetched.returncode:
            return None, tr('updates.errors.git', [(fetched.stderr or fetched.stdout).strip()[-200:]])
        followed = channel.target(git, upstream, remote)
        behind = int(git('rev-list', '--count', f'HEAD..{followed}').stdout.strip() or 0)
        ahead = int(git('rev-list', '--count', f'{followed}..HEAD').stdout.strip() or 0)
        log = git('log', f'--max-count={COMMITS}', '--format=%h%x09%s', f'HEAD..{followed}').stdout
        head = git('rev-parse', '--short', followed).stdout.strip()
        dirty = bool(git('status', '--porcelain', '--untracked-files=no').stdout.strip())
        installed = channel.version(git)
        latest = channel.version(git, followed) if behind else installed
        notes = channel.between(channel.changelog_at(git, followed), installed, latest) if latest != installed else []
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        return None, tr('updates.errors.git', [str(error)])
    commits = [{'hash': fields[0], 'subject': fields[1]} for fields in (line.split('\t', 1) for line in log.splitlines())
               if len(fields) == 2 and fields[0]]
    return {'upstream': followed, 'head': head, 'behind': behind, 'ahead': ahead, 'dirty': dirty, 'commits': commits,
            'version': installed, 'latest': latest, 'notes': notes}, None


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
        ('firmware', list, firmware_listing),
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
            # A clone without an upstream branch (or no clone) was not a check; nor is fwupd, which reads metadata
            # already on the disk.
            reached = reached or name not in ('repository', 'firmware') or bool(listed)
    # The time of the last check that reached at least one source.
    checked = round(time.time(), 3) if reached and only is None else before.get('checked')
    # errors: what the panel shows; failed: the same by source, for a check of only some of them.
    # Asked at every check: an update made outside the panel (dnf in a terminal) needs the restart just as well.
    restart = restart_state() if only is None else before.get('restart', {'needed': False, 'reasons': []})
    return dict(result, checked=checked, compositor=any(package.get('name') in COMPOSITOR for package in result['packages']),
                restart=restart, errors=list(failures.values()), failed=failures)


def retry_later():
    # A transient timer: systemd-run refuses a second one while it waits, so retries never pile up.
    try:
        subprocess.run(['systemd-run', '--user', '--quiet', '--collect', '--on-active=' + RETRY, '--unit=desktop-updates-retry',
                        str(Path.home() / '.local/bin/desktop-updates'), 'check'], capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def read_apply():
    return read_json(APPLY)


def apply_running():
    # An apply holds the lock for as long as it runs.
    return lock_held(APPLY_LOCK)


def log_tail(count=LOG_LINES):
    return last_lines(APPLY_LOG, count)


# The catalog key of each cause in FAILURES.
REASON_KEYS = {reason: 'updates.apply.reasons.' + reason for reason, _ in FAILURES}


def failure_reason(lines):
    """The known cause of a failed apply (FAILURES), '' for none."""
    text = '\n'.join(lines)
    for reason, pattern in FAILURES:
        if re.search(pattern, text):
            return reason
    return ''


def free_space(path='/'):
    try:
        return shutil.disk_usage(path).free
    except OSError:
        return FREE_SPACE


def notify(icon, body):
    subprocess.run(['notify-send', '--app-name=' + tr('updates.title'), '--app-icon=' + icon, tr('updates.title'), body], check=False)


def apply(keys):
    keys = [key for key in APPLY_KEYS if key in keys]
    if not keys:
        print(tr('updates.errors.usage'), file=sys.stderr)
        return 2
    APPLY.parent.mkdir(parents=True, exist_ok=True)
    # Packages and Flatpak apps unpack on the root file system, and a transaction that runs out of room halfway
    # leaves the system between versions.
    if set(keys) & set(ROOT_KEYS) and free_space() < FREE_SPACE:
        now = int(time.time())
        write_atomic(APPLY, json.dumps({'running': False, 'keys': keys, 'started': now, 'finished': now, 'status': 1,
                                        'reason': 'space'}) + '\n')
        notify('dialog-error', tr('updates.apply.noSpace', [round(free_space() / 1024 ** 3, 1)]))
        return 1
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
        # No suspend, idle sleep or lid-close sleep halfway through a transaction (the lock screen still comes).
        if shutil.which('systemd-inhibit'):
            command = ['systemd-inhibit', '--what=sleep:handle-lid-switch', '--mode=block', '--who=' + tr('updates.title'),
                       '--why=' + tr('updates.apply.inhibit'), *command]
        with APPLY_LOG.open('w', encoding='utf-8') as log:
            status = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT).returncode
        reason = failure_reason(log_tail()) if status else ''
        write_atomic(APPLY, json.dumps({'running': False, 'keys': keys, 'started': started, 'finished': int(time.time()),
                                        'status': status, 'compositor': compositor and status == 0, 'reason': reason}) + '\n')
    if status == 0:
        restart = restart_state()
        body = tr('updates.apply.doneCompositor' if compositor else 'updates.apply.done')
        if restart['needed'] and not compositor:
            body = tr('updates.apply.doneRestart')
        notify('system-software-update', body)
    else:
        lines = log_tail(5)
        cause = tr(REASON_KEYS[reason]) if reason else (lines[-1] if lines else str(status))
        notify('dialog-error', tr('updates.apply.failed', [cause]))
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

#!/usr/bin/env python3
"""The Hyprland plugins of this packaging, for the session and Settings → System → Plugins.

plugins.py [reload]      At Hyprland startup: load the plugins built from this packaging for this compositor. When they
                         need a rebuild, ask for one: the shell starts it (plugins.py rebuild) once its polkit agent is up.
plugins.py status        JSON for the Plugins tab: the bundle, each plugin, the build cache and the last rebuild.
plugins.py rebuild       Rebuild in the background with one pkexec prompt (privileged.py), output in the rebuild log.
plugins.py clear-cache old|all
                         Remove build cache entries no plugin would reuse, or all of them.
"""
from common import last_lines, lock_held, read_json, write_atomic
from i18n import tr
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

# The repository behind the Stow link: the plugin packaging and its installer live there.
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'scripts/hyprpm'))
import build  # noqa: E402
import bundle  # noqa: E402

HERE = Path(__file__).resolve().parent
STATE = bundle.STAMP.parent
# The last rebuild: {"wanted": reason} until the shell starts it, then running, then its result.
REBUILD = STATE / 'plugin-rebuild.json'
LOG = STATE / 'plugin-rebuild.log'
LOCK = STATE / 'plugin-rebuild.lock'
LOG_LINES = 60


def output(*args):
    return subprocess.check_output(args, text=True)


def notify(title, body):
    subprocess.run(['notify-send', title, body], check=False)


def session_matches(stamp):
    running = json.loads(output('hyprctl', '-j', 'version'))
    devel = bundle.package_version(bundle.headers_package())
    instances = json.loads(output('hyprctl', '-j', 'instances'))
    instance = next(x for x in instances if x['instance'] == os.environ['HYPRLAND_INSTANCE_SIGNATURE'])
    return (devel == stamp['rpm'] and all(running.get(k) == stamp.get(k) for k in ('version', 'abiHash'))
            and os.path.samefile('/proc/' + str(instance['pid']) + '/exe', '/usr/bin/Hyprland'))


def read_rebuild():
    return read_json(REBUILD)


def write_rebuild(value):
    # Atomic, through a temporary file of its own: two writers (the shell's rebuild, a login rebuild) never share one.
    STATE.mkdir(parents=True, exist_ok=True)
    write_atomic(REBUILD, json.dumps(value) + '\n')


def locked():
    # A rebuild holds the lock for as long as it runs.
    return lock_held(LOCK)


def ask_rebuild(state):
    # At Hyprland startup, before anything has loaded them: the only safe time to replace the plugins. The shell runs it,
    # since the pkexec prompt needs its polkit agent, which is not up yet.
    if not locked():
        write_rebuild({'wanted': state, 'since': int(time.time())})
    notify(tr('plugins.rebuildTitle'), tr('plugins.rebuild.' + state))


def reload():
    state = bundle.status()
    if state == bundle.MISSING:
        return  # First installation: the installer's autostart builds them, with no sudo prompts or retry loops here.
    if state in (bundle.INCOMPLETE, bundle.PACKAGING_CHANGED, bundle.COMPOSITOR_CHANGED):
        ask_rebuild(state)
        return
    if state == bundle.MISMATCHED:
        notify(tr('plugins.notificationTitle'), tr('plugins.errors.headersMismatch'))
        sys.exit(tr('plugins.errors.headersMismatch'))
    if state != bundle.CURRENT or not session_matches(bundle.stamp()):
        notify(tr('plugins.notificationTitle'), tr('plugins.errors.rebuildRequired'))
        sys.exit(tr('plugins.errors.unverifiedBuild'))
    subprocess.run(['hyprpm', 'reload'], check=True)
    # Built and loaded: a rebuild asked for earlier and never started is not needed any more.
    if read_rebuild().get('wanted') and not locked():
        REBUILD.unlink(missing_ok=True)


def up_to_date():
    # Built from this packaging and all loaded: install-hypr-plugins.py would do nothing, so no prompt is needed.
    return bundle.status() == bundle.CURRENT and set(bundle.selected()) <= loaded()


def rebuild():
    STATE.mkdir(parents=True, exist_ok=True)
    with open(LOCK, 'a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit(tr('plugins.errors.running'))
        reason = read_rebuild().get('wanted', 'manual')
        started = int(time.time())
        if up_to_date():
            # A request left from before (or a rebuild made in a terminal since): nothing to ask a password for.
            write_rebuild({'running': False, 'reason': reason, 'started': started, 'finished': started, 'status': 0})
            return 0
        write_rebuild({'running': True, 'reason': reason, 'started': started})
        command = [sys.executable, str(HERE / 'privileged.py'), 'run', sys.executable, str(REPO / 'scripts/install-hypr-plugins.py')]
        with open(LOG, 'w', encoding='utf-8') as log:
            status = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT).returncode
        write_rebuild({'running': False, 'reason': reason, 'started': started, 'finished': int(time.time()), 'status': status})
    if status == 0:
        notify(tr('plugins.rebuildTitle'), tr('plugins.background.done'))
    else:
        notify(tr('plugins.notificationTitle'), tr('plugins.background.failed', [last_line()]))
    return status


def last_line():
    lines = log_tail(5)
    return lines[-1] if lines else ''


def log_tail(count=LOG_LINES):
    return last_lines(LOG, count)


def loaded():
    # With nothing loaded, hyprctl answers in words, not JSON.
    try:
        return {plugin['name'] for plugin in json.loads(output('hyprctl', '-j', 'plugin', 'list'))}
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError):
        return set()


def size(path):
    total = 0
    for folder, _directories, files in os.walk(path):
        for name in files:
            try:
                total += os.lstat(os.path.join(folder, name)).st_size
            except OSError:
                pass
    return total


def current_keys():
    # The key each plugin would build under now; none when Hyprland is missing (then nothing is current).
    try:
        return {name: build.cache_key(name) for name in build.PLUGINS}
    except (OSError, subprocess.CalledProcessError, ValueError):
        return {}


def cache_entries():
    keys = current_keys()
    entries = []
    if not build.CACHE.is_dir():
        return entries
    for plugin in sorted(build.CACHE.iterdir()):
        if not plugin.is_dir():
            continue
        children = [child for child in plugin.iterdir() if child.is_dir()] if plugin.name in build.PLUGINS else [plugin]
        for child in children:
            entries.append({'plugin': plugin.name if plugin.name in build.PLUGINS else '', 'key': child.name,
                            'bytes': size(child), 'current': keys.get(plugin.name) == child.name})
    return entries


def status():
    state = bundle.repository_state()
    selected = bundle.selected()
    in_use = loaded()
    plugins = []
    for name, (repo, revision, _artifact) in build.PLUGINS.items():
        built = name in state and not state[name].get('failed', True)
        plugins.append({'name': name, 'repo': repo, 'revision': revision, 'profile': bundle.PROFILE_OF.get(name, 'core'),
                        'selected': name in selected, 'built': built, 'loaded': name in in_use})
    entries = cache_entries()
    rebuilding = read_rebuild()
    if rebuilding.get('running') and not locked():
        rebuilding = {**rebuilding, 'running': False, 'status': -1}  # Stopped without writing its result.
    return {
        'state': bundle.status(),
        'hyprland': bundle.package_version('hyprland'),
        'verified': list(bundle.VERIFIED),
        'plugins': plugins,
        'cache': {'bytes': sum(entry['bytes'] for entry in entries), 'entries': entries},
        'rebuild': {**rebuilding, 'log': log_tail()},
    }


def clear_cache(kind):
    if locked():
        sys.exit(tr('plugins.errors.running'))
    if kind == 'all':
        shutil.rmtree(build.CACHE, ignore_errors=True)
        return
    for entry in cache_entries():
        if not entry['current']:
            path = build.CACHE / entry['plugin'] / entry['key'] if entry['plugin'] else build.CACHE / entry['key']
            shutil.rmtree(path, ignore_errors=True)
    for plugin in build.CACHE.iterdir() if build.CACHE.is_dir() else ():
        if plugin.is_dir() and not any(plugin.iterdir()):
            plugin.rmdir()


def main(arguments):
    if arguments in ([], ['reload']):
        reload()
    elif arguments == ['status']:
        print(json.dumps(status(), ensure_ascii=False))
    elif arguments == ['rebuild']:
        return rebuild()
    elif len(arguments) == 2 and arguments[0] == 'clear-cache' and arguments[1] in ('old', 'all'):
        clear_cache(arguments[1])
    else:
        sys.exit(__doc__)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as error:
        sys.exit(str(error))

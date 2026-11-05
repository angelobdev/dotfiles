#!/usr/bin/env python3
"""Autoload only plugins built from this packaging for this running and installed compositor; rebuild the others."""
from i18n import tr
import json
import os
from pathlib import Path
import subprocess
import sys

# The repository behind the Stow link: the plugin packaging and its installer live there.
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'scripts/hyprpm'))
import bundle  # noqa: E402


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


def rebuild(state):
    # This runs at Hyprland startup, before anything has loaded them: the only safe time to replace the plugins.
    notify(tr('plugins.rebuildTitle'), tr('plugins.rebuild.' + state))
    subprocess.Popen(['kitty', '--hold', '--title', tr('plugins.rebuildTitle'), str(REPO / 'scripts/install-hypr-plugins.py')],
                     stdin=subprocess.DEVNULL, start_new_session=True)


def main():
    state = bundle.status()
    if state == bundle.MISSING:
        return  # First installation: the installer's autostart builds them, with no sudo prompts or retry loops here.
    if state in (bundle.INCOMPLETE, bundle.PACKAGING_CHANGED, bundle.COMPOSITOR_CHANGED):
        rebuild(state)
        return
    if state == bundle.MISMATCHED:
        notify(tr('plugins.notificationTitle'), tr('plugins.errors.headersMismatch'))
        sys.exit(tr('plugins.errors.headersMismatch'))
    if state != bundle.CURRENT or not session_matches(bundle.stamp()):
        notify(tr('plugins.notificationTitle'), tr('plugins.errors.rebuildRequired'))
        sys.exit(tr('plugins.errors.unverifiedBuild'))
    subprocess.run(['hyprpm', 'reload'], check=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as error:
        sys.exit(str(error))

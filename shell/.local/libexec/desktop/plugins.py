#!/usr/bin/env python3
"""Autoload only plugins built for this running and installed Fedora compositor."""
from i18n import tr
import json
import os
from pathlib import Path
import subprocess
import sys


def output(*args):
    return subprocess.check_output(args, text=True)


def main():
    stamp_path = Path.home() / '.local/state/dotfiles/hypr-plugins.json'
    if not stamp_path.exists():
        return  # First installation: no sudo prompts or retry loops at login.
    stamp = json.loads(stamp_path.read_text())
    running = json.loads(output('hyprctl', '-j', 'version'))
    rpm = output('rpm', '-q', '--qf', '%{VERSION}-%{RELEASE}.%{ARCH}', 'hyprland')
    devel = output('rpm', '-q', '--qf', '%{VERSION}-%{RELEASE}.%{ARCH}', 'hyprland-devel')
    instances = json.loads(output('hyprctl', '-j', 'instances'))
    instance = next(x for x in instances if x['instance'] == os.environ['HYPRLAND_INSTANCE_SIGNATURE'])
    matches = (rpm == devel == stamp['rpm'] and all(running.get(k) == stamp.get(k) for k in ('version', 'abiHash'))
               and os.path.samefile('/proc/' + str(instance['pid']) + '/exe', '/usr/bin/Hyprland'))
    if not matches:
        subprocess.run(['notify-send', tr('plugins.notificationTitle'), tr('plugins.errors.rebuildRequired')], check=False)
        sys.exit(tr('plugins.errors.unverifiedBuild'))
    subprocess.run(['hyprpm', 'reload'], check=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as error:
        sys.exit(str(error))

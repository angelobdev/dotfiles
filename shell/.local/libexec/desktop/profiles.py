#!/usr/bin/env python3
"""The installer's profiles for Settings → System → Profiles: what of each is on this system, and how to add or
remove one without a terminal.

list: every profile as JSON: installed (all of it there), done of total (what it sets up that can be seen without
sudo: packages, swaps, AUR packages, release archives, Stow links), recorded (in the installer's record), default.
plan install NAME / plan remove NAME: JSON with the installer's commands for it: preview (its dry-run, as the
desktop user) and apply (run by jobs.py behind one pkexec prompt), and blocked, a reason it cannot run now.
Install keeps the recorded profiles and adds NAME; remove undoes what only NAME set up.
"""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys

from i18n import tr

# This file is a Stow link into the repository: shell/.local/libexec/desktop/profiles.py.
REPO = Path(__file__).resolve().parents[4]


def installer_screens():
    # install-tui.py, which loads install-desktop.py: the same state its profiles screen shows.
    spec = importlib.util.spec_from_file_location('install_tui', REPO / 'scripts/install-tui.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def listing():
    try:
        tui = installer_screens()
        installer = tui.installer
        # Quiet: the installer prints warnings, and exits on a distribution it does not support.
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            plan = installer.load_plan(('core',))
            plan.distro.remember_answers()
            recorded = tui.recorded_profiles()
            defaults = installer.default_profiles().split(',')
            rows = []
            for name in installer.PROFILES:
                status = tui.profile_status(plan, name)
                rows.append({'name': name, 'installed': tui.installed(status), 'done': status.total - len(status.missing),
                             'total': status.total, 'recorded': name in recorded, 'default': name in defaults})
    except SystemExit as stop:
        return {'profiles': [], 'error': str(stop.code or '')}
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        return {'profiles': [], 'error': str(error)}
    return {'profiles': rows, 'error': ''}


def checked(name):
    names = [profile for profile in name.split(',') if profile]
    if not names or not all(profile.replace('-', '').isalnum() for profile in names):
        raise ValueError(tr('settings.profiles.errors.name', [name]))
    return names


def plan(action, name):
    names = checked(name)
    tui = installer_screens()
    installer = tui.installer
    script = [sys.executable, str(REPO / 'scripts/install-desktop.py')]
    blocked = ''
    if action == 'install':
        if set(names) - set(installer.PROFILES):
            raise ValueError(tr('settings.profiles.errors.name', [name]))
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            recorded = tui.recorded_profiles()
        wanted = [profile for profile in installer.PROFILES if profile == 'core' or profile in recorded or profile in names]
        arguments = ['--profiles', ','.join(wanted)]
    else:
        if not installer.removable_profiles(tuple(names)):
            raise ValueError(tr('settings.profiles.errors.name', [name]))
        arguments = ['--remove', ','.join(names)]
        # The running Hyprland has the plugins loaded: the installer refuses, and so does this, before the prompt.
        if 'plugins' in names and installer.hyprland_running():
            blocked = tr('settings.profiles.pluginsInSession')
    return {'preview': script + ['dry-run', *arguments], 'apply': script + ['apply', *arguments], 'blocked': blocked}


def main(arguments):
    if arguments == ['list']:
        print(json.dumps(listing(), ensure_ascii=False))
    elif len(arguments) == 3 and arguments[0] == 'plan' and arguments[1] in ('install', 'remove'):
        print(json.dumps(plan(arguments[1], arguments[2])))
    else:
        raise ValueError(__doc__)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

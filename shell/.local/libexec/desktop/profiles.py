#!/usr/bin/env python3
"""The installer's profiles for Settings → System → Profiles: what of each is on this system, and the guided
installer to add or remove one.

list: every profile as JSON: installed (all of it there), done of total (what it sets up that can be seen without
sudo: packages, swaps, AUR packages, release archives, Stow links), recorded (in the installer's record), default.
install NAME: the guided installer on the profiles, NAME checked on top of the installed ones (desktop-manager --add).
remove NAME: the guided installer on the review of removing NAME (desktop-manager --remove).
Both run in a Kitty window, where the plan is reviewed and sudo asks, and wait until it closes.
"""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from i18n import tr

# This file is a Stow link into the repository: shell/.local/libexec/desktop/profiles.py.
REPO = Path(__file__).resolve().parents[4]
MANAGER = Path.home() / '.local/bin/desktop-manager'


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


def run_manager(name, flag, title):
    names = [profile for profile in name.split(',') if profile]
    if not names or not all(profile.replace('-', '').isalnum() for profile in names):
        raise ValueError(tr('settings.profiles.errors.name', [name]))
    # The window stays until Enter, with the installer's last words.
    script = (f'{shlex.quote(str(MANAGER))} {flag} {shlex.quote(",".join(names))}\n'
              f'printf "\\n%s" {shlex.quote(tr("settings.profiles.close"))}\n'
              'read -r _\n')
    # desktop-updates: the window rule that floats a terminal in the middle (hypr/config/rules.lua).
    subprocess.run(['kitty', '--class', 'desktop-updates', '--title', tr(title, [', '.join(names)]), 'sh', '-c', script], check=False)


def main(arguments):
    if arguments == ['list']:
        print(json.dumps(listing(), ensure_ascii=False))
    elif len(arguments) == 2 and arguments[0] == 'install':
        run_manager(arguments[1], '--add', 'settings.profiles.installTitle')
    elif len(arguments) == 2 and arguments[0] == 'remove':
        run_manager(arguments[1], '--remove', 'settings.profiles.removeTitle')
    else:
        raise ValueError(__doc__)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

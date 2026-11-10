#!/usr/bin/env python3
"""The installer's profiles and their parts for Settings → System → Profiles: what of each is on this system, and how
to add or remove them without a terminal.

list: every profile as JSON: installed, done of total (what it sets up that can be seen without sudo: packages, swaps,
AUR packages, release archives, Stow links), recorded (in the installer's record), default, and its parts, each with
the same fields.
plan install UNITS / plan remove UNITS / plan change ADD REMOVE: JSON with the commands for it: preview (the dry-run,
as the desktop user) and apply (run by jobs.py behind one pkexec prompt), and blocked, a reason it cannot run now.
Units are profiles or parts (profile.part), comma-separated; "-" is none. Install keeps the recorded units and adds
these, a profile with its default parts; remove undoes what only they set up, a profile with all of its parts; change
does both, the adding first. Both keep the units found installed without a record, and record them.
run dry-run|apply ADD REMOVE: the installer for a change, one run after the other.
"""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import re
from pathlib import Path
import subprocess
import sys

from i18n import tr

# This file is a Stow link into the repository: shell/.local/libexec/desktop/profiles.py.
REPO = Path(__file__).resolve().parents[4]
# The installer's modules, the same ones install-desktop.py and the guided installer run.
sys.path.insert(0, str(REPO / 'scripts/install'))
import install_paths  # noqa: E402
import install_plan  # noqa: E402
import install_undo  # noqa: E402
import install_removal  # noqa: E402


def installer_screens():
    # install-tui.py, which loads install-desktop.py: the same state its profiles screen shows.
    spec = importlib.util.spec_from_file_location('install_tui', REPO / 'scripts/install-tui.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(tui, statuses, name, recorded, defaults):
    status = statuses[name]
    return {'name': name, 'installed': tui.unit_installed(statuses, name), 'done': status.total - len(status.missing),
            'total': status.total, 'recorded': name in recorded, 'default': name in defaults}


def listing():
    try:
        tui = installer_screens()
        # Quiet: the installer prints warnings, and exits on a distribution it does not support.
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            plan = install_plan.load_plan(('core',))
            plan.distro.remember_answers()
            recorded = tui.recorded_profiles()
            defaults = install_plan.default_profiles(plan.table).split(',')
            units = install_plan.units(plan.table)
            statuses = {name: tui.profile_status(plan, name) for name in units}
            rows = []
            for name in install_paths.PROFILES:
                parts = [row(tui, statuses, part, recorded, defaults) | {'part': part.split('.', 1)[1],
                                                                         'default': part in install_plan.default_parts(name, plan.table)}
                         for part in units if install_plan.parent(part) == name and part != name]
                rows.append(row(tui, statuses, name, recorded, defaults) | {'parts': parts})
    except SystemExit as stop:
        return {'profiles': [], 'error': str(stop.code or '')}
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        return {'profiles': [], 'error': str(error)}
    return {'profiles': rows, 'error': ''}


def checked(text):
    # Units of the manifest, comma-separated; "-" or nothing is none.
    names = [name for name in text.split(',') if name and name != '-']
    if not all(re.fullmatch(r'[a-z0-9][a-z0-9.-]*', name) for name in names) or set(names) - set(install_plan.manifest_units()):
        raise ValueError(tr('settings.profiles.errors.name', [text]))
    return names


def present_units(tui):
    # Units all there on this system without a record of them (Herdr from its own installer, say): an install from
    # here keeps them, as the TUI starts them on, so the units file never leaves out what is installed.
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        plan = install_plan.load_plan(('core',))
        plan.distro.remember_answers()
        statuses = {name: tui.profile_status(plan, name) for name in install_plan.units(plan.table)}
    return {name for name in statuses if name != 'core' and tui.unit_installed(statuses, name)}


def install_arguments(tui, names):
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        recorded = tui.recorded_profiles()
    # A profile added here comes with its default parts.
    added = {part for name in names if name not in recorded for part in install_plan.default_parts(name)}
    return ['--profiles', ','.join(install_plan.normalized(set(recorded) | present_units(tui) | {'core'} | set(names) | added))]


def keep_arguments(tui, removing):
    # A removal keeps them too, and records them: without that, the units file it writes would leave out what is
    # installed but was never recorded (the AI block with a hand-installed Herdr).
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        recorded = set(tui.recorded_profiles())
    going = set(install_plan.with_parts(tuple(removing)))
    kept = sorted(present_units(tui) - recorded - going)
    return ['--keep', ','.join(kept)] if kept else []


def plan(action, first, second=''):
    tui = installer_screens()
    script = [sys.executable, str(REPO / 'scripts/install-desktop.py')]
    if action == 'change':
        add, remove = checked(first), checked(second)
        if not add and not remove or remove and not install_removal.removable_profiles(tuple(remove)):
            raise ValueError(tr('settings.profiles.errors.name', [f'{first} {second}']))
        runner = [sys.executable, str(Path(__file__).resolve()), 'run']
        arguments = [','.join(add) or '-', ','.join(remove) or '-']
        preview, apply = runner + ['dry-run', *arguments], runner + ['apply', *arguments]
    else:
        names = checked(first)
        if not names:
            raise ValueError(tr('settings.profiles.errors.name', [first]))
        if action == 'install':
            arguments = install_arguments(tui, names)
            remove = []
        else:
            if not install_removal.removable_profiles(tuple(names)):
                raise ValueError(tr('settings.profiles.errors.name', [first]))
            arguments, remove = ['--remove', ','.join(names), *keep_arguments(tui, names)], names
        preview, apply = script + ['dry-run', *arguments], script + ['apply', *arguments]
    # The running Hyprland has the plugins loaded: the installer refuses, and so does this, before the prompt.
    blocked = tr('settings.profiles.pluginsInSession') if 'plugins' in remove and install_undo.hyprland_running() else ''
    return {'preview': preview, 'apply': apply, 'blocked': blocked}


def run(mode, first, second):
    """A change: the installer adds, then removes. Its status is the first that failed."""
    tui = installer_screens()
    add, remove = checked(first), checked(second)
    script = [sys.executable, str(REPO / 'scripts/install-desktop.py'), mode]
    status = 0
    if add:
        status = subprocess.run(script + install_arguments(tui, add)).returncode
    if remove and status == 0:
        status = subprocess.run(script + ['--remove', ','.join(remove), *keep_arguments(tui, remove)]).returncode
    return status


def main(arguments):
    if arguments == ['list']:
        print(json.dumps(listing(), ensure_ascii=False))
    elif len(arguments) == 3 and arguments[0] == 'plan' and arguments[1] in ('install', 'remove'):
        print(json.dumps(plan(arguments[1], arguments[2])))
    elif len(arguments) == 4 and arguments[0] == 'plan' and arguments[1] == 'change':
        print(json.dumps(plan('change', arguments[2], arguments[3])))
    elif len(arguments) == 4 and arguments[0] == 'run' and arguments[1] in ('dry-run', 'apply'):
        return run(*arguments[1:])
    else:
        raise ValueError(__doc__)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

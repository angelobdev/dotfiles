"""Running a set of steps (run_steps) and what is said around a run: the checks before it, the notes for the
review, and what to do afterwards (log out, reboot, or the first login that finishes it)."""
import getpass
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

import install_paths
import install_plan
import install_record
import install_removal
import install_steps
import install_undo


# The titles of the steps the last run_steps applied: what they need afterwards (restart_needed).
APPLIED = []


def refuse(plan):
    if platform.machine() != 'x86_64':
        sys.exit(f'{platform.machine()} is not verified: the desktop is tested on x86_64.')
    if not install_plan.member(getpass.getuser(), plan.distro.ADMIN_GROUP):
        sys.exit(f'{getpass.getuser()} must be in the {plan.distro.ADMIN_GROUP} group to install packages.')


def preflight_warnings(plan):
    warnings = []
    free = shutil.disk_usage('/').free
    if free < install_paths.MIN_FREE:
        source = install_plan.query('findmnt', '-no', 'SOURCE', '/').stdout.strip()
        grow = f' Grow it with: sudo lvextend -r -l +100%FREE {source}' if source.startswith('/dev/mapper/') else ''
        warnings.append(f'Only {free // 2**30} GiB free on /.{grow}')
    if install_plan.merged(plan, 'auth') and plan.distro.auth_base() not in ('local', plan.distro.AUTH_PROFILE):
        warnings.append(f'The auth step expects the local authselect profile, found "{plan.distro.auth_base()}".')
    for item in install_steps.firmware_needed(plan):
        if not install_steps.firmware_source(plan, item):
            where = f'{plan.firmware} has no copy of it' if plan.firmware else 'pass --firmware <directory with a copy>'
            warnings.append(f'{item["purpose"]} needs {Path(item["target"]).name} ({item["source"]}): {where}.')
    for path in install_steps.clones_kept(plan):
        warnings.append(f'~/{path} is there already and is not a clone without local changes: it is left alone.')
    for name in install_steps.archives_unsupported(plan):
        warnings.append(f'{name} has no build for {platform.machine()}: it is left out.')
    return warnings


def preflight(plan):
    refuse(plan)
    for warning in preflight_warnings(plan):
        print('Warning: ' + warning)


def run_steps(plan, preview, steps=install_steps.STEPS):
    done = 0
    APPLIED.clear()
    # Install steps, all of them or some (the guided installer's Updates screen runs only the pins it moves):
    # either way an unreadable record is set aside and a missing one rebuilt before anything is remembered,
    # or the next uninstall would trust a record that knows only what this run added.
    installing = all(step in install_steps.STEPS for step in steps)
    record = None if preview else install_record.load_record(set_aside=installing)
    if record and record.get('uninstalled'):
        record = {}  # A new install after an uninstall starts its own record.
    if record is not None and installing:
        if not install_record.knows_changes(record) and install_undo.desktop_present():
            # Installed before there was a record: what came then is told by the history, or uninstall would miss it.
            record = {**install_undo.reconstruct(plan), **record}
        # Only a whole install says the profiles are installed.
        if tuple(steps) == install_steps.STEPS:
            install_record.keep(record, 'profiles', plan.profiles)
        install_record.save_record(record)
    for step in steps:
        items = step.pending(plan)
        if not items:
            continue
        done += 1
        print(f'{step.title}: {len(items)} to do')
        # Flushed: what runs next writes straight to the terminal or the log.
        print('\n'.join('  ' + item for item in items), flush=True)
        if not preview:
            # Saved before the change: a step that stops halfway is still undone by uninstall.
            if step.remember:
                step.remember(plan, items, record)
                install_record.save_record(record)
            step.apply(plan, items)
            APPLIED.append(step.title)
    return done


def refuse_uninstall():
    # Also for the plugins profile alone: its builds are loaded in the running Hyprland.
    if install_undo.hyprland_running():
        sys.exit('Hyprland is running: uninstalling removes the configuration it runs on (or, for the plugins profile, '
                 'the plugins it has loaded). Log out, switch to a console (Ctrl+Alt+F3), sign in there and run this again.')


def after_uninstall(plan, done):
    if not done:
        print('Nothing to do.')
        return
    print('Done. Not undone: the system upgrade, and what you changed by hand.')
    print(f'Left in place: your preferences in ~/.config/desktop, and this repository ({install_paths.REPO}).')


def recording_notes(plan):
    # The units an install adds to the record: one already on the system (installed by hand) changes nothing else.
    record = install_record.load_record()
    recorded = install_removal.recorded_profiles(record)
    new = [name for name in plan.profiles if recorded and name not in recorded]
    return [f'{install_paths.RECORD} names {", ".join(new)} from now on.'] if new else []


def record_notes(plan):
    # What an uninstall without a record cannot know, said before it starts.
    notes = []
    if plan.record.get('reconstructed'):
        notes.append('The desktop was installed before there was an install record: what came then is read from the manifest '
                     'and the package history, and units apply turned off then (such as sshd.service) stay off.')
    if plan.record.get('base_unknown'):
        notes.append('The package history does not show how the system was installed: no package from before the record is removed.')
    every = install_undo.every_profile(plan)
    for path in install_undo.changed_files(plan)[1]:
        notes.append(f'{path} changed since the install: it stays as it is.')
    for path in install_undo.clones_undoable(plan)[1]:
        notes.append(f'~/{path} changed since the install: it stays as it is.')
    shell = plan.record.get('login_shell')
    if shell and install_steps.login_shell() not in (shell, install_plan.setting(every, 'login_shell')):
        notes.append(f'The login shell is now {install_steps.login_shell()}, chosen after the install: it stays.')
    zone = plan.record.get('firewall_zone')
    if zone and install_plan.booted() and shutil.which('firewall-cmd') and install_record.default_zone_now() not in (zone, install_plan.setting(every, 'firewall_zone')):
        notes.append(f'The firewall zone is now {install_record.default_zone_now()}, chosen after the install: it stays.')
    for name, packages in install_undo.repos_in_use(plan, install_undo.recorded_repos(plan)).items():
        shown = ', '.join(packages[:3]) + (f' and {len(packages) - 3} more' if len(packages) > 3 else '')
        notes.append(f'The {name} repository stays: it still provides {shown}.')
    return notes


def next_steps(plan, done):
    if not done:
        print('Nothing to do.')
    elif 'plugins' in plan.profiles and not install_paths.STAMP.exists():
        print('Reboot and sign in. A terminal opens and builds the plugins; if it does not, press Super + Return and run:')
        print(f'  {install_paths.REPO / "scripts/install-desktop.py"} post --profiles {",".join(plan.profiles)}')
    elif install_undo.hyprland_running():
        # Inside the desktop: only what the applied steps need.
        print({'reboot': 'Done. Reboot: the new firmware loads at the next boot.',
               'login': 'Done. Log out and back in: new groups and the login shell come with the next login.'}.get(restart_needed(), 'Done.'))
    else:
        print('Done. Reboot to reach the login screen.')


def restart_needed():
    """What the steps the last run applied need inside a running desktop: 'reboot', 'login' or None."""
    if {'firmware', 'boot'} & set(APPLIED):
        return 'reboot'
    if {'groups', 'shell'} & set(APPLIED):
        return 'login'
    return None


def post(plan):
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        sys.exit('Run post from a terminal inside Hyprland.')
    if not sys.stdin.isatty():
        sys.exit('Run post from a terminal: hyprpm asks for confirmation.')
    if 'plugins' in plan.profiles:
        subprocess.run((str(install_paths.REPO / 'scripts/install-hypr-plugins.py'),), check=True)
    errors = subprocess.check_output(('hyprctl', 'configerrors'), text=True).strip()
    if errors:
        sys.exit(errors)
    subprocess.run((str(Path.home() / '.local/bin/desktop-shell'), 'status'), stdout=subprocess.DEVNULL, check=True)
    install_paths.AUTOSTART.unlink(missing_ok=True)
    print('The desktop is ready. Still to do by hand:')
    for note in install_plan.merged(plan, 'notes'):
        print('  ' + note)

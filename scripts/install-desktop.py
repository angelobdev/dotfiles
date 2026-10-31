#!/usr/bin/env python3
"""Turn an installed distribution into this desktop: dry-run shows the work, apply does it, post ends it after login."""
from argparse import ArgumentParser
from collections import namedtuple
import getpass
import grp
import importlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tomllib

REPO = Path(__file__).resolve().parent.parent
INSTALL = REPO / 'scripts/install'
PROFILES = ('core', 'hardware', 'plugins', 'apps')
DEFAULT_PROFILES = 'core,hardware,plugins'
MIN_FREE = 30 * 2**30
SESSION = 'hyprland-uwsm'
FLATHUB = 'https://dl.flathub.org/repo/flathub.flatpakrepo'
# The Steam and assistant launchers name this home.
EXPECTED_HOME = Path('/home/angelo')
AUTOSTART = Path.home() / '.config/autostart/desktop-finish-install.desktop'
STAMP = Path.home() / '.local/state/dotfiles/hypr-plugins.json'
ACCOUNTS = 'org.freedesktop.Accounts'

BOOT_SESSION = 'default session ' + SESSION
BOOT_GDM = 'enable gdm.service'
BOOT_TARGET = 'boot into graphical.target'
BOOT_AUTOSTART = 'finish the plugins at the first login'

Plan = namedtuple('Plan', 'distro release table commands profiles')
Step = namedtuple('Step', 'title pending apply')
sys.dont_write_bytecode = True


def query(*command):
    # A tool that is not installed yet is an empty answer: the preview runs before the packages.
    try:
        return subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        return subprocess.CompletedProcess(command, 127, '', '')


def merged(plan, key):
    items = []
    for profile in plan.profiles:
        items += [item for item in plan.table[profile].get(key, ()) if item not in items]
    return items


def setting(plan, key):
    return next((plan.table[profile][key] for profile in plan.profiles if key in plan.table[profile]), None)


# Calls that need systemd, D-Bus or a daemon running; a container has none and skips them.
def booted():
    return Path('/run/systemd/system').is_dir()


def member(user, group):
    try:
        return user in grp.getgrnam(group).gr_mem
    except KeyError:
        return False


def unit_state(unit):
    return query('systemctl', 'is-enabled', unit).stdout.strip()


def user_object():
    reply = query('busctl', 'call', ACCOUNTS, '/org/freedesktop/Accounts', ACCOUNTS, 'FindUserByName', 's', getpass.getuser())
    parts = reply.stdout.split('"')
    return parts[1] if len(parts) > 1 else ''


def session():
    path = user_object()
    return query('busctl', 'get-property', ACCOUNTS, path, ACCOUNTS + '.User', 'Session').stdout if path else ''


def repos_pending(plan):
    return [name for name in merged(plan, 'repos') if plan.distro.repo_missing(plan.table['repos'][name])]


def repos_apply(plan, names):
    for name in names:
        plan.distro.add_repo(plan.table['repos'][name], plan.release)


def upgrade_pending(plan):
    return ['installed packages'] if plan.distro.upgrades_pending() else []


def upgrade_apply(plan, items):
    plan.distro.upgrade()


def packages_pending(plan):
    return plan.distro.missing(merged(plan, 'packages'))


def packages_apply(plan, packages):
    plan.distro.install(packages)


def files_pending(plan):
    return [item['path'] for item in merged(plan, 'files') if plan.distro.file_differs(item['path'], item['content'].lstrip())]


def files_apply(plan, paths):
    for item in merged(plan, 'files'):
        if item['path'] in paths:
            plan.distro.write_file(item['path'], item['content'].lstrip())


def groups_pending(plan):
    return [group for group in merged(plan, 'groups') if not member(getpass.getuser(), group)]


def groups_apply(plan, groups):
    for group in groups:
        plan.distro.sudo('usermod', '-aG', group, getpass.getuser())


def services_pending(plan):
    enable = [unit for unit in merged(plan, 'services') if unit_state(unit) not in ('enabled', 'static', 'alias')]
    disable = [unit for unit in merged(plan, 'disable') if unit_state(unit) == 'enabled']
    # For every user: a Workstation preset turns these on, and an edition without a desktop leaves them off.
    users = [unit for unit in merged(plan, 'user_services') if query('systemctl', '--global', 'is-enabled', unit).stdout.strip() != 'enabled']
    return ['enable ' + unit for unit in enable] + ['disable ' + unit for unit in disable] + ['enable --global ' + unit for unit in users]


def services_apply(plan, items):
    # Never --now: stopping sshd or the network here could cut the session running this script.
    for item in items:
        plan.distro.sudo('systemctl', *item.split())


def firewall_pending(plan):
    zone = setting(plan, 'firewall_zone')
    if not zone or not booted() or not shutil.which('firewall-cmd'):
        return []
    return [] if query('firewall-cmd', '--get-default-zone').stdout.strip() == zone else [zone]


def firewall_apply(plan, zones):
    plan.distro.sudo('firewall-cmd', '--set-default-zone=' + zones[0])


def auth_pending(plan):
    return plan.distro.auth_pending() if setting(plan, 'auth') else []


def auth_apply(plan, items):
    plan.distro.auth_apply(items, REPO / 'scripts/tablet-auth.sh')


def stow_pending(plan):
    if not shutil.which('stow'):
        return ['every package: GNU Stow is not installed yet']
    result = query(str(REPO / 'scripts/stow.py'), 'dry-run')
    if result.returncode:
        raise RuntimeError('stow.py dry-run failed: ' + (result.stderr or result.stdout).strip()[-300:])
    lines = (result.stdout + result.stderr).splitlines()
    return [line for line in lines if line.startswith(('LINK:', 'MKDIR:', 'Will back up'))]


def stow_apply(plan, items):
    # Never with sudo: the links belong to the desktop user.
    subprocess.run((str(REPO / 'scripts/stow.py'), 'apply'), check=True)


def flatpak_pending(plan):
    apps = merged(plan, 'flatpaks')
    if not apps or not booted():
        return []
    present = query('flatpak', 'list', '--app', '--columns=application').stdout.split() if shutil.which('flatpak') else []
    return [app for app in apps if app not in present]


def flatpak_apply(plan, apps):
    plan.distro.sudo('flatpak', 'remote-add', '--if-not-exists', 'flathub', FLATHUB)
    plan.distro.sudo('flatpak', 'install', '-y', '--noninteractive', 'flathub', *apps)


def plugin_guard():
    # Early warning: post would refuse this Hyprland build, after a reboot.
    sys.path.insert(0, str(REPO / 'scripts/hyprpm'))
    from build import fingerprint
    try:
        fingerprint()
    except RuntimeError as error:
        print(f'Warning: {error}')


def verify_pending(plan):
    if 'plugins' in plan.profiles and not plan.distro.missing(['hyprland', 'hyprland-devel']):
        plugin_guard()
    return ['command not found: ' + command for command in plan.commands if not shutil.which(command)]


def verify_apply(plan, problems):
    raise RuntimeError('The desktop is incomplete, so the system keeps booting to the console.')


def boot_pending(plan):
    items = []
    if booted() and SESSION not in session():
        items.append(BOOT_SESSION)
    if unit_state('gdm.service') != 'enabled':
        items.append(BOOT_GDM)
    if query('systemctl', 'get-default').stdout.strip() != 'graphical.target':
        items.append(BOOT_TARGET)
    if 'plugins' in plan.profiles and not STAMP.exists() and not AUTOSTART.exists():
        items.append(BOOT_AUTOSTART)
    return items


def autostart_entry(plan):
    profiles = ','.join(plan.profiles)
    return ('[Desktop Entry]\nType=Application\nName=Finish the desktop installation\n'
            f'Exec=kitty --hold {REPO / "scripts/install-desktop.py"} post --profiles {profiles}\n')


def boot_apply(plan, items):
    if BOOT_SESSION in items:
        plan.distro.sudo('busctl', 'call', ACCOUNTS, user_object(), ACCOUNTS + '.User', 'SetSession', 's', SESSION)
    if BOOT_GDM in items:
        plan.distro.sudo('systemctl', 'enable', 'gdm.service')
    if BOOT_TARGET in items:
        plan.distro.sudo('systemctl', 'set-default', 'graphical.target')
    if BOOT_AUTOSTART in items:
        AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
        AUTOSTART.write_text(autostart_entry(plan), encoding='utf-8')


# In order. boot stays last: a run that stops earlier leaves a system that still starts on the console.
STEPS = (
    Step('repos', repos_pending, repos_apply),
    Step('upgrade', upgrade_pending, upgrade_apply),
    Step('packages', packages_pending, packages_apply),
    Step('files', files_pending, files_apply),
    Step('groups', groups_pending, groups_apply),
    Step('services', services_pending, services_apply),
    Step('firewall', firewall_pending, firewall_apply),
    Step('auth', auth_pending, auth_apply),
    Step('stow', stow_pending, stow_apply),
    Step('flatpak', flatpak_pending, flatpak_apply),
    Step('verify', verify_pending, verify_apply),
    Step('boot', boot_pending, boot_apply),
)


def os_release(path=Path('/etc/os-release')):
    fields = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        key, separator, value = line.partition('=')
        if separator:
            fields[key] = value.strip('"\'')
    return fields


def load_plan(profiles, release=None):
    manifest = tomllib.loads((INSTALL / 'manifest.toml').read_text(encoding='utf-8'))
    release = release or os_release()
    name, version = release.get('ID', ''), release.get('VERSION_ID', '')
    table = manifest.get(name)
    if name == 'verify' or table is None:
        sys.exit(f'{name or "This distribution"} is not verified yet: see docs/guide/installation.md.')
    if version not in table['versions']:
        sys.exit(f'{name} {version} is not verified: supported versions are {", ".join(table["versions"])}.')
    sys.path.insert(0, str(INSTALL))
    return Plan(importlib.import_module(name), version, table, manifest['verify']['commands'], profiles)


def preflight(plan):
    if platform.machine() != 'x86_64':
        sys.exit(f'{platform.machine()} is not verified: the desktop is tested on x86_64.')
    if not member(getpass.getuser(), plan.distro.ADMIN_GROUP):
        sys.exit(f'{getpass.getuser()} must be in the {plan.distro.ADMIN_GROUP} group to install packages.')
    warnings = []
    free = shutil.disk_usage('/').free
    if free < MIN_FREE:
        source = query('findmnt', '-no', 'SOURCE', '/').stdout.strip()
        grow = f' Grow it with: sudo lvextend -r -l +100%FREE {source}' if source.startswith('/dev/mapper/') else ''
        warnings.append(f'Only {free // 2**30} GiB free on /.{grow}')
    if Path.home() != EXPECTED_HOME:
        warnings.append(f'The desktop-ai and steam launchers name {EXPECTED_HOME}: edit them for {Path.home()}.')
    if setting(plan, 'auth') and plan.distro.auth_base() not in ('local', plan.distro.AUTH_PROFILE):
        warnings.append(f'The auth step expects the local authselect profile, found "{plan.distro.auth_base()}".')
    for warning in warnings:
        print('Warning: ' + warning)


def run_steps(plan, preview):
    done = 0
    for step in STEPS:
        items = step.pending(plan)
        if not items:
            continue
        done += 1
        print(f'{step.title}: {len(items)} to do')
        # Flushed: what runs next writes straight to the terminal or the log.
        print('\n'.join('  ' + item for item in items), flush=True)
        if not preview:
            step.apply(plan, items)
    return done


def next_steps(plan, done):
    if not done:
        print('Nothing to do.')
    elif 'plugins' in plan.profiles and not STAMP.exists():
        print('Reboot and sign in. A terminal opens and builds the plugins; if it does not, press Super + Return and run:')
        print(f'  {REPO / "scripts/install-desktop.py"} post --profiles {",".join(plan.profiles)}')
    else:
        print('Done. Reboot to reach the login screen.')


def post(plan):
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        sys.exit('Run post from a terminal inside Hyprland.')
    if not sys.stdin.isatty():
        sys.exit('Run post from a terminal: hyprpm asks for confirmation.')
    if 'plugins' in plan.profiles:
        subprocess.run((str(REPO / 'scripts/install-hypr-plugins.py'),), check=True)
    errors = subprocess.check_output(('hyprctl', 'configerrors'), text=True).strip()
    if errors:
        sys.exit(errors)
    subprocess.run((str(Path.home() / '.local/bin/desktop-shell'), 'status'), stdout=subprocess.DEVNULL, check=True)
    AUTOSTART.unlink(missing_ok=True)
    print('The desktop is ready. Still to do by hand:')
    for note in merged(plan, 'notes'):
        print('  ' + note)


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', choices=('dry-run', 'apply', 'post'), default='dry-run')
    parser.add_argument('--profiles', default=DEFAULT_PROFILES, help=f'comma separated, from {", ".join(PROFILES)} (default: {DEFAULT_PROFILES})')
    args = parser.parse_args(argv)
    profiles = tuple(args.profiles.split(','))
    if 'core' not in profiles or set(profiles) - set(PROFILES):
        parser.error(f'--profiles needs core, and takes only {", ".join(PROFILES)}.')
    if os.geteuid() == 0:
        sys.exit('Run as the desktop user: the script asks sudo for each system change.')
    plan = load_plan(profiles)
    preflight(plan)
    if args.action == 'post':
        post(plan)
        return 0
    done = run_steps(plan, args.action == 'dry-run')
    if args.action == 'apply':
        next_steps(plan, done)
    elif not done:
        print('Nothing to do.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (subprocess.CalledProcessError, RuntimeError, OSError) as error:
        sys.exit(str(error))

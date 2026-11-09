#!/usr/bin/env python3
"""Turn an installed distribution into this desktop, or back: dry-run shows the work, apply does it, post ends it after login."""
from argparse import ArgumentParser
import ast
from collections import namedtuple
import functools
import getpass
import grp
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import pwd
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import urllib.parse
import urllib.request

REPO = Path(__file__).resolve().parent.parent
INSTALL = REPO / 'scripts/install'
PROFILES = ('core', 'hardware', 'tablet', 'plugins', 'apps', 'utils', 'assistant', 'containers', 'radio', 'gaming')
# On a 2-in-1 (touch_hardware) tablet joins them, and each profile brings its default parts: default_profiles().
DEFAULT_PROFILES = 'core,hardware,plugins'
# Units: a profile, or a part of one as profile.part ([<distro>.<profile>.parts.<part>] in the manifest), which load_plan
# makes a table of its own, so that every step, the record and removal work by unit as they do by profile.
MANIFEST = REPO / 'scripts/install/manifest.toml'
# USB vendors whose devices there are fingerprint readers: Synaptics, Goodix, Validity, Egis, FPC, FocalTech; Elan's
# readers are its 0c.. products (its other USB devices are touchscreens).
FINGERPRINT_VENDORS = {'06cb', '27c6', '138a', '1c7a', '10a5', '2808'}
MIN_FREE = 30 * 2**30
SESSION = 'hyprland-uwsm'
FLATHUB = 'https://dl.flathub.org/repo/flathub.flatpakrepo'
AUTOSTART = Path.home() / '.config/autostart/desktop-finish-install.desktop'
STAMP = Path.home() / '.local/state/dotfiles/hypr-plugins.json'
ACCOUNTS = 'org.freedesktop.Accounts'
STATE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'dotfiles'
# What apply changed and what was there before, for uninstall: written before each step runs.
RECORD = STATE / 'install.json'
# The units the record names, one per line, for Lua and QML (save_units).
UNITS = STATE / 'units'
AUR = 'https://aur.archlinux.org/'

BOOT_SESSION = 'default session ' + SESSION
BOOT_GDM = 'enable gdm.service'
BOOT_TARGET = 'boot into graphical.target'
BOOT_AUTOSTART = 'finish the plugins at the first login'

# firmware: the directory --firmware names, searched for the blobs the manifest lists; None when not given.
# record: what an earlier apply changed (RECORD, or rebuilt from the package history), for uninstall.
Plan = namedtuple('Plan', 'distro release table commands profiles firmware record', defaults=(None, None))
# remember(plan, items, record) notes in the record what apply is about to change, and what was there before.
Step = namedtuple('Step', 'title pending apply remember', defaults=(None,))
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'scripts/hyprpm'))
import bundle  # noqa: E402


def query(*command):
    # A tool that is not installed yet is an empty answer: the preview runs before the packages.
    try:
        return subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        return subprocess.CompletedProcess(command, 127, '', '')


def parent(unit):
    return unit.split('.', 1)[0]


def flatten_parts(table):
    """A new table where each [<profile>.parts.<part>] is a table of its own, profile.part, right after its profile's.
    The manifest's own tables are left as they are."""
    flat = {}
    for name, section in table.items():
        if isinstance(section, dict) and isinstance(section.get('parts'), dict):
            flat[name] = {key: value for key, value in section.items() if key != 'parts'}
            flat.update({f'{name}.{part}': value for part, value in section['parts'].items()})
        else:
            flat[name] = section
    return flat


def units(table):
    """Every unit of a (flattened) table, in PROFILES order: each profile, then its parts."""
    names = []
    for profile in PROFILES:
        if profile in table:
            names += [profile] + [name for name in table if name.startswith(profile + '.')]
    return tuple(names)


@functools.lru_cache(maxsize=None)
def manifest_units():
    """The units of every distribution of the manifest, for what is checked before a plan is loaded."""
    manifest = tomllib.loads(MANIFEST.read_text(encoding='utf-8'))
    names = []
    for table in manifest.values():
        if isinstance(table, dict) and 'versions' in table:
            names += [name for name in units(flatten_parts(table)) if name not in names]
    return tuple(name for name in units({name: None for name in names}))


def normalized(names, known=None):
    """These units with the profile of each part, in the order of known (manifest_units())."""
    known = known or manifest_units()
    chosen = set(names) | {parent(name) for name in names}
    return tuple(name for name in known if name in chosen)


def with_parts(names, known=None):
    """These units, and every part of the profiles among them: what removing a profile takes."""
    known = known or manifest_units()
    return tuple(name for name in known if name in names or name != parent(name) and parent(name) in names)


def detect_intel(cpuinfo=Path('/proc/cpuinfo')):
    try:
        return 'GenuineIntel' in cpuinfo.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return False


def detect_camera(sysfs=Path('/sys')):
    # A V4L2 device, or an Intel IPU (PCI class 0x0480) whose cameras libcamera drives.
    if any((sysfs / 'class/video4linux').glob('*')):
        return True
    for device in (sysfs / 'bus/pci/devices').glob('*'):
        try:
            vendor, kind = (device / 'vendor').read_text().strip(), (device / 'class').read_text().strip()
        except OSError:
            continue
        if vendor == '0x8086' and kind.startswith('0x0480'):
            return True
    return False


def detect_fingerprint(sysfs=Path('/sys')):
    for device in (sysfs / 'bus/usb/devices').glob('*'):
        try:
            vendor, product = (device / 'idVendor').read_text().strip(), (device / 'idProduct').read_text().strip()
        except OSError:
            continue
        if vendor in FINGERPRINT_VENDORS or vendor == '04f3' and product.startswith('0c'):
            return True
    return False


# What a part's default may name instead of true or false: checked where the installer runs.
DETECT = {'intel': detect_intel, 'camera': detect_camera, 'fingerprint': detect_fingerprint}


def part_default(part):
    value = part.get('default', False) if isinstance(part, dict) else False
    return bool(DETECT[value]()) if isinstance(value, str) and value in DETECT else value is True


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


def swaps(plan):
    return [tuple(pair) for pair in merged(plan, 'swaps')]


def wanted_packages(plan):
    # A swapped package is replaced, never installed: its replacement takes its place.
    old = {pair[0] for pair in swaps(plan)}
    return [package for package in merged(plan, 'packages') + [pair[1] for pair in swaps(plan)] if package not in old]


def swaps_pending(plan):
    return [f'{old} -> {new}' for old, new in swaps(plan) if plan.distro.installed(old)]


def swaps_apply(plan, items):
    for old, new in swaps(plan):
        if f'{old} -> {new}' in items:
            plan.distro.swap(old, new)


def packages_pending(plan):
    missing = plan.distro.missing(list(dict.fromkeys(wanted_packages(plan))))
    compositor_guard(plan, missing)
    return missing


def compositor_guard(plan, missing):
    # The plugins accept only the Hyprland builds they were verified against, and dnf or pacman installs the newest
    # one the repository has: say so before installing, not at the first login. Once the repositories are there, so
    # the build is the one that will come (apply adds them before this step).
    wanted = [name for name in ('hyprland', 'hyprland-devel') if name in missing]
    if 'plugins' not in plan.profiles or not wanted or repos_pending(plan):
        return
    for name, build in sorted(plan.distro.candidates(wanted).items()):
        if build not in bundle.VERIFIED:
            print(f'Warning: {name} {build} is newer than the build the plugins were verified against '
                  f'({", ".join(bundle.VERIFIED)}): they will not be built at the first login until it is verified.')


def packages_apply(plan, packages):
    plan.distro.install(packages, merged(plan, 'exclude'))


def files_pending(plan):
    return [item['path'] for item in merged(plan, 'files') if plan.distro.file_differs(item['path'], item['content'].lstrip())]


def files_apply(plan, paths):
    for item in merged(plan, 'files'):
        if item['path'] in paths:
            plan.distro.write_file(item['path'], item['content'].lstrip(), item.get('mode', '0644'))


def groups_pending(plan):
    return [group for group in merged(plan, 'groups') if not member(getpass.getuser(), group)]


def groups_apply(plan, groups):
    for group in groups:
        plan.distro.sudo('usermod', '-aG', group, getpass.getuser())


def login_shell():
    return pwd.getpwnam(getpass.getuser()).pw_shell


def shell_pending(plan):
    shell = setting(plan, 'login_shell')
    return [shell] if shell and login_shell() != shell else []


def shell_apply(plan, shells):
    # usermod, not chsh: chsh is not on every edition, and it asks for the password again.
    plan.distro.sudo('usermod', '--shell', shells[0], getpass.getuser())


def clone_path(item):
    return Path.home() / item['path']


def clone_head(path):
    result = query('git', '-C', str(path), 'rev-parse', 'HEAD')
    return result.stdout.strip() if result.returncode == 0 else ''


def clone_clean(path):
    result = query('git', '-C', str(path), 'status', '--porcelain')
    return result.returncode == 0 and not result.stdout.strip()


# A folder the user has there already is updated only when it is a clone without local changes: never a plain
# folder or edited files (apply checks out with --force).
def clone_ours(path):
    return not path.exists() or path.is_dir() and not any(path.iterdir()) or (path / '.git').exists() and clone_clean(path)


def clones_pending(plan):
    return [item['path'] for item in merged(plan, 'clones')
            if clone_head(clone_path(item)) != item['commit'] and clone_ours(clone_path(item))]


def clones_kept(plan):
    return [item['path'] for item in merged(plan, 'clones')
            if clone_head(clone_path(item)) != item['commit'] and not clone_ours(clone_path(item))]


def checkout(path, repo, commit):
    # Only that commit, fetched into path (a clone, or a new one).
    if not (path / '.git').exists():
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(('git', '-C', str(path), 'init', '-q'), check=True)
    subprocess.run(('git', '-C', str(path), 'fetch', '-q', '--depth', '1', repo, commit), check=True)
    subprocess.run(('git', '-C', str(path), '-c', 'advice.detachedHead=false', 'checkout', '-q', '--force', commit), check=True)


def clones_apply(plan, paths):
    # As the desktop user, into the home: pinned commits of what the distribution does not package.
    for item in merged(plan, 'clones'):
        if item['path'] in paths:
            checkout(clone_path(item), item['repo'], item['commit'])


# Release archives: a tarball pinned by version and sha256 per architecture, unpacked into the home as the user, for
# programs that ship that way and then update themselves (herdr). Only one still missing installs: an update the
# program made itself is never taken back.
ARCHES = {'x86_64': 'x86_64', 'amd64': 'x86_64', 'aarch64': 'aarch64', 'arm64': 'aarch64'}


def machine():
    return ARCHES.get(platform.machine().lower(), '')


def archive_label(item):
    return f'{item["name"]} {item["version"]}'


def archive_paths(item):
    # What apply puts in the home: the unpacked files and folders, the links, the written files.
    return list(item['unpack'].values()) + list(item.get('links', {})) + list(item.get('entries', {}))


def archive_missing(item):
    return not any((Path.home() / path).exists() for path in item['unpack'].values())


def archives_pending(plan):
    return [archive_label(item) for item in merged(plan, 'archives') if machine() in item['sha256'] and archive_missing(item)]


def archives_unsupported(plan):
    return [item['name'] for item in merged(plan, 'archives') if machine() not in item['sha256']]


def open_url(url, timeout):
    # With a name of its own: releases.herdr.dev refuses urllib's default User-Agent (403).
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'install-desktop.py (dotfiles)'}), timeout=timeout)


def archive_url(item):
    return item['url'].format(version=item['version'], arch=machine())


def unpack_archive(item):
    home = Path.home()
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        tarball = folder / 'archive.tar.gz'
        with open_url(archive_url(item), 60) as response, tarball.open('wb') as out:
            shutil.copyfileobj(response, out)
        if sha256(tarball) != item['sha256'][machine()]:
            sys.exit(f'{archive_label(item)}: the download does not match its sha256 in the manifest.')
        with tarfile.open(tarball) as archive:
            archive.extractall(folder / 'unpacked', filter='data')
        for member, path in item['unpack'].items():
            # Next to its place first, then renamed into it: never half a program where it runs from.
            target = home / path
            staged = target.with_name(target.name + '.new')
            target.parent.mkdir(parents=True, exist_ok=True)
            if staged.is_dir():
                shutil.rmtree(staged)
            staged.unlink(missing_ok=True)
            shutil.move(folder / 'unpacked' / member, staged)
            staged.replace(target)
    # A link or file already there (a program of the same name, a launcher entry of its own) stays.
    for link, target in item.get('links', {}).items():
        path = home / link
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.unlink(missing_ok=True)
            path.symlink_to(home / target)
    for path, content in item.get('entries', {}).items():
        target = home / path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content.lstrip().replace('{home}', str(home)), encoding='utf-8')


def archives_apply(plan, items):
    for item in merged(plan, 'archives'):
        if archive_label(item) in items:
            unpack_archive(item)


# The AUR (Arch only): each PKGBUILD at the commit the manifest pins, built by makepkg in a cache of the user.
# The manifest also names the version that commit builds, so a preview needs no network.

def aur_cache():
    return Path.home() / '.cache/dotfiles/aur'


def aur_path(item):
    return aur_cache() / item['package']


def aur_pending(plan):
    # Missing, or another version than the pinned one: updating is a new pin (pins --update), then apply.
    items = []
    for item in merged(plan, 'aur'):
        now = plan.distro.version(item['package'])
        if now != item['version']:
            items.append(f'{item["package"]} {now} -> {item["version"]}' if now else f'{item["package"]} {item["version"]}')
    return items


def srcinfo_version(text):
    # The version a PKGBUILD builds, from its .SRCINFO, as pacman prints it: [EPOCH:]PKGVER-PKGREL.
    fields = {}
    for line in text.splitlines():
        key, separator, value = line.strip().partition(' = ')
        if separator and key in ('epoch', 'pkgver', 'pkgrel'):
            fields.setdefault(key, value)
    version = f'{fields.get("pkgver", "")}-{fields.get("pkgrel", "")}'
    return f'{fields["epoch"]}:{version}' if fields.get('epoch') else version


def import_key(url):
    # Which key may sign the sources is the PKGBUILD's validpgpkeys: this only gives makepkg's gpg a copy of it.
    with urllib.request.urlopen(url, timeout=60) as response:
        key = response.read()
    subprocess.run(('gpg', '--batch', '--quiet', '--import'), input=key, check=True)


def aur_apply(plan, items):
    # As the desktop user: makepkg refuses root, and asks sudo for pacman itself.
    names = {item.split()[0] for item in items}
    for item in merged(plan, 'aur'):
        if item['package'] not in names:
            continue
        path = aur_path(item)
        checkout(path, AUR + item['package'] + '.git', item['commit'])
        built = srcinfo_version((path / '.SRCINFO').read_text(encoding='utf-8'))
        if built != item['version']:
            raise RuntimeError(f'{item["package"]} at {item["commit"][:12]} builds {built}, '
                               f'not the {item["version"]} the manifest names: correct the manifest.')
        if item.get('key'):
            import_key(item['key'])
        plan.distro.build_package(path)
        # The PKGBUILD stays, for the next update; the sources and the built package go.
        subprocess.run(('git', '-C', str(path), 'clean', '-q', '-d', '-x', '--force'), check=True)


def dmi(field):
    try:
        return Path('/sys/class/dmi/id', field).read_text(encoding='utf-8').strip()
    except OSError:
        return ''


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as file:
        for block in iter(lambda: file.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def firmware_needed(plan):
    # Only for the model each blob belongs to, and only where it is missing or different.
    return [item for item in merged(plan, 'firmware') if dmi('product_name') == item['product']
            and not (Path(item['target']).is_file() and sha256(item['target']) == item['sha256'])]


def firmware_source(plan, item):
    # By hash, not by name: the vendor package names it differently from the kernel.
    if not plan.firmware:
        return None
    return found_firmware(str(Path(plan.firmware).expanduser()), item['size'], item['sha256'])


# Searched once per run (preflight, pending and apply each ask, the guided installer more often): the directory
# can be a whole backup disk. The guided installer forgets it at each new check.
@functools.lru_cache(maxsize=None)
def found_firmware(directory, size, digest):
    # The size check first: only files that can match get hashed.
    for path in sorted(Path(directory).rglob('*')):
        if path.is_file() and path.stat().st_size == size and sha256(path) == digest:
            return path
    return None


def firmware_pending(plan):
    return [item['target'] for item in firmware_needed(plan) if firmware_source(plan, item)]


def firmware_apply(plan, targets):
    for item in firmware_needed(plan):
        if item['target'] in targets:
            plan.distro.install_firmware(firmware_source(plan, item), item['target'])
    # The ISH loader runs from the initramfs, before the root file system: every kernel needs it there.
    plan.distro.rebuild_initramfs()


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


def stow_command(plan, action):
    extra = [argument for name in merged(plan, 'stow') for argument in ('--with', name)]
    return (str(REPO / 'scripts/stow.py'), action, *extra)


def stow_pending(plan):
    if not shutil.which('stow'):
        return ['every package: GNU Stow is not installed yet']
    result = query(*stow_command(plan, 'dry-run'))
    if result.returncode:
        raise RuntimeError('stow.py dry-run failed: ' + (result.stderr or result.stdout).strip()[-300:])
    lines = (result.stdout + result.stderr).splitlines()
    return [line for line in lines if line.startswith(('LINK:', 'MKDIR:', 'Will back up'))]


def stow_apply(plan, items):
    # Never with sudo: the links belong to the desktop user.
    subprocess.run(stow_command(plan, 'apply'), check=True)


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
    try:
        bundle.verify()
    except RuntimeError as error:
        print(f'Warning: {error}')


def verify_pending(plan):
    if 'plugins' in plan.profiles and not plan.distro.missing(list(dict.fromkeys(['hyprland', bundle.headers_package()]))):
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


# One Exec= argument, by the Desktop Entry rules: plain ones as they are; others quoted, with ", `, $ and \ escaped
# by a backslash that the string escaping doubles again, and % doubled (it starts a field code).
def exec_argument(text):
    if re.fullmatch(r'[A-Za-z0-9_./,:=+-]+', text):
        return text
    # The quoting rule first, then the string escaping, which doubles every backslash.
    quoted = ''.join('\\' + char if char in '"`$\\' else char for char in text).replace('\\', '\\\\')
    return '"' + quoted.replace('%', '%%') + '"'


def autostart_entry(plan):
    profiles = ','.join(plan.profiles)
    command = ['kitty', '--hold', str(REPO / 'scripts/install-desktop.py'), 'post', '--profiles', profiles]
    return ('[Desktop Entry]\nType=Application\nName=Finish the desktop installation\n'
            f'Exec={" ".join(exec_argument(part) for part in command)}\n')


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


# The record: for each step, what it is about to change and the value it replaces. The first value seen wins, so a
# second apply never mistakes its own work for what was there before.

def load_record(set_aside=False):
    # Missing: an empty record. Unreadable: empty too, said out loud, and moved aside before anything replaces it.
    # One from before the tablet profile gets it beside hardware, which held it then.
    try:
        record = json.loads(RECORD.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        record = None
    if isinstance(record, dict):
        return bundle.migrate(record)
    aside = RECORD.with_name(RECORD.name + '.unreadable')
    if set_aside:
        RECORD.replace(aside)
    print(f'Warning: {RECORD} cannot be read' + (f', moved to {aside.name}' if set_aside else '') +
          ': what the installer changed comes from the manifest and the package history instead.', file=sys.stderr)
    return {}


def knows_changes(record):
    # Only profiles: an apply that found nothing to do on an install made before there was a record.
    return bool(set(record) - {'profiles', 'profiles_version'})


def desktop_present():
    # Installed before: Stow links into this repository, or plugins already built.
    return bool(linked_files()) or STAMP.exists()


def save_record(record):
    if 'profiles' in record:
        record['profiles_version'] = bundle.PROFILES_VERSION
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    temporary = RECORD.with_name(RECORD.name + '.tmp')
    temporary.write_text(json.dumps(record, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(RECORD)
    save_units(record)


def save_units(record):
    """UNITS: the installed units, one per line, for what Hyprland (config/installed.lua) and the shell (Installed.qml)
    show only with their unit. Without a list of profiles (uninstalled, or none yet), no file: everything counts."""
    profiles = record.get('profiles')
    if not isinstance(profiles, list) or record.get('uninstalled'):
        UNITS.unlink(missing_ok=True)
        return
    temporary = UNITS.with_name(UNITS.name + '.tmp')
    temporary.write_text(''.join(f'{name}\n' for name in profiles if isinstance(name, str)), encoding='utf-8')
    temporary.replace(UNITS)


def keep(record, key, values):
    items = record.setdefault(key, [])
    items += [value for value in values if value not in items]


def current_session():
    # busctl prints 's "hyprland-uwsm"': the last quoted string.
    parts = session().split('"')
    return parts[-2] if len(parts) > 2 else ''


def default_target():
    return query('systemctl', 'get-default').stdout.strip()


def default_zone_now():
    return query('firewall-cmd', '--get-default-zone').stdout.strip()


def read_or_none(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        return None


def repos_remember(plan, items, record):
    keep(record, 'repos', items)


def swaps_remember(plan, items, record):
    keep(record, 'swaps', [[old, new] for old, new in swaps(plan) if f'{old} -> {new}' in items])


def packages_remember(plan, items, record):
    keep(record, 'packages', items)


def text_digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def files_remember(plan, items, record):
    # What apply is about to write, by digest: a later manifest change must not make it look edited by hand.
    written = record.setdefault('written', {})
    for item in merged(plan, 'files'):
        if item['path'] in items:
            written[item['path']] = text_digest(item['content'].lstrip())
    files = record.setdefault('files', {})
    for path in items:
        if path not in files:
            try:
                files[path] = read_or_none(path)
            except OSError:
                pass  # There but unreadable: uninstall leaves it alone.


def firmware_remember(plan, items, record):
    firmware = record.setdefault('firmware', {})
    for target in items:
        firmware.setdefault(target, Path(target).exists())


def groups_remember(plan, items, record):
    keep(record, 'groups', items)


def shell_remember(plan, items, record):
    record.setdefault('login_shell', login_shell())


def services_remember(plan, items, record):
    services = record.setdefault('services', {})
    for item in items:
        words = item.split()
        keep(services, 'global' if '--global' in words else words[0] + 'd', [words[-1]])


def firewall_remember(plan, items, record):
    record.setdefault('firewall_zone', default_zone_now())


def auth_remember(plan, items, record):
    keep(record, 'auth', items)


def stow_remember(plan, items, record):
    keep(record, 'stow', merged(plan, 'stow'))


def clones_remember(plan, items, record):
    # Only folders apply creates are undone; one that was there before stays the user's.
    keep(record, 'clones', [path for path in items if not (Path.home() / path).exists()])


def archives_remember(plan, items, record):
    # Only what apply creates; uninstall leaves what was there before.
    keep(record, 'archives', [path for item in merged(plan, 'archives') if archive_label(item) in items
                              for path in archive_paths(item) if not os.path.lexists(Path.home() / path)])


def aur_remember(plan, items, record):
    # With the other packages: uninstall removes them alike. One installed before, which apply updates, stays.
    keep(record, 'packages', [name for name in (item.split()[0] for item in items) if not plan.distro.installed(name)])


def flatpak_remember(plan, items, record):
    keep(record, 'flatpaks', items)


def boot_remember(plan, items, record):
    boot = record.setdefault('boot', {})
    if BOOT_SESSION in items:
        boot.setdefault('session', current_session())
    if BOOT_GDM in items:
        boot.setdefault('gdm', unit_state('gdm.service') or 'disabled')
    if BOOT_TARGET in items:
        boot.setdefault('target', default_target())


# In order. boot stays last: a run that stops earlier leaves a system that still starts on the console.
STEPS = (
    Step('repos', repos_pending, repos_apply, repos_remember),
    Step('upgrade', upgrade_pending, upgrade_apply),
    # Before packages: a package that needs the replacement would conflict with what it replaces.
    Step('swaps', swaps_pending, swaps_apply, swaps_remember),
    Step('packages', packages_pending, packages_apply, packages_remember),
    # After the packages: makepkg needs base-devel and git.
    Step('aur', aur_pending, aur_apply, aur_remember),
    Step('files', files_pending, files_apply, files_remember),
    Step('firmware', firmware_pending, firmware_apply, firmware_remember),
    Step('groups', groups_pending, groups_apply, groups_remember),
    Step('shell', shell_pending, shell_apply, shell_remember),
    Step('services', services_pending, services_apply, services_remember),
    Step('firewall', firewall_pending, firewall_apply, firewall_remember),
    Step('auth', auth_pending, auth_apply, auth_remember),
    Step('stow', stow_pending, stow_apply, stow_remember),
    Step('clones', clones_pending, clones_apply, clones_remember),
    Step('archives', archives_pending, archives_apply, archives_remember),
    Step('flatpak', flatpak_pending, flatpak_apply, flatpak_remember),
    Step('verify', verify_pending, verify_apply),
    Step('boot', boot_pending, boot_apply, boot_remember),
)


# Uninstall: the steps above backwards, from the record. Each one undoes only what is still the way apply left it.

def every_profile(plan):
    return plan._replace(profiles=units(plan.table))


def reconstruct(plan):
    # No record: an install made before there was one. Only what the manifest names and the package history shows
    # arrived after the system was installed; values from before that the system cannot tell are left alone.
    every = every_profile(plan)
    distro = plan.distro
    base = distro.base_packages(distro.history())
    # Without the transactions that installed the system, nobody can tell its packages from the desktop's: they stay.
    swapped = [[old, new] for old, new in swaps(every) if distro.installed(new) and not distro.installed(old)
               and any(name.rsplit('.', 1)[0] == old for name in base)]
    news = {new for _, new in swapped}
    aur = [item['package'] for item in merged(every, 'aur')]
    wanted = [package for package in dict.fromkeys(wanted_packages(every) + aur) if package not in news]
    packages = [name for name in distro.installed_names(wanted) if name not in base] if base else []
    record = {'reconstructed': True, 'packages': packages, 'swaps': swapped,
              'repos': [name for name in merged(every, 'repos') if not distro.repo_missing(every.table['repos'][name])],
              'files': {item['path']: None for item in merged(every, 'files')
                        if not distro.file_differs(item['path'], item['content'].lstrip()) and not distro.owned(item['path'])},
              'firmware': {item['target']: False for item in merged(every, 'firmware') if Path(item['target']).is_file()
                           and sha256(item['target']) == item['sha256'] and not distro.owned(item['target'])},
              'groups': [group for group in merged(every, 'groups') if member(getpass.getuser(), group)],
              'clones': [item['path'] for item in merged(every, 'clones') if (clone_path(item) / '.git').exists()],
              'stow': merged(every, 'stow'), 'auth': distro.auth_reconstruct(packages)}
    shell = setting(every, 'login_shell')
    if shell and login_shell() == shell:
        record['login_shell'] = '/bin/bash'
    zone = setting(every, 'firewall_zone')
    if zone and booted() and shutil.which('firewall-cmd') and default_zone_now() == zone != distro.default_zone():
        record['firewall_zone'] = distro.default_zone()
    if not base:
        record['base_unknown'] = True
    boot = record['boot'] = {}
    if booted() and current_session() == SESSION:
        boot['session'] = ''
    # The display manager came with the desktop: the system started on the console before it.
    if any(name.rsplit('.', 1)[0] == 'gdm' for name in packages):
        boot['gdm'] = 'disabled'
        if default_target() == 'graphical.target' != distro.BASE_TARGET:
            boot['target'] = distro.BASE_TARGET
    return record


def uninstall_plan(plan, preview=True):
    record = load_record(set_aside=not preview)
    return plan._replace(record=record if knows_changes(record) else reconstruct(plan))


def hyprland_running():
    return query('pgrep', '-u', str(os.getuid()), '-x', 'Hyprland').returncode == 0


def plugin_paths():
    home = Path.home()
    return [home / '.local/share/dotfiles/hyprpm', home / '.cache/dotfiles/hyprpm-build', home / '.local/bin/hyprcapture-ui',
            home / '.local/share/licenses/hyprcapture', bundle.STAMP]


def unplugins_pending(plan):
    repository = bundle.CACHE / bundle.REPOSITORY
    return ([str(repository)] if repository.exists() else []) + [str(path) for path in plugin_paths() if path.exists() or path.is_symlink()]


def unplugins_apply(plan, items):
    # Files only: no Hyprland runs, so nothing is unloaded. The cache goes whole unless it holds other repositories.
    if str(bundle.CACHE / bundle.REPOSITORY) in items:
        others = [path for path in bundle.CACHE.iterdir() if path.is_dir() and path.name not in ('headersRoot', bundle.REPOSITORY)]
        plan.distro.sudo('rm', '-rf', '--', str(bundle.CACHE / bundle.REPOSITORY) if others else str(bundle.CACHE))
    for path in plugin_paths():
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        elif path.exists() or path.is_symlink():
            path.unlink()


UNBOOT_AUTOSTART = 'remove the first-login autostart'


def unboot_pending(plan):
    boot, items = plan.record.get('boot', {}), []
    # Only what is still the way apply left it: a session or target chosen since then stays.
    if 'session' in boot and booted() and current_session() == SESSION != boot['session']:
        items.append('default session ' + (boot['session'] or 'chosen by GDM'))
    if boot.get('gdm', 'enabled') != 'enabled' and unit_state('gdm.service') == 'enabled':
        items.append('disable gdm.service')
    if 'target' in boot and default_target() == 'graphical.target' != boot['target']:
        items.append('boot into ' + boot['target'])
    if AUTOSTART.exists():
        items.append(UNBOOT_AUTOSTART)
    return items


def unboot_apply(plan, items):
    boot = plan.record.get('boot', {})
    if any(item.startswith('default session ') for item in items):
        plan.distro.sudo('busctl', 'call', ACCOUNTS, user_object(), ACCOUNTS + '.User', 'SetSession', 's', boot['session'])
    if 'disable gdm.service' in items:
        plan.distro.sudo('systemctl', 'disable', 'gdm.service')
    if any(item.startswith('boot into ') for item in items):
        plan.distro.sudo('systemctl', 'set-default', boot['target'])
    if UNBOOT_AUTOSTART in items:
        AUTOSTART.unlink(missing_ok=True)


# A recorded clone is removed only while it is what apply left: a folder the manifest names, at its commit, with no
# local changes. The record is a file in the home, so a path from it is never trusted on its own.
def clones_undoable(plan):
    named = {item['path']: item for item in merged(every_profile(plan), 'clones')}
    undoable, changed = [], []
    for path in plan.record.get('clones', ()):
        item = named.get(path)
        if not item or not (Path.home() / path).exists():
            continue
        target = clone_path(item)
        (undoable if clone_head(target) == item['commit'] and clone_clean(target) else changed).append(path)
    return undoable, changed


def unclones_pending(plan):
    return clones_undoable(plan)[0]


def unclones_apply(plan, paths):
    for path in paths:
        shutil.rmtree(Path.home() / path)


def unarchives_pending(plan):
    # What apply unpacked, as it is now: these programs update themselves, so a newer version goes too.
    return [path for path in plan.record.get('archives', ()) if os.path.lexists(Path.home() / path)]


def unarchives_apply(plan, paths):
    for path in paths:
        target = Path.home() / path
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)


def unaur_pending(plan):
    # The PKGBUILDs; the packages built from them go with the others.
    return [str(aur_cache())] if aur_cache().exists() else []


def unaur_apply(plan, items):
    shutil.rmtree(aur_cache())


def stow_packages():
    # The lists of stow.py, read without running it.
    values = {}
    for node in ast.parse((REPO / 'scripts/stow.py').read_text(encoding='utf-8')).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') in ('PACKAGES', 'OPTIONAL'):
            values[node.targets[0].id] = ast.literal_eval(node.value)
    return values['PACKAGES'] + values['OPTIONAL']


def linked_files():
    links = []
    for package in stow_packages():
        root = REPO / package
        for source in sorted(root.rglob('*')):
            target = Path.home() / source.relative_to(root)
            if source.is_file() and target.is_symlink() and target.resolve() == source.resolve():
                links.append(target)
    return links


def backups():
    # Files Stow moved aside, newest backup first: the latest copy of a file wins.
    root = STATE / 'backups'
    return [(folder, path) for folder in sorted(root.iterdir(), reverse=True) if folder.is_dir()
            for path in sorted(folder.rglob('*')) if path.is_file() or path.is_symlink()] if root.is_dir() else []


def unstow_pending(plan):
    items = []
    links = linked_files()
    if links:
        items.append(f'unlink {len(links)} files linked into {REPO}')
    # Put back where nothing is, or where a link of ours is that the unlinking removes first; the newest copy of
    # each file counts once.
    linked = set(links)
    restorable = {Path.home() / path.relative_to(folder) for folder, path in backups()}
    restorable = [target for target in restorable if target in linked or not (target.exists() or target.is_symlink())]
    if restorable:
        items.append(f'put back {len(restorable)} files Stow had moved to {STATE / "backups"}')
    return items


def unstow_apply(plan, items):
    if linked_files():
        # Never with sudo, as apply. stow.py --delete unlinks every package, the optional ones too.
        subprocess.run((str(REPO / 'scripts/stow.py'), 'remove'), check=True)
    for folder, path in backups():
        target = Path.home() / path.relative_to(folder)
        if not target.exists() and not target.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(target))


INTERFACE = STATE / 'interface-before-theme.ini'


def unsettings_pending(plan):
    return [f'GNOME interface settings saved in {INTERFACE.name}'] if INTERFACE.exists() and booted() else []


def unsettings_apply(plan, items):
    # Saved by theme.py before its first change: one "schema key value" per line, in GVariant text.
    environment = dict(os.environ)
    environment.setdefault('DBUS_SESSION_BUS_ADDRESS', f'unix:path=/run/user/{os.getuid()}/bus')
    for line in INTERFACE.read_text(encoding='utf-8').splitlines():
        schema, key, value = (line.split(' ', 2) + ['', ''])[:3]
        if schema and key:
            subprocess.run(('gsettings', 'set', schema, key, value), env=environment, check=False)
    INTERFACE.unlink()


def unflatpak_pending(plan):
    apps = plan.record.get('flatpaks', [])
    present = query('flatpak', 'list', '--app', '--columns=application').stdout.split() if apps and shutil.which('flatpak') else []
    return [app for app in apps if app in present]


def unflatpak_apply(plan, apps):
    plan.distro.sudo('flatpak', 'uninstall', '-y', '--noninteractive', *apps)


def unauth_pending(plan):
    # Before the packages: PAM would point at modules that are gone.
    recorded = plan.record.get('auth', [])
    return [item for item in recorded if item not in plan.distro.auth_pending()] if recorded else []


def unauth_apply(plan, items):
    plan.distro.auth_revert(items, REPO / 'scripts/tablet-auth.sh')


def unfirewall_pending(plan):
    zone = plan.record.get('firewall_zone')
    if not zone or not booted() or not shutil.which('firewall-cmd'):
        return []
    now = default_zone_now()
    return [] if now == zone or now != setting(every_profile(plan), 'firewall_zone') else [zone]


def unfirewall_apply(plan, zones):
    plan.distro.sudo('firewall-cmd', '--set-default-zone=' + zones[0])


def unservices_pending(plan):
    # Units apply turned off come back only with a record: without one, nobody knows they were ever on.
    services = plan.record.get('services', {})
    disable = [unit for unit in services.get('enabled', ()) if unit_state(unit) == 'enabled']
    enable = [unit for unit in services.get('disabled', ()) if unit_state(unit) == 'disabled']
    users = [unit for unit in services.get('global', ()) if query('systemctl', '--global', 'is-enabled', unit).stdout.strip() == 'enabled']
    return ['disable ' + unit for unit in disable] + ['enable ' + unit for unit in enable] + ['disable --global ' + unit for unit in users]


def unshell_pending(plan):
    # Before the packages: a login shell that is gone locks the user out. One chosen since the install stays.
    shell = plan.record.get('login_shell')
    if not shell or login_shell() == shell or login_shell() != setting(every_profile(plan), 'login_shell'):
        return []
    return [shell if Path(shell).exists() else '/bin/bash']


def ungroups_pending(plan):
    return [group for group in plan.record.get('groups', ()) if member(getpass.getuser(), group)]


def ungroups_apply(plan, groups):
    for group in groups:
        plan.distro.sudo('gpasswd', '-d', getpass.getuser(), group)


def written_files(plan):
    return {item['path']: item['content'].lstrip() for item in merged(every_profile(plan), 'files')}


def changed_files(plan):
    # Recorded files apply would undo, split by whether they still hold what apply wrote or were edited since.
    # What apply wrote is told by its digest in the record; records from before it compare with the manifest.
    written, digests, ours, edited = written_files(plan), plan.record.get('written', {}), [], []
    for path, before in plan.record.get('files', {}).items():
        try:
            now = read_or_none(path)
        except OSError:
            continue
        if now != before:
            mine = now is not None and (text_digest(now) == digests[path] if path in digests else now == written.get(path))
            (ours if mine else edited).append(path)
    return ours, edited


def unfiles_pending(plan):
    return changed_files(plan)[0]


def unfiles_apply(plan, paths):
    for path in paths:
        before = plan.record['files'][path]
        if before is None:
            plan.distro.sudo('rm', '-f', '--', path)
        else:
            plan.distro.write_file(path, before)


def unfirmware_pending(plan):
    # Only a blob still as apply put it: the manifest's file, by hash, that no package has taken over since.
    named = {item['target']: item for item in merged(every_profile(plan), 'firmware')}
    return [target for target, existed in plan.record.get('firmware', {}).items()
            if not existed and target in named and Path(target).is_file()
            and sha256(target) == named[target]['sha256'] and not plan.distro.owned(target)]


def unfirmware_apply(plan, targets):
    for target in targets:
        plan.distro.sudo('rm', '-f', '--', target)
    plan.distro.rebuild_initramfs()


def removal_split(plan):
    # What apply installed and is still there: swapped packages go back by swap, prerequisites stay. A package
    # someone installed by hand would go with them as a dependent: it stays, and so does everything of ours it needs.
    # Removing some profiles, the packages of those that stay count as installed by hand.
    news = {new for _, new in plan.record.get('swaps', ())}
    names = plan.distro.installed_names([package for package in plan.record.get('packages', ()) if package not in news])
    names = [name for name in names if name.rsplit('.', 1)[0] not in plan.distro.PROTECTED + tuple(news)]
    staying = set(plan.distro.installed_names(plan.record['staying'])) if plan.record.get('staying') else set()
    names = [name for name in names if name not in staying]
    kept = []
    for _ in range(5):  # Each round keeps more; dnf's answer settles in one or two.
        rows = plan.distro.removal(names)
        others = [row for row in rows if row not in names]
        theirs = plan.distro.installed_by_hand(others) | (staying & set(others))
        needed = plan.distro.requirements(sorted(theirs)) if theirs else set()
        if not needed & set(names):
            return names, kept, rows, theirs
        kept += [name for name in names if name in needed]
        names = [name for name in names if name not in needed]
    return names, kept, rows, theirs


def removed_names(plan):
    return removal_split(plan)[0]


def unpackages_pending(plan):
    # dnf's own answer: what depends on them goes too, and so do the dependencies nothing else needs. A package
    # installed by hand that still goes needs one of them in a way dnf did not tell: it is marked, for the review.
    names, kept, rows, theirs = removal_split(plan)
    marked = [row + ('  (installed by hand: it needs one of the others)' if row in theirs else '') for row in rows]
    # A package kept because one that stays (or one installed by hand) needs it is no work of its own: it is listed
    # only beside what goes, so an uninstall run again over what it had to keep has nothing to do.
    if plan.record.get('removing'):
        return marked + [f'keep {name}  (a package that stays needs it)' for name in kept] if rows else []
    return marked + [f'keep {name}  (a package installed by hand needs it)' for name in kept] if rows else []


def unpackages_apply(plan, items):
    plan.distro.remove(removed_names(plan))


def unswaps_pending(plan):
    return [f'{new} -> {old}' for old, new in plan.record.get('swaps', ()) if plan.distro.installed(new) and not plan.distro.installed(old)]


def unswaps_apply(plan, items):
    for old, new in plan.record.get('swaps', ()):
        if f'{new} -> {old}' in items:
            plan.distro.swap(new, old)


def repos_in_use(plan, names):
    # Of these repositories, the ones packages that stay still come from: removing them would stop their updates.
    sources = {name: plan.distro.packages_from(plan.table['repos'][name]) for name in names}
    if not any(sources.values()):
        return {}
    going = {row.rsplit('.', 1)[0] for row in plan.distro.removal(removed_names(plan))}
    going |= {new for old, new in plan.record.get('swaps', ()) if plan.distro.installed(new) and not plan.distro.installed(old)}
    staying = {name: sorted(package for package in packages if package.rsplit('.', 1)[0] not in going) for name, packages in sources.items()}
    return {name: packages for name, packages in staying.items() if packages}


def recorded_repos(plan):
    return [name for name in plan.record.get('repos', ()) if name in plan.table['repos'] and not plan.distro.repo_missing(plan.table['repos'][name])]


def unrepos_pending(plan):
    names = recorded_repos(plan)
    in_use = repos_in_use(plan, names)
    return [name for name in names if name not in in_use]


def unrepos_apply(plan, names):
    for name in names:
        plan.distro.remove_repo(plan.table['repos'][name])


# What uninstall left on purpose and is still there: packages something installed by hand needs, repositories
# that still provide packages. Kept in the record, so a later uninstall can finish once they are free.
def leftovers(plan):
    packages = [name for name in plan.record.get('packages', ()) if plan.distro.installed(name)]
    repos = recorded_repos(plan)
    return {key: value for key, value in (('packages', packages), ('repos', repos)) if value}


def unstate_pending(plan):
    if not plan.record.get('uninstalled'):
        return [f'mark {RECORD} as undone']
    left = leftovers(plan)
    current = {key: plan.record[key] for key in ('packages', 'repos') if plan.record.get(key)}
    return [] if left == current else [f'note in {RECORD} what is still left']


def unstate_apply(plan, items):
    # Kept, emptied of what is undone: a second uninstall finds only what was left, instead of rebuilding a record
    # from the history.
    save_record({'uninstalled': True, 'version': 1, **leftovers(plan)})


# In order: the plugins, the login and the links while their tools are installed; PAM and the login shell before
# the packages they point at; the packages before the swaps and repositories they came from; the record last.
UNSTEPS = (
    Step('plugins', unplugins_pending, unplugins_apply),
    Step('boot', unboot_pending, unboot_apply),
    Step('clones', unclones_pending, unclones_apply),
    Step('archives', unarchives_pending, unarchives_apply),
    Step('aur', unaur_pending, unaur_apply),
    Step('stow', unstow_pending, unstow_apply),
    Step('settings', unsettings_pending, unsettings_apply),
    Step('flatpak', unflatpak_pending, unflatpak_apply),
    Step('auth', unauth_pending, unauth_apply),
    Step('firewall', unfirewall_pending, unfirewall_apply),
    Step('services', unservices_pending, services_apply),
    Step('shell', unshell_pending, shell_apply),
    Step('groups', ungroups_pending, ungroups_apply),
    Step('files', unfiles_pending, unfiles_apply),
    Step('firmware', unfirmware_pending, unfirmware_apply),
    Step('packages', unpackages_pending, unpackages_apply),
    Step('swaps', unswaps_pending, unswaps_apply),
    Step('repos', unrepos_pending, unrepos_apply),
    Step('record', unstate_pending, unstate_apply),
)


# Removing some profiles: the steps above, on the part of the record that only those profiles name in the
# manifest. What a profile that stays wants stays (gcc of apps and gaming, the RPM Fusion repositories, the ffmpeg
# swap), and so do its packages when dnf would remove them as dependents. core is the desktop itself: removing it is
# the uninstall above.

def removable_profiles(profiles):
    return bool(profiles) and 'core' not in profiles and not set(profiles) - set(manifest_units())


def staying_profiles(record, removed):
    # The profiles the record says are installed, but those; without a record of them, every other profile, so that
    # nothing another one may need goes.
    recorded = record.get('profiles') if isinstance(record.get('profiles'), list) and not record.get('uninstalled') else None
    return tuple(name for name in manifest_units() if name not in removed and (recorded is None or name in recorded or name == 'core'))


def profile_record(plan, record, removed):
    """The part of record that only the removed profiles set up, as a record for the steps of PROFILE_UNSTEPS."""
    real = load_record()
    # Only profiles still installed by the record's account: one removed already has nothing left to undo, and what of
    # it stayed (a package core needs) is core's now.
    recorded = real.get('profiles') if isinstance(real.get('profiles'), list) and not real.get('uninstalled') else None
    undone = [name for name in units(plan.table) if name in removed and (recorded is None or name in recorded)]
    going = plan._replace(profiles=tuple(undone))
    staying = plan._replace(profiles=tuple(name for name in staying_profiles(real, removed) if name in plan.table))

    def only(key):
        kept = merged(staying, key)
        return [item for item in merged(going, key) if item not in kept]

    def aur(part):
        return [item['package'] for item in merged(part, 'aur')]
    wanted = set(wanted_packages(staying) + aur(staying))
    packages = set(wanted_packages(going) + aur(going)) - wanted
    swapped = [list(pair) for pair in swaps(going) if pair not in swaps(staying)]
    files = {item['path'] for item in only('files')}
    firmware = {item['target'] for item in only('firmware')}
    archives = {path for item in only('archives') for path in archive_paths(item)}
    clones = {item['path'] for item in only('clones')}
    services = record.get('services', {})
    narrowed = {
        'removing': [name for name in manifest_units() if name in removed], 'undone': undone, 'staying': sorted(wanted),
        'packages': [name for name in record.get('packages', ()) if name in packages],
        'swaps': [pair for pair in record.get('swaps', ()) if list(pair) in swapped],
        'repos': [name for name in record.get('repos', ()) if name in only('repos')],
        'files': {path: before for path, before in record.get('files', {}).items() if path in files},
        'written': {path: digest for path, digest in record.get('written', {}).items() if path in files},
        'firmware': {target: existed for target, existed in record.get('firmware', {}).items() if target in firmware},
        'groups': [group for group in record.get('groups', ()) if group in only('groups')],
        'services': {'enabled': [unit for unit in services.get('enabled', ()) if unit in only('services')],
                     'disabled': [unit for unit in services.get('disabled', ()) if unit in only('disable')],
                     'global': [unit for unit in services.get('global', ()) if unit in only('user_services')]},
        'flatpaks': [app for app in record.get('flatpaks', ()) if app in only('flatpaks')],
        'archives': [path for path in record.get('archives', ()) if path in archives],
        'clones': [path for path in record.get('clones', ()) if path in clones],
        'aur': only('aur'), 'stow': only('stow'),
    }
    for key in ('firewall_zone', 'login_shell'):
        if key in record and setting(going, key) and not setting(staying, key):
            narrowed[key] = record[key]
    if record.get('auth') and setting(going, 'auth') and not setting(staying, 'auth'):
        narrowed['auth'] = record['auth']
    if record.get('reconstructed'):
        narrowed['reconstructed'] = True
    return narrowed


def removal_plan(plan, removed, preview=True):
    whole = uninstall_plan(plan, preview)
    return plan._replace(record=profile_record(plan, whole.record, removed))


def removing_plugins(plan):
    return 'plugins' in plan.record.get('undone', ())


def unprofile_plugins_pending(plan):
    # Without the plugins profile the login check cannot read the headers' version, and nothing can rebuild them.
    return unplugins_pending(plan) if removing_plugins(plan) else []


def unprofile_aur_pending(plan):
    return [str(aur_path(item)) for item in plan.record.get('aur', ()) if aur_path(item).exists()]


def unprofile_aur_apply(plan, paths):
    for path in paths:
        shutil.rmtree(path)


def profile_links(plan):
    # The links of the profile's own Stow packages (steam-hidpi), and the files Stow moved aside for them.
    links, restorable = [], []
    for package in plan.record.get('stow', ()):
        root = REPO / package
        for source in sorted(root.rglob('*')) if root.is_dir() else ():
            target = Path.home() / source.relative_to(root)
            if source.is_file() and target.is_symlink() and target.resolve() == source.resolve():
                links.append(target)
        relative = {source.relative_to(root) for source in root.rglob('*')} if root.is_dir() else set()
        restorable += [(folder, path) for folder, path in backups() if path.relative_to(folder) in relative]
    return links, restorable


def unprofile_stow_pending(plan):
    links, restorable = profile_links(plan)
    return [f'unlink {link}' for link in links] + [f'put back {Path.home() / path.relative_to(folder)}' for folder, path in restorable
                                                     if not (Path.home() / path.relative_to(folder)).is_file()]


def unprofile_stow_apply(plan, items):
    links, restorable = profile_links(plan)
    for link in links:
        link.unlink()
    for folder, path in restorable:
        target = Path.home() / path.relative_to(folder)
        if not target.exists() and not target.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(target))


def unprofile_record_pending(plan):
    recorded = load_record().get('profiles')
    listed = [name for name in plan.record['removing'] if isinstance(recorded, list) and name in recorded]
    return [f'note in {RECORD} that {", ".join(listed)} ' + ('is' if len(listed) == 1 else 'are') + ' no longer installed'] if listed else []


def unprofile_record_apply(plan, items):
    # The record without the profiles, and without what is undone: a package installed again later by hand is the
    # user's, and the full uninstall leaves it. What stays (a package something needs, a repository in use) stays there.
    record = load_record()
    if not record or record.get('uninstalled'):
        return
    narrowed = plan.record
    if isinstance(record.get('profiles'), list):
        record['profiles'] = [name for name in record['profiles'] if name not in narrowed['removing']]
    gone = {
        'packages': plan.distro.missing(narrowed['packages']) if narrowed['packages'] else [],
        'swaps': [pair for pair in narrowed['swaps'] if not plan.distro.installed(pair[1])],
        'repos': [name for name in narrowed['repos'] if name not in recorded_repos(plan)],
        'groups': [group for group in narrowed['groups'] if not member(getpass.getuser(), group)],
        'flatpaks': [app for app in narrowed['flatpaks'] if app not in unflatpak_pending(plan)],
        'archives': [path for path in narrowed['archives'] if not os.path.lexists(Path.home() / path)],
        'clones': [path for path in narrowed['clones'] if not (Path.home() / path).exists()],
    }
    for key, values in gone.items():
        if key in record:
            record[key] = [value for value in record[key] if value not in values]
    ours = set(changed_files(plan)[0])
    for path in narrowed['files']:
        if path not in ours:
            record.get('files', {}).pop(path, None)
            record.get('written', {}).pop(path, None)
    for target in narrowed['firmware']:
        if target not in unfirmware_pending(plan):
            record.get('firmware', {}).pop(target, None)
    for kind, units in narrowed['services'].items():
        if kind in record.get('services', {}):
            record['services'][kind] = [unit for unit in record['services'][kind] if unit not in units]
    if 'firewall_zone' in narrowed and not unfirewall_pending(plan):
        record.pop('firewall_zone', None)
    if narrowed.get('auth') and not unauth_pending(plan):
        record.pop('auth', None)
    save_record(record)


# In the order of UNSTEPS; the boot, the clones of core, the GNOME settings and the login shell belong to core.
PROFILE_UNSTEPS = (
    Step('plugins', unprofile_plugins_pending, unplugins_apply),
    Step('clones', unclones_pending, unclones_apply),
    Step('archives', unarchives_pending, unarchives_apply),
    Step('aur', unprofile_aur_pending, unprofile_aur_apply),
    Step('stow', unprofile_stow_pending, unprofile_stow_apply),
    Step('flatpak', unflatpak_pending, unflatpak_apply),
    Step('auth', unauth_pending, unauth_apply),
    Step('firewall', unfirewall_pending, unfirewall_apply),
    Step('services', unservices_pending, services_apply),
    Step('groups', ungroups_pending, ungroups_apply),
    Step('files', unfiles_pending, unfiles_apply),
    Step('firmware', unfirmware_pending, unfirmware_apply),
    Step('packages', unpackages_pending, unpackages_apply),
    Step('swaps', unswaps_pending, unswaps_apply),
    Step('repos', unrepos_pending, unrepos_apply),
    Step('record', unprofile_record_pending, unprofile_record_apply),
)


def os_release(path=Path('/etc/os-release')):
    fields = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        key, separator, value = line.partition('=')
        if separator:
            fields[key] = value.strip('"\'')
    return fields


def load_plan(profiles, release=None, firmware=None, any_version=False):
    manifest = tomllib.loads((INSTALL / 'manifest.toml').read_text(encoding='utf-8'))
    release = release or os_release()
    # A rolling release has no version of its own (Arch's container image adds the date of the image).
    name = release.get('ID', '')
    version = 'rolling' if release.get('BUILD_ID') == 'rolling' else release.get('VERSION_ID', '')
    table = manifest.get(name)
    if name == 'verify' or table is None:
        sys.exit(f'{name or "This distribution"} is not verified yet: see docs/guide/installation.md.')
    if version not in table['versions']:
        if not any_version:
            sys.exit(f'{name} {version} is not verified: supported versions are {", ".join(table["versions"])}. '
                     'Removing the desktop still works: install-desktop.py dry-run --uninstall.')
        print(f'Note: {name} {version} is not verified; the uninstall reads the manifest of {table["versions"][-1]}.')
    sys.path.insert(0, str(INSTALL))
    table = flatten_parts(table)
    resolve_files(table)
    return Plan(importlib.import_module(name), version, table, manifest['verify']['commands'], profiles, firmware)


def resolve_files(table):
    # A file is written inline (content) or copied from this repository (source), with its mode (default 0644).
    for section in table.values():
        for item in section.get('files', ()) if isinstance(section, dict) else ():
            if 'source' in item:
                item['content'] = (REPO / item['source']).read_text(encoding='utf-8')
            if not re.fullmatch(r'0[0-7]{3}', item.get('mode', '0644')):
                sys.exit(f'{item["path"]}: mode is four octal digits, such as 0755.')


def valid_profiles(profiles):
    return 'core' in profiles and not set(profiles) - set(manifest_units())


def refuse(plan):
    if platform.machine() != 'x86_64':
        sys.exit(f'{platform.machine()} is not verified: the desktop is tested on x86_64.')
    if not member(getpass.getuser(), plan.distro.ADMIN_GROUP):
        sys.exit(f'{getpass.getuser()} must be in the {plan.distro.ADMIN_GROUP} group to install packages.')


def preflight_warnings(plan):
    warnings = []
    free = shutil.disk_usage('/').free
    if free < MIN_FREE:
        source = query('findmnt', '-no', 'SOURCE', '/').stdout.strip()
        grow = f' Grow it with: sudo lvextend -r -l +100%FREE {source}' if source.startswith('/dev/mapper/') else ''
        warnings.append(f'Only {free // 2**30} GiB free on /.{grow}')
    if setting(plan, 'auth') and plan.distro.auth_base() not in ('local', plan.distro.AUTH_PROFILE):
        warnings.append(f'The auth step expects the local authselect profile, found "{plan.distro.auth_base()}".')
    for item in firmware_needed(plan):
        if not firmware_source(plan, item):
            where = f'{plan.firmware} has no copy of it' if plan.firmware else 'pass --firmware <directory with a copy>'
            warnings.append(f'{item["purpose"]} needs {Path(item["target"]).name} ({item["source"]}): {where}.')
    for path in clones_kept(plan):
        warnings.append(f'~/{path} is there already and is not a clone without local changes: it is left alone.')
    for name in archives_unsupported(plan):
        warnings.append(f'{name} has no build for {platform.machine()}: it is left out.')
    return warnings


def preflight(plan):
    refuse(plan)
    for warning in preflight_warnings(plan):
        print('Warning: ' + warning)


def run_steps(plan, preview, steps=STEPS):
    done = 0
    record = None if preview else load_record(set_aside=steps is STEPS)
    if record and record.get('uninstalled'):
        record = {}  # A new install after an uninstall starts its own record.
    if record is not None and steps is STEPS:
        if not knows_changes(record) and desktop_present():
            # Installed before there was a record: what came then is told by the history, or uninstall would miss it.
            record = {**reconstruct(plan), **record}
        keep(record, 'profiles', plan.profiles)
        save_record(record)
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
                save_record(record)
            step.apply(plan, items)
    return done


def refuse_uninstall():
    # Also for the plugins profile alone: its builds are loaded in the running Hyprland.
    if hyprland_running():
        sys.exit('Hyprland is running: uninstalling removes the configuration it runs on (or, for the plugins profile, '
                 'the plugins it has loaded). Log out, switch to a console (Ctrl+Alt+F3), sign in there and run this again.')


def after_uninstall(plan, done):
    if not done:
        print('Nothing to do.')
        return
    print('Done. Not undone: the system upgrade, and what you changed by hand.')
    print(f'Left in place: your preferences in ~/.config/desktop, and this repository ({REPO}).')


def record_notes(plan):
    # What an uninstall without a record cannot know, said before it starts.
    notes = []
    if plan.record.get('reconstructed'):
        notes.append('The desktop was installed before there was an install record: what came then is read from the manifest '
                     'and the package history, and units apply turned off then (such as sshd.service) stay off.')
    if plan.record.get('base_unknown'):
        notes.append('The package history does not show how the system was installed: no package from before the record is removed.')
    every = every_profile(plan)
    for path in changed_files(plan)[1]:
        notes.append(f'{path} changed since the install: it stays as it is.')
    for path in clones_undoable(plan)[1]:
        notes.append(f'~/{path} changed since the install: it stays as it is.')
    shell = plan.record.get('login_shell')
    if shell and login_shell() not in (shell, setting(every, 'login_shell')):
        notes.append(f'The login shell is now {login_shell()}, chosen after the install: it stays.')
    zone = plan.record.get('firewall_zone')
    if zone and booted() and shutil.which('firewall-cmd') and default_zone_now() not in (zone, setting(every, 'firewall_zone')):
        notes.append(f'The firewall zone is now {default_zone_now()}, chosen after the install: it stays.')
    for name, packages in repos_in_use(plan, recorded_repos(plan)).items():
        shown = ', '.join(packages[:3]) + (f' and {len(packages) - 3} more' if len(packages) > 3 else '')
        notes.append(f'The {name} repository stays: it still provides {shown}.')
    return notes


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


# Pins: manifest entries fixed to a commit, AUR packages and clones, or to a version, release archives. Newer is the
# AUR's latest commit, a clone's latest release tag (track = 'tags'), or else the head of its default branch, and an
# archive's version in its release manifest (latest). version is what the new commit of a PKGBUILD builds, tag the
# release a clone moves to, hashes the sha256 of each architecture of an archive; url shows the changes to review.
Pin = namedtuple('Pin', 'kind name old new label url version tag hashes', defaults=(None,))


def remote_head(repo):
    result = query('git', 'ls-remote', repo, 'HEAD')
    fields = result.stdout.split()
    return fields[0] if result.returncode == 0 and fields else ''


def aur_head(package):
    return remote_head(AUR + package + '.git')


def aur_srcinfo(package, commit):
    url = f'{AUR}cgit/aur.git/plain/.SRCINFO?' + urllib.parse.urlencode({'h': package, 'id': commit})
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode('utf-8')


def version_key(name):
    # Natural order, digits as numbers: 26.10.1 after 26.9.30. Splitting on a group alternates text and numbers.
    return [int(part) if index % 2 else part for index, part in enumerate(re.split(r'(\d+)', name))]


def remote_tags(repo):
    # {tag: commit}. An annotated tag stands for the commit it points to, its ^{} line.
    result = query('git', 'ls-remote', '--tags', repo)
    tags = {}
    for line in result.stdout.splitlines() if result.returncode == 0 else ():
        commit, _, ref = line.partition('\t')
        name = ref.removeprefix('refs/tags/')
        if name.endswith('^{}'):
            tags[name[:-3]] = commit
        elif name:
            tags.setdefault(name, commit)
    return tags


def pin_name(kind, item):
    if kind == 'archives':
        return item['name']
    return item['package'] if kind == 'aur' else item['path'].rstrip('/').rsplit('/', 1)[-1]


def pin_entries(tables, profiles=None):
    # Every pinned entry of these tables, once: the same clone pinned on two distributions moves for both.
    entries = {}
    for table in tables:
        table = flatten_parts(table)
        for profile in profiles or units(table):
            for kind in ('aur', 'clones', 'archives'):
                for item in table.get(profile, {}).get(kind, ()):
                    key = (kind, item.get('package') or item.get('repo') or item['name'], item.get('commit') or item['version'])
                    entries.setdefault(key, (kind, item))
    return list(entries.values())


def newer_archive(item):
    try:
        with open_url(item['latest'], 30) as response:
            latest = json.load(response)
        new, targets = latest['version'], latest['targets']
        hashes = {arch: targets[f'linux-{arch}']['sha256'] for arch in item['sha256']}
        # The download URL must still be the one the manifest builds, or apply would fetch something else.
        urls = [targets[f'linux-{arch}']['url'] for arch in item['sha256']]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    if any(url != item['url'].format(version=new, arch=arch) for arch, url in zip(item['sha256'], urls)):
        return False
    if new == item['version']:
        return None
    return Pin('archives', item['name'], item['version'], new, f'{item["version"]} -> {new}', item.get('changes') or item['latest'],
               '', '', hashes)


def newer_pin(kind, item):
    # The Pin to move to; None when the entry is at its latest; False when its remote did not answer.
    if kind == 'archives':
        return newer_archive(item)
    if kind == 'aur':
        new = aur_head(item['package'])
        if not new or new == item['commit']:
            return None if new else False
        version = srcinfo_version(aur_srcinfo(item['package'], new))
        url = f'{AUR}cgit/aur.git/diff/?' + urllib.parse.urlencode({'h': item['package'], 'id': new, 'id2': item['commit']})
        return Pin(kind, item['package'], item['commit'], new, f'{item["version"]} -> {version}', url, version, '')
    if item.get('track') == 'tags':
        tags = remote_tags(item['repo'])
        if not tags:
            return False
        tag = max(tags, key=version_key)
        new = tags[tag]
        old = next((name for name in sorted(tags, key=version_key) if tags[name] == item['commit']), item['commit'][:12])
        label = f'{old} -> {tag}'
    else:
        new, tag = remote_head(item['repo']), ''
        if not new:
            return False
        label = f'{item["commit"][:12]} -> {new[:12]}'
    if new == item['commit']:
        return None
    url = f'{item["repo"]}/compare/{item["commit"]}...{new}' if item['repo'].startswith('https://github.com/') else item['repo']
    return Pin(kind, pin_name(kind, item), item['commit'], new, label, url, '', tag)


def repin(text, old, new, version='', tag=''):
    # Each manifest table pinned to old, rewritten in place: its commit line, with the release it is at as a comment
    # for a clone that follows tags, and for an AUR package the version line of the same table.
    lines = text.splitlines(keepends=True)
    pinned = re.compile(r"commit = '" + re.escape(old) + r"'(\s*#.*)?")
    for index, line in enumerate(lines):
        if not pinned.fullmatch(line.strip()):
            continue
        lines[index] = f"commit = '{new}'" + (f'  # {tag}' if tag else '') + '\n'
        if not version:
            continue
        start, end = index, index + 1
        while start > 0 and not lines[start].startswith('['):
            start -= 1
        while end < len(lines) and not lines[end].startswith('['):
            end += 1
        for other in range(start, end):
            if lines[other].startswith('version = '):
                lines[other] = f"version = '{version}'\n"
    return ''.join(lines)


def repin_archive(text, name, old, new, hashes):
    # Each archive table of that name at version old: its version and sha256 lines.
    lines = text.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.startswith('[')] + [len(lines)]
    for start, end in zip(starts, starts[1:]):
        block = [line.strip() for line in lines[start:end]]
        if f"name = '{name}'" not in block or f"version = '{old}'" not in block:
            continue
        for index in range(start, end):
            if lines[index].strip() == f"version = '{old}'":
                lines[index] = f"version = '{new}'\n"
            elif lines[index].startswith('sha256 = {'):
                lines[index] = 'sha256 = { ' + ', '.join(f"{arch} = '{digest}'" for arch, digest in hashes.items()) + ' }\n'
    return ''.join(lines)


def apply_pin(text, pin):
    if pin.kind == 'archives':
        return repin_archive(text, pin.name, pin.old, pin.new, pin.hashes)
    return repin(text, pin.old, pin.new, pin.version, pin.tag)


def pins(update):
    # The pins of every distribution, not only this one: they can be moved from any machine.
    path = INSTALL / 'manifest.toml'
    text = path.read_text(encoding='utf-8')
    tables = [table for table in tomllib.loads(text).values() if isinstance(table, dict)]
    newer, failed = [], 0
    for kind, item in pin_entries(tables):
        pin = newer_pin(kind, item)
        if pin is False:
            where = 'the AUR' if kind == 'aur' else item.get('repo') or item['latest']
            print(f'{pin_name(kind, item)}: {where} did not answer.')
            failed += 1
        elif pin:
            newer.append(pin)
            print(f'{pin.name} {pin.label}')
            print(f'  review the changes: {pin.url}')
            if update:
                text = apply_pin(text, pin)
    if update and newer:
        path.write_text(text, encoding='utf-8')
        print(f'Pinned in {path.relative_to(REPO)}: install-desktop.py apply builds and checks them out.')
    elif newer:
        print('install-desktop.py pins --update pins them.')
    elif not failed:
        print('Every pin is at its latest commit.')
    return 1 if failed else 0


def touch_hardware(devices=Path('/proc/bus/input/devices')):
    # A 2-in-1: an input device with a tablet mode switch (SW_TABLET_MODE, bit 1 of SW) or a touchscreen (absolute
    # axes on a direct input device: INPUT_PROP_DIRECT, bit 1 of PROP).
    try:
        text = devices.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return False
    for block in text.split('\n\n'):
        bits = {}
        for line in block.splitlines():
            if line.startswith('B: ') and '=' in line:
                name, _, value = line[3:].partition('=')
                try:
                    bits[name] = int(value.split()[-1], 16) if value.split() else 0
                except ValueError:
                    continue
        if bits.get('SW', 0) & 0b10 or (bits.get('PROP', 0) & 0b10 and 'ABS' in bits):
            return True
    return False


@functools.lru_cache(maxsize=None)
def distro_table():
    # This distribution's table, flattened: what default parts are checked against. Empty where it is not verified.
    manifest = tomllib.loads(MANIFEST.read_text(encoding='utf-8'))
    table = manifest.get(os_release().get('ID', ''))
    return flatten_parts(table) if isinstance(table, dict) else {}


def default_parts(profile, table=None):
    """The parts of profile that start checked: default true, or a detection that finds the hardware here."""
    table = distro_table() if table is None else table
    return tuple(name for name in units(table) if parent(name) == profile and name != profile and part_default(table[name]))


def default_profiles(table=None):
    names = DEFAULT_PROFILES.split(',') + (['tablet'] if touch_hardware() else [])
    names += [part for name in names for part in default_parts(name, table)]
    return ','.join(normalized(names))


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', choices=('dry-run', 'apply', 'post', 'pins'), default='dry-run',
                        help='pins: newer commits than the manifest pins, of AUR packages and clones (from any distribution)')
    parser.add_argument('--update', action='store_true', help='with pins: pin those newer commits in the manifest')
    parser.add_argument('--firmware', metavar='DIR', help='directory searched (by hash) for the vendor firmware the manifest lists')
    parser.add_argument('--profiles', help=f'comma separated, from {", ".join(PROFILES)} and their parts, as profile.part (default: '
                        f'{DEFAULT_PROFILES} with their default parts, and tablet on a 2-in-1)')
    parser.add_argument('--uninstall', action='store_true', help='undo what apply set up, from its record (dry-run shows it, apply does it)')
    parser.add_argument('--remove', metavar='PROFILES', help='undo what only these profiles set up (comma separated, not core), '
                        'leaving what the other installed profiles need')
    args = parser.parse_args(argv)
    if (args.uninstall or args.remove) and args.action in ('post', 'pins'):
        parser.error('--uninstall and --remove go with dry-run or apply.')
    if args.uninstall and args.remove:
        parser.error('--uninstall removes every profile: leave --remove out.')
    removed = tuple(args.remove.split(',')) if args.remove else ()
    if args.remove and not removable_profiles(removed):
        parser.error(f'--remove takes {", ".join(manifest_units()[1:])}; core goes only with --uninstall.')
    # Removing a profile removes its parts.
    removed = with_parts(removed)
    if args.update and args.action != 'pins':
        parser.error('--update goes with pins.')
    profiles = tuple((args.profiles or default_profiles()).split(','))
    if not valid_profiles(profiles):
        parser.error(f'--profiles needs core, and takes only {", ".join(manifest_units())}.')
    # A part brings its profile.
    profiles = normalized(profiles)
    if os.geteuid() == 0:
        sys.exit('Run as the desktop user: the script asks sudo for each system change.')
    if args.action == 'pins':
        return pins(args.update)
    plan = load_plan(profiles, firmware=args.firmware, any_version=args.uninstall)
    plan.distro.remember_answers()
    if removed:
        refuse(plan)
        if args.action == 'apply' and 'plugins' in removed:
            refuse_uninstall()
        plan = removal_plan(plan, removed, preview=args.action == 'dry-run')
        for note in record_notes(plan):
            print('Note: ' + note)
        done = run_steps(plan, args.action == 'dry-run', PROFILE_UNSTEPS)
        if not done:
            print('Nothing to do.')
        elif args.action == 'apply':
            print(f'Done: {", ".join(removed)} removed. Not undone: what you changed by hand.')
        return 0
    if args.uninstall:
        refuse(plan)
        if args.action == 'apply':
            refuse_uninstall()
        plan = uninstall_plan(plan, preview=args.action == 'dry-run')
        for note in record_notes(plan):
            print('Note: ' + note)
        done = run_steps(plan, args.action == 'dry-run', UNSTEPS)
        if args.action == 'apply':
            after_uninstall(plan, done)
        elif not done:
            print('Nothing to do.')
        return 0
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

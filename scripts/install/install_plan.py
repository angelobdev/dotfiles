"""What an install is about: the manifest's units (profiles and profile.part), the plan for this distribution and
these units, what the hardware asks for (detection), and the questions about the system every step asks (query)."""
from collections import namedtuple
import functools
import getpass
import grp
import importlib
from pathlib import Path
import re
import subprocess
import sys
import tomllib

import install_paths


# firmware: the directory --firmware names, searched for the blobs the manifest lists; None when not given.
# record: what an earlier apply changed (RECORD, or rebuilt from the package history), for uninstall.
Plan = namedtuple('Plan', 'distro release table commands profiles firmware record', defaults=(None, None))


# How long a remote (git ls-remote for the pins) may take: the guided installer's Updates screen waits on it.
REMOTE_TIMEOUT = 60


def query(*command, timeout=None):
    # A tool that is not installed yet is an empty answer: the preview runs before the packages. One that takes
    # longer than timeout is a failed one (124, as timeout(1) says).
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return subprocess.CompletedProcess(command, 127, '', '')
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(command, 124, '', f'no answer in {timeout} s')


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
    for profile in install_paths.PROFILES:
        if profile in table:
            names += [profile] + [name for name in table if name.startswith(profile + '.')]
    return tuple(names)


@functools.lru_cache(maxsize=None)
def manifest_units():
    """The units of every distribution of the manifest, for what is checked before a plan is loaded."""
    manifest = tomllib.loads(install_paths.MANIFEST.read_text(encoding='utf-8'))
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
        if vendor in install_paths.FINGERPRINT_VENDORS or vendor == '04f3' and product.startswith('0c'):
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
    reply = query('busctl', 'call', install_paths.ACCOUNTS, '/org/freedesktop/Accounts', install_paths.ACCOUNTS, 'FindUserByName', 's', getpass.getuser())
    parts = reply.stdout.split('"')
    return parts[1] if len(parts) > 1 else ''


def session():
    path = user_object()
    return query('busctl', 'get-property', install_paths.ACCOUNTS, path, install_paths.ACCOUNTS + '.User', 'Session').stdout if path else ''


def os_release(path=Path('/etc/os-release')):
    fields = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        key, separator, value = line.partition('=')
        if separator:
            fields[key] = value.strip('"\'')
    return fields


def load_plan(profiles, release=None, firmware=None, any_version=False):
    manifest = tomllib.loads((install_paths.INSTALL / 'manifest.toml').read_text(encoding='utf-8'))
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
    sys.path.insert(0, str(install_paths.INSTALL))
    table = flatten_parts(table)
    resolve_files(table)
    return Plan(importlib.import_module(name), version, table, manifest['verify']['commands'], profiles, firmware)


def resolve_files(table):
    # A file is written inline (content) or copied from this repository (source), with its mode (default 0644).
    for section in table.values():
        for item in section.get('files', ()) if isinstance(section, dict) else ():
            if 'source' in item:
                item['content'] = (install_paths.REPO / item['source']).read_text(encoding='utf-8')
            if not re.fullmatch(r'0[0-7]{3}', item.get('mode', '0644')):
                sys.exit(f'{item["path"]}: mode is four octal digits, such as 0755.')


def valid_profiles(profiles):
    return 'core' in profiles and not set(profiles) - set(manifest_units())


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
    manifest = tomllib.loads(install_paths.MANIFEST.read_text(encoding='utf-8'))
    table = manifest.get(os_release().get('ID', ''))
    return flatten_parts(table) if isinstance(table, dict) else {}


def default_parts(profile, table=None):
    """The parts of profile that start checked: default true, or a detection that finds the hardware here."""
    table = distro_table() if table is None else table
    return tuple(name for name in units(table) if parent(name) == profile and name != profile and part_default(table[name]))


def default_profiles(table=None):
    names = install_paths.DEFAULT_PROFILES.split(',') + (['tablet'] if touch_hardware() else [])
    names += [part for name in names for part in default_parts(name, table)]
    return ','.join(normalized(names))

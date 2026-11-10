"""The install record (install.json): what apply changed and what was there before, read and written before each
step, so that uninstall can undo exactly that; and the units file Hyprland and the shell read."""
import json
from pathlib import Path
import sys

import install_paths
import bundle  # noqa: E402  (after install_paths, which puts scripts/hyprpm on the path)
import install_plan


def load_record(set_aside=False):
    # Missing: an empty record. Unreadable: empty too, said out loud, and moved aside before anything replaces it.
    # One from before the tablet profile gets it beside hardware, which held it then.
    try:
        record = json.loads(install_paths.RECORD.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        record = None
    if isinstance(record, dict):
        return bundle.migrate(record)
    aside = install_paths.RECORD.with_name(install_paths.RECORD.name + '.unreadable')
    if set_aside:
        install_paths.RECORD.replace(aside)
    print(f'Warning: {install_paths.RECORD} cannot be read' + (f', moved to {aside.name}' if set_aside else '') +
          ': what the installer changed comes from the manifest and the package history instead.', file=sys.stderr)
    return {}


def knows_changes(record):
    # Only profiles: an apply that found nothing to do on an install made before there was a record.
    return bool(set(record) - {'profiles', 'profiles_version'})


def save_record(record):
    if 'profiles' in record:
        record['profiles_version'] = bundle.PROFILES_VERSION
    install_paths.RECORD.parent.mkdir(parents=True, exist_ok=True)
    temporary = install_paths.RECORD.with_name(install_paths.RECORD.name + '.tmp')
    temporary.write_text(json.dumps(record, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(install_paths.RECORD)
    save_units(record)


def save_units(record):
    """UNITS: the installed units, one per line, for what Hyprland (config/installed.lua) and the shell (Installed.qml)
    show only with their unit. Without a list of profiles (uninstalled, or none yet), no file: everything counts."""
    profiles = record.get('profiles')
    if not isinstance(profiles, list) or record.get('uninstalled'):
        install_paths.UNITS.unlink(missing_ok=True)
        return
    temporary = install_paths.UNITS.with_name(install_paths.UNITS.name + '.tmp')
    temporary.write_text(''.join(f'{name}\n' for name in profiles if isinstance(name, str)), encoding='utf-8')
    temporary.replace(install_paths.UNITS)


def keep(record, key, values):
    items = record.setdefault(key, [])
    items += [value for value in values if value not in items]


def current_session():
    # busctl prints 's "hyprland-uwsm"': the last quoted string.
    parts = install_plan.session().split('"')
    return parts[-2] if len(parts) > 2 else ''


def default_target():
    return install_plan.query('systemctl', 'get-default').stdout.strip()


def default_zone_now():
    return install_plan.query('firewall-cmd', '--get-default-zone').stdout.strip()


def read_or_none(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        return None

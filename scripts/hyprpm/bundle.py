"""The plugin bundle and its state: what is built, from which packaging, for which Hyprland.

Outside the bundle, so it is not part of its digest: accepting a Hyprland build here rebuilds nothing by itself.
"""
import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tomllib

import build
from build import PLUGINS, release_id

PACKAGING = Path(__file__).resolve().parent
# What hyprpm builds from: a change to any of these is a new bundle, rebuilt at the next login.
FILES = ('build.py', 'hyprpm.toml', 'hyprgrass-touch-as-pointer.patch')
REPOSITORY = 'dotfiles-desktop'
# Builds of Hyprland and its headers the pins in build.py were verified against: Fedora's RPM, Arch's package.
VERIFIED = ('0.57.1-1.fc45.x86_64', '0.57.1-1')
CACHE = Path('/var/cache/hyprpm') / getpass.getuser()
STAMP = Path.home() / '.local/state/dotfiles/hypr-plugins.json'
# The installer's record (install-desktop.py RECORD): its profiles say which plugins to build.
RECORD = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'dotfiles/install.json'
# Plugins built only with a profile: the touchscreen gestures are for a 2-in-1.
PROFILE_OF = {'hyprgrass': 'tablet'}
# Records say which profiles they name. 2: tablet left hardware. 3: profiles have parts (profile.part), herdr became
# assistant, media radio, codecs went into core, steam-hidpi into gaming, and apps split into apps and utils.
PROFILES_VERSION = 3
# A version 2 profile as the units of version 3 that hold what it installed.
UNITS_OF_V2 = {
    'hardware': ['hardware', 'hardware.intel', 'hardware.audio', 'hardware.camera', 'hardware.fingerprint', 'hardware.firmware'],
    'apps': ['apps', 'apps.zen', 'apps.onepassword', 'apps.vscode', 'utils', 'utils.neovim', 'utils.gcc', 'utils.xclip',
             'utils.unrar', 'utils.fuse', 'utils.gh', 'utils.glab', 'utils.uv', 'utils.wev'],
    'herdr': ['assistant'],
    'containers': ['containers', 'utils', 'utils.tailscale'],
    'media': ['radio', 'apps', 'apps.loupe', 'apps.papers', 'apps.showtime'],
    'gaming': ['gaming', 'gaming.steam', 'gaming.gamescope'],
    'steam-hidpi': ['gaming', 'gaming.steam-hidpi'],
    'codecs': ['core'],
}

# status(): what the plugins need, from the least to the most work.
CURRENT = 'current'          # built from this bundle for the installed Hyprland
MISSING = 'missing'          # never installed: the first login after the installer builds them
INCOMPLETE = 'incomplete'    # built once, but a rebuild stopped halfway: the repository is gone or a plugin failed
PACKAGING_CHANGED = 'packaging'
COMPOSITOR_CHANGED = 'compositor'
UNVERIFIED = 'unverified'    # Hyprland changed to a build the pins were not verified against
MISMATCHED = 'mismatched'    # hyprland and hyprland-devel differ: an update stopped halfway, nothing can be built


def headers_package():
    # Fedora ships Hyprland's headers in hyprland-devel; Arch keeps them in hyprland itself.
    return 'hyprland' if release_id() == 'arch' else 'hyprland-devel'


def package_version(package):
    # The installed build, or '' when the package is missing.
    try:
        return build.package_version(package)
    except (subprocess.CalledProcessError, OSError, ValueError):
        return ''


def verify():
    # Refuse unreviewed compositor builds and mismatched headers.
    version = package_version('hyprland')
    if version != package_version(headers_package()):
        raise RuntimeError('hyprland and hyprland-devel must have the same RPM version')
    if version not in VERIFIED:
        raise RuntimeError('Hyprland build differs from the verified version: update and verify pins before building')
    return version


def migrate(record):
    """A record of an older version, in the names of this one. Only names change: nothing is installed or removed."""
    profiles = record.get('profiles')
    version = record.get('profiles_version')
    if not isinstance(profiles, list) or version == PROFILES_VERSION:
        return record
    # Version 1: its hardware profile was hardware and tablet together.
    if version is None and 'hardware' in profiles and 'tablet' not in profiles:
        profiles.insert(profiles.index('hardware') + 1, 'tablet')
    units = []
    for name in profiles:
        units += [unit for unit in UNITS_OF_V2.get(name, [name]) if unit not in units]
    record['profiles'] = units
    record['profiles_version'] = PROFILES_VERSION
    return record


def recorded_profiles():
    # The profiles the installer applied, or None without a record (plugins installed by hand: all of them).
    try:
        record = json.loads(RECORD.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or record.get('uninstalled') or not isinstance(record.get('profiles'), list):
        return None
    return migrate(record)['profiles']


def selected(profiles=False):
    # The plugins to build, in PLUGINS order: those of a profile only when it is installed.
    profiles = recorded_profiles() if profiles is False else profiles
    return tuple(name for name in PLUGINS if profiles is None or PROFILE_OF.get(name, 'core') == 'core' or PROFILE_OF[name] in profiles)


def manifest(names):
    # hyprpm.toml with only these plugins: hyprpm builds every plugin its manifest lists.
    text = (PACKAGING / 'hyprpm.toml').read_text(encoding='utf-8')
    if tuple(names) == tuple(PLUGINS):
        return text
    blocks = text.split('\n\n')
    kept = [block for block in blocks if not any(f'[{name}]' in block.splitlines() for name in PLUGINS if name not in names)]
    return '\n\n'.join(kept)


def digest(names=None):
    # The full set keeps the digest it always had: a laptop with every plugin rebuilds nothing for this.
    names = selected() if names is None else tuple(names)
    data = b''.join((PACKAGING / name).read_bytes() for name in FILES)
    if names != tuple(PLUGINS):
        data += ('\0plugins:' + ','.join(names)).encode()
    return hashlib.sha256(data).hexdigest()[:16]


def repository_state():
    try:
        return tomllib.loads((CACHE / REPOSITORY / 'state.toml').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def installed_digest():
    # hyprpm records where it built from; the installer names that directory after the digest.
    url = repository_state().get('repository', {}).get('url', '')
    return url.rstrip('/').rsplit('/', 1)[-1] if url else ''


def complete():
    # Every plugin built: hyprpm marks one that did not with failed = true, and a removed repository has none.
    state = repository_state()
    return bool(installed_digest()) and not any(state.get(name, {}).get('failed', True) for name in selected())


def stamp():
    try:
        return json.loads(STAMP.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def status():
    built = stamp()
    if not built:
        return MISSING
    version = package_version('hyprland')
    if version != package_version(headers_package()):
        return MISMATCHED
    # The stamp keeps the build under 'rpm', its name from before Arch: any distribution's package build.
    if version != built.get('rpm'):
        return COMPOSITOR_CHANGED if version in VERIFIED else UNVERIFIED
    if not complete():
        return INCOMPLETE
    if installed_digest() != digest():
        return PACKAGING_CHANGED
    return CURRENT

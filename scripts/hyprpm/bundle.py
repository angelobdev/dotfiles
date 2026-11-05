"""The plugin bundle and its state: what is built, from which packaging, for which Hyprland.

Outside the bundle, so it is not part of its digest: accepting a Hyprland build here rebuilds nothing by itself.
"""
import getpass
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

from build import PLUGINS

PACKAGING = Path(__file__).resolve().parent
# What hyprpm builds from: a change to any of these is a new bundle, rebuilt at the next login.
FILES = ('build.py', 'hyprpm.toml', 'hyprgrass-hold-touches.patch')
REPOSITORY = 'dotfiles-desktop'
# RPM builds of hyprland and hyprland-devel the pins in build.py were verified against.
VERIFIED = ('0.57.1-1.fc45.x86_64',)
CACHE = Path('/var/cache/hyprpm') / getpass.getuser()
STAMP = Path.home() / '.local/state/dotfiles/hypr-plugins.json'

# status(): what the plugins need, from the least to the most work.
CURRENT = 'current'          # built from this bundle for the installed Hyprland
MISSING = 'missing'          # never installed: the first login after the installer builds them
INCOMPLETE = 'incomplete'    # built once, but a rebuild stopped halfway: the repository is gone or a plugin failed
PACKAGING_CHANGED = 'packaging'
COMPOSITOR_CHANGED = 'compositor'
UNVERIFIED = 'unverified'    # Hyprland changed to a build the pins were not verified against
MISMATCHED = 'mismatched'    # hyprland and hyprland-devel differ: an update stopped halfway, nothing can be built


def rpm_version(package):
    result = subprocess.run(('rpm', '-q', '--qf', '%{VERSION}-%{RELEASE}.%{ARCH}', package), capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ''


def verify():
    # Refuse unreviewed compositor builds and mismatched headers.
    version = rpm_version('hyprland')
    if version != rpm_version('hyprland-devel'):
        raise RuntimeError('hyprland and hyprland-devel must have the same RPM version')
    if version not in VERIFIED:
        raise RuntimeError('Hyprland build differs from the verified version: update and verify pins before building')
    return version


def digest():
    return hashlib.sha256(b''.join((PACKAGING / name).read_bytes() for name in FILES)).hexdigest()[:16]


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
    return bool(installed_digest()) and not any(state.get(name, {}).get('failed', True) for name in PLUGINS)


def stamp():
    try:
        return json.loads(STAMP.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def status():
    built = stamp()
    if not built:
        return MISSING
    version = rpm_version('hyprland')
    if version != rpm_version('hyprland-devel'):
        return MISMATCHED
    if version != built.get('rpm'):
        return COMPOSITOR_CHANGED if version in VERIFIED else UNVERIFIED
    if not complete():
        return INCOMPLETE
    if installed_digest() != digest():
        return PACKAGING_CHANGED
    return CURRENT

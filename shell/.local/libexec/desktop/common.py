"""Shared by the helpers: atomic file replacement, the image types they accept, ImageMagick, Hyprland and the distribution."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

# What the wallpaper and theme helpers accept as an image (decoded by ImageMagick).
IMAGES = {'.png', '.jpg', '.jpeg', '.webp', '.jxl', '.avif', '.bmp', '.tif', '.tiff'}
# Resource limits, so a huge image cannot take the memory of the session.
MAGICK = ['magick', '-limit', 'memory', '256MiB', '-limit', 'map', '512MiB']
# Icon and cursor theme folder names. They end up in Lua, JSON and INI files, and some come from the KDE Store,
# so only plain names are offered or installed.
THEME_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9 ._+-]{0,63}')


def theme_name(name):
    return isinstance(name, str) and THEME_NAME.fullmatch(name) is not None


# A temporary file next to path that replaces it when the block succeeds and is removed otherwise. follow
# writes through a symlink to its target; without it the link itself is replaced. suffix is for tools that
# pick the format from the name (ImageMagick); without one, listings by extension never see the temporary.
# The permissions are those of the file being replaced, else 0644 (mkstemp creates 0600; these are ordinary
# files, readable like the rest of ~/.config).
@contextlib.contextmanager
def replacing(path, follow=True, suffix='', mode=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if follow and path.is_symlink():
        path = path.resolve()
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.', suffix=suffix)
    os.close(handle)
    try:
        yield Path(temporary)
        keep = path.exists() and not path.is_symlink()
        os.chmod(temporary, mode if mode is not None else stat.S_IMODE(path.stat().st_mode) if keep else 0o644)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)



# Downloads url into destination through replacing(): a file whose digest is not expected, or that grows past
# limit bytes, never replaces what was there. The messages are the caller's own (translated) words. urllib is
# imported here, so helpers that never download (osk.py through predict.py) do not load it.
def download(url, destination, expected='', algorithm='sha256', mismatch='', limit=None, too_large='', headers=None, timeout=30):
    import urllib.request
    digest, size = hashlib.new(algorithm), 0
    request = urllib.request.Request(url, headers=headers or {})
    with replacing(destination) as temporary:
        with urllib.request.urlopen(request, timeout=timeout) as response, temporary.open('wb') as file:
            for block in iter(lambda: response.read(1024 * 1024), b''):
                size += len(block)
                if limit is not None and size > limit:
                    raise ValueError(too_large)
                digest.update(block)
                file.write(block)
        if expected and digest.hexdigest() != expected:
            raise ValueError(mismatch)

def write_atomic(path, text, follow=True, mode=None):
    # mode: always this one (private files), instead of the replaced file's.
    with replacing(path, follow, mode=mode) as temporary:
        temporary.write_text(text, encoding='utf-8')


def magick(*arguments, timeout=60, check=False):
    return subprocess.run(MAGICK + [str(argument) for argument in arguments], capture_output=True, text=True,
                          timeout=timeout, check=check)


def hypr_json(*args):
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        return None
    try:
        result = subprocess.run(['hyprctl', '-j', *args], check=True,
                                capture_output=True, text=True, timeout=2)
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def focused_monitor():
    monitors = hypr_json('monitors')
    if not isinstance(monitors, list):
        return None
    active = [m for m in monitors if isinstance(m, dict) and not m.get('disabled')]
    return next((m for m in active if m.get('focused')), active[0] if active else None)


def release_id(path=Path('/etc/os-release')):
    # The distribution: the package manager and some package names differ between Fedora and Arch.
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except OSError:
        return ''
    return next((line.partition('=')[2].strip('"\'') for line in lines if line.startswith('ID=')), '')


# How each distribution installs packages; Fedora's for any other, as before Arch.
INSTALL = {'fedora': 'sudo dnf install', 'arch': 'sudo pacman -S'}


def install_command(packages):
    # packages: the names, or {distribution: names} where they differ (Fedora's names for any other).
    distribution = release_id()
    if isinstance(packages, dict):
        packages = packages.get(distribution, packages['fedora'])
    return f"{INSTALL.get(distribution, INSTALL['fedora'])} {' '.join(packages)}"

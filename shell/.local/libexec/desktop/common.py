"""Shared by the helpers: atomic file replacement, the image types they accept, ImageMagick and Hyprland."""
import contextlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

# What the wallpaper and theme helpers accept as an image (decoded by ImageMagick).
IMAGES = {'.png', '.jpg', '.jpeg', '.webp', '.jxl', '.avif', '.bmp', '.tif', '.tiff'}
# Resource limits, so a huge image cannot take the memory of the session.
MAGICK = ['magick', '-limit', 'memory', '256MiB', '-limit', 'map', '512MiB']


# A temporary file next to path that replaces it when the block succeeds and is removed otherwise. follow
# writes through a symlink to its target; without it the link itself is replaced. suffix is for tools that
# pick the format from the name (ImageMagick); without one, listings by extension never see the temporary.
# The permissions are those of the file being replaced, else 0644 (mkstemp creates 0600; these are ordinary
# files, readable like the rest of ~/.config).
@contextlib.contextmanager
def replacing(path, follow=True, suffix=''):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if follow and path.is_symlink():
        path = path.resolve()
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.', suffix=suffix)
    os.close(handle)
    try:
        yield Path(temporary)
        keep = path.exists() and not path.is_symlink()
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode) if keep else 0o644)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_atomic(path, text, follow=True):
    with replacing(path, follow) as temporary:
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

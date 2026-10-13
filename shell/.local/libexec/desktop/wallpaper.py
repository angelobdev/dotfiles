#!/usr/bin/env python3
"""Apply a wallpaper through hyprpaper, persisting a managed local JPEG copy."""
from i18n import tr
from pathlib import Path
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.jxl', '.avif', '.bmp', '.tif', '.tiff'}

def main():
    home = Path.home()
    state = Path(os.environ.get('XDG_STATE_HOME', home / '.local/state')) / 'desktop-session/wallpaper'
    default = Path(os.environ.get('XDG_DATA_HOME', home / '.local/share')) / 'wallpapers/desktop-night.jpg'
    state.mkdir(parents=True, exist_ok=True)
    current = state / 'current.jpg'
    # hyprpaper's stowed config uses the standard XDG path, matching the rest of this repo.
    with (state / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if sys.argv[1:] == ['--ensure']:
            if not current.is_file():
                if not default.is_file():
                    raise ValueError(tr('wallpaper.errors.defaultMissing'))
                replace_link(current, default)
            return
        if len(sys.argv) != 2:
            raise ValueError(tr('wallpaper.errors.usage'))
        original = default if sys.argv[1] == '--reset' else Path(sys.argv[1]).expanduser().resolve()
        if not original.is_file() or original.suffix.lower() not in EXTENSIONS:
            raise ValueError(tr('wallpaper.errors.invalidImage'))
        digest = hashlib.sha256()
        with original.open('rb') as data:
            for block in iter(lambda: data.read(1024 * 1024), b''):
                digest.update(block)
        rendered = state / (digest.hexdigest()[:24] + '.jpg')
        if not rendered.is_file():
            fd, temporary = tempfile.mkstemp(suffix='.jpg', prefix='.render-', dir=state)
            os.close(fd)
            try:
                result = subprocess.run(['magick', '-limit', 'memory', '256MiB', '-limit', 'map', '512MiB',
                    str(original) + '[0]', '-auto-orient', '-quality', '92', temporary],
                    capture_output=True, text=True, timeout=45)
                if result.returncode != 0 or Path(temporary).stat().st_size == 0:
                    raise ValueError(tr('wallpaper.errors.decodePrefix') + result.stderr.strip()[:400])
                os.replace(temporary, rendered)
            finally:
                Path(temporary).unlink(missing_ok=True)
        # The generated path contains no commas/newlines, so IPC filenames are unambiguous.
        applied = subprocess.run(['hyprctl', 'hyprpaper', 'wallpaper', ',' + str(rendered) + ',cover'],
            capture_output=True, text=True, timeout=10)
        if applied.returncode != 0 or 'error' in (applied.stdout + applied.stderr).lower():
            raise ValueError(tr('wallpaper.errors.applyFailedPrefix') +
                (applied.stderr or applied.stdout).strip()[:300])
        replace_link(current, rendered)
        fd, temporary = tempfile.mkstemp(prefix='.selection-', dir=state)
        with os.fdopen(fd, 'w') as output:
            json.dump({'source': str(original), 'rendered': str(rendered)}, output, ensure_ascii=False)
            output.write('\n')
        os.replace(temporary, state / 'selection.json')
        # Keep the current image only: the original selected file is never modified.
        for cached in state.glob('*.jpg'):
            if cached != current and cached != rendered and not cached.is_symlink():
                cached.unlink()
        print(tr('wallpaper.appliedPrefix') + original.name)

def replace_link(destination, target):
    # Unique name plus atomic rename: a failed conversion never replaces the prior selection.
    fd, name = tempfile.mkstemp(prefix='.current-', dir=destination.parent)
    os.close(fd)
    temporary = Path(name)
    temporary.unlink()
    try:
        temporary.symlink_to(target)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

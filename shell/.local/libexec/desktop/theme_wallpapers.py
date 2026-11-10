"""The wallpapers of a theme: its set (shipped or downloaded, checked by sha256), the one remembered per theme,
the one shown now (wallpaper.py applies it), and the thumbnails the gallery shows."""
from common import IMAGES, magick, replacing, write_atomic
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import theme_assets
import theme_core
import theme_paths


def thumb_path(path):
    path = Path(path)
    try:
        info = path.stat()
        key = f'{path}\0{info.st_mtime_ns}\0{info.st_size}'
    except OSError:
        key = str(path)
    return theme_paths.THUMBS / (hashlib.sha1(key.encode()).hexdigest() + '.jpg')


def make_thumb(path):
    target = thumb_path(path)
    if target.is_file():
        return target
    with replacing(target, suffix='.jpg') as temporary:
        magick(str(path) + '[0]', '-auto-orient', '-thumbnail', '480x300^', '-gravity', 'center', '-extent', '480x300',
               '-quality', '85', temporary, check=True)
    return target


def make_thumbs(paths):
    for path in paths:
        status = {'path': str(path)}
        try:
            print(json.dumps(dict(status, thumb=str(make_thumb(path)), status='ready'), ensure_ascii=False), flush=True)
        except (OSError, subprocess.SubprocessError) as error:
            print(json.dumps(dict(status, status='failed', error=str(error)), ensure_ascii=False), flush=True)


def wallpaper_entries(name, theme):
    entries = []
    for entry in theme.get('wallpapers', []):
        path = theme_paths.WALLPAPERS / name / entry['file']
        thumb = thumb_path(path)
        entries.append(dict(entry, path=str(path), downloaded=path.is_file(), thumb=str(thumb), thumbReady=thumb.is_file()))
    return entries


# The images a theme can show now: its downloaded pack in manifest order, or the directories it names.
def wallpaper_files(name, theme):
    if theme.get('wallpapers'):
        return [Path(entry['path']) for entry in wallpaper_entries(name, theme) if entry['downloaded']]
    files = []
    for directory in theme.get('wallpaperDirectories', []):
        directory = Path(directory).expanduser()
        if directory.is_dir():
            files += sorted(path for path in directory.iterdir() if path.suffix.lower() in IMAGES and path.is_file())
    return files


# wallpaper.py records the resolved path, while the listed files may be links (the stowed default), so
# both sides are compared resolved.
def next_wallpaper(files, current):
    if not files:
        return None
    resolved = [path.resolve() for path in files]
    current = Path(current).resolve() if current else None
    if current in resolved:
        return files[(resolved.index(current) + 1) % len(files)]
    return files[0]


def memory():
    try:
        value = json.loads((theme_paths.STATE / 'wallpapers.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def remember(name, path):
    if path:
        write_atomic(theme_paths.STATE / 'wallpapers.json', json.dumps(dict(memory(), **{name: str(path)}), ensure_ascii=False) + '\n')


def current_wallpaper():
    try:
        return json.loads(theme_paths.SELECTION.read_text(encoding='utf-8')).get('source')
    except (OSError, ValueError, AttributeError):
        return None


# The current wallpaper when it was chosen under the theme name. Switching away from a theme before its own
# wallpaper landed (a conversion or download still running, or offline) leaves the previous theme's image on
# screen, which is not this theme's. A selection from before wallpaper.py noted the theme counts as its.
def wallpaper_chosen_under(name):
    try:
        selection = json.loads(theme_paths.SELECTION.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(selection, dict) or selection.get('theme', name) != name:
        return None
    return selection.get('source')


# The remembered wallpaper while it still exists, else the first available one.
def wallpaper_for(name, theme):
    remembered = memory().get(name)
    if remembered and Path(remembered).is_file():
        return Path(remembered)
    files = wallpaper_files(name, theme)
    return files[0] if files else None


def apply_wallpaper(path):
    result = subprocess.run([sys.executable, str(theme_paths.WALLPAPER), str(path)], capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or str(path))


# Downloads what is missing, one JSON line per entry. With show, the theme's wallpaper is applied as soon
# as one is available, unless the user switched theme in the meantime.
def fetch(name, theme, show=False):
    shown = False
    def show_now():
        nonlocal shown
        if show and not shown and theme_core.current() == name:
            target = wallpaper_for(name, theme)
            if target:
                apply_wallpaper(target)
                shown = True
    show_now()
    failures = 0
    for entry in wallpaper_entries(name, theme):
        status = {'theme': name, 'file': entry['file']}
        if entry['downloaded']:
            print(json.dumps(dict(status, status='present')), flush=True)
            continue
        try:
            theme_assets.download(entry, Path(entry['path']))
            try:
                make_thumb(entry['path'])
            except (OSError, subprocess.SubprocessError):
                pass
            print(json.dumps(dict(status, status='downloaded')), flush=True)
            show_now()
        except (OSError, ValueError) as error:
            failures += 1
            print(json.dumps(dict(status, status='failed', error=str(error)), ensure_ascii=False), flush=True)
    return failures

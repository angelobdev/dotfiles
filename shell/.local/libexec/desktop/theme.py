#!/usr/bin/env python3
"""Render the desktop theme into the files the shell and applications read."""
from i18n import tr
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import urllib.request

HOME = Path.home()
STATE = Path(os.environ.get('XDG_STATE_HOME') or HOME / '.local/state') / 'desktop-theme'
DATA = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'desktop'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'desktop'
# User themes override the ones shipped by the dotfiles.
THEME_DIRS = (CONFIG / 'themes', DATA / 'themes')
TEMPLATES = DATA / 'templates'
BTOP = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'btop'
VSCODE = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'Code/User/settings.json'
VSCODE_EXTENSIONS = HOME / '.vscode/extensions'
# Downloaded theme wallpapers live outside the repository; wallpaper.py owns applying them.
WALLPAPERS = DATA / 'wallpapers'
SELECTION = Path(os.environ.get('XDG_STATE_HOME') or HOME / '.local/state') / 'desktop-session/wallpaper/selection.json'
WALLPAPER = Path(__file__).resolve().with_name('wallpaper.py')
IMAGES = {'.png', '.jpg', '.jpeg', '.webp', '.jxl', '.avif', '.bmp', '.tif', '.tiff'}
REQUIRED = ('bg', 'base', 'raised', 'border', 'fg', 'muted', 'dim', 'accent', 'accentFg', 'link', 'danger',
            'success', 'warning')
DEFAULT = 'graphite'
# {{ path }} or {{ path | filter }} or {{ path | filter:alpha }}; braces are free for CSS, Lua and JSON.
PLACEHOLDER = re.compile(r'\{\{\s*([A-Za-z0-9_.]+)\s*(?:\|\s*([a-z]+)(?::([0-9a-f]{2}))?\s*)?\}\}')
COLOR = re.compile(r'#([0-9a-f]{6})([0-9a-f]{2})?')
SCHEMA = 'org.gnome.desktop.interface'


def split_color(value, path):
    match = COLOR.fullmatch(str(value))
    if not match:
        raise ValueError(tr('theme.errors.color', [path, value]))
    return match[1], match[2]


def convert(value, path, name, alpha):
    if name is None:
        return str(value)
    rgb, own = split_color(value, path)
    alpha = alpha or own
    if name == 'hex':
        return '#' + rgb
    if name == 'rgba':
        return rgb + (alpha or 'ff')
    # Qt and Hyprland put alpha first; a colour without alpha stays #rrggbb for Qt.
    if name == 'qt':
        return '#' + (alpha or '') + rgb
    if name == 'hypr':
        return '0x' + (alpha or 'ff') + rgb
    # Hyprglass takes its tint as 0xRRGGBBAA.
    if name == 'hexrgba':
        return '0x' + rgb + (alpha or 'ff')
    raise ValueError(tr('theme.errors.filter', [name]))


def lookup(theme, path):
    value = theme
    for part in path.split('.'):
        if isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        elif isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def render(text, theme, template):
    def replace(match):
        value = lookup(theme, match[1])
        if value is None or isinstance(value, (dict, list)):
            raise ValueError(tr('theme.errors.template', [template, match[1]]))
        return convert(value, match[1], match[2], match[3])
    return PLACEHOLDER.sub(replace, text)


def theme_path(name):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', name):
        raise ValueError(tr('theme.errors.unknown', [name]))
    for directory in THEME_DIRS:
        path = directory / name / 'theme.json'
        if path.is_file():
            return path
    raise ValueError(tr('theme.errors.unknown', [name]))


def load(name):
    path = theme_path(name)
    try:
        theme = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise ValueError(tr('theme.errors.invalid', [name, error])) from error
    if not isinstance(theme, dict) or not isinstance(theme.get('palette'), dict):
        raise ValueError(tr('theme.errors.invalid', [name, path]))
    missing = [key for key in REQUIRED if key not in theme['palette']]
    if missing:
        raise ValueError(tr('theme.errors.invalid', [name, 'palette.' + ', palette.'.join(missing)]))
    return complete(theme)


def mix(first, second, amount):
    a, b = split_color(first, 'mix')[0], split_color(second, 'mix')[0]
    return '#' + ''.join('%02x' % round(int(a[i:i + 2], 16) * (1 - amount) + int(b[i:i + 2], 16) * amount)
                         for i in (0, 2, 4))


def alpha(color, value):
    return '#' + split_color(color, 'alpha')[0] + value


# Values a theme may leave out, derived from its palette. Explicit keys always win, so Graphite, which
# spells everything out, renders exactly as before.
def complete(theme):
    theme = json.loads(json.dumps(theme))
    palette = theme['palette']
    for key, value in (('light', mix(palette['border'], palette['fg'], 0.2)),
                       ('mid', mix(palette['raised'], palette['border'], 0.5)),
                       ('dark', mix(palette['bg'], '#000000', 0.35)),
                       ('shadow', mix(palette['bg'], '#000000', 0.5)),
                       ('brightText', '#ffffff')):
        palette.setdefault(key, value)
    shell = theme.setdefault('shell', {})
    for key, value in (('background', alpha(palette['bg'], 'f2')), ('surface', alpha(palette['bg'], 'd9')),
                       ('raised', alpha(palette['base'], 'e6')), ('tile', alpha(palette['raised'], 'e6')),
                       ('accentText', palette['accentFg']), ('track', alpha(mix(palette['dim'], palette['bg'], 0.3), '80')),
                       ('stroke', alpha(palette['fg'], '28')), ('text', palette['fg']), ('muted', palette['muted']),
                       ('accent', palette['accent']), ('danger', palette['danger']), ('scrim', '#00000014'),
                       ('scrimModal', '#00000099'), ('scrimStrong', '#000000bb'), ('tooltip', alpha(palette['raised'], 'f0')),
                       ('handlePressed', palette['brightText']), ('handleFocus', mix(palette['muted'], palette['dim'], 0.5)),
                       ('barShadeTop', '#00000055'), ('barShadeBottom', '#00000044'), ('shareShade', '#00000028')):
        shell.setdefault(key, value)
    hyprland = theme.setdefault('hyprland', {})
    hyprland.setdefault('shadow', alpha(palette['shadow'], '66'))
    hyprland.setdefault('glassTint', alpha(palette['bg'], '22'))
    theme.setdefault('terminal', {}).setdefault('opacity', 0.94)
    return theme


def themes():
    found = {}
    for directory in reversed(THEME_DIRS):
        for path in sorted(directory.glob('*/theme.json')):
            try:
                theme = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            found[path.parent.name] = {'id': path.parent.name, 'name': theme.get('name', path.parent.name),
                                       'mode': theme.get('mode', 'dark')}
    return sorted(found.values(), key=lambda t: t['name'].lower())


def render_all(theme, templates=TEMPLATES):
    outputs = {}
    for path in sorted(templates.glob('*.tpl')):
        outputs[path.stem] = render(path.read_text(encoding='utf-8'), theme, path.name)
    return outputs


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write through a symlink to its target, and keep the permissions of a file being replaced.
    path = path.resolve() if path.is_symlink() else path
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as file:
            file.write(text)
        if path.exists():
            os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def current():
    try:
        name = json.loads((STATE / 'current.json').read_text(encoding='utf-8')).get('theme')
    except (OSError, ValueError, AttributeError):
        name = None
    return name if isinstance(name, str) and name else DEFAULT


# Everything is rendered before anything is written, so a template error leaves the old theme intact.
def apply(name):
    theme = load(name)
    outputs = render_all(theme)
    for file, text in outputs.items():
        write_atomic(STATE / file, text)
    write_atomic(STATE / 'current.json', json.dumps({'theme': name}, ensure_ascii=False) + '\n')
    apply_btop(outputs.get('btop.theme'))
    apply_gsettings(theme)
    return theme


# btop rewrites btop.conf on exit, so it cannot be a stowed symlink: the theme goes into its themes
# directory as "desktop" and btop.conf only has its color_theme line pointed at it.
def apply_btop(text):
    config = BTOP / 'btop.conf'
    if text is None or not config.is_file():
        return
    write_atomic(BTOP / 'themes/desktop.theme', text)
    lines = config.read_text(encoding='utf-8').splitlines(keepends=True)
    wanted = 'color_theme = "desktop"\n'
    changed = [wanted if line.startswith('color_theme =') else line for line in lines]
    if not any(line.startswith('color_theme =') for line in lines):
        changed.append(wanted)
    if changed != lines:
        write_atomic(config, ''.join(changed))


def extension_installed(extension):
    prefix = extension.lower() + '-'
    return VSCODE_EXTENSIONS.is_dir() and any(path.name.lower().startswith(prefix) for path in VSCODE_EXTENSIONS.iterdir())


# A targeted edit keeps the rest of settings.json, its order and formatting as VS Code wrote them.
def vscode_settings(text, key, colour_theme):
    value = json.dumps(colour_theme, ensure_ascii=False)
    pattern = re.compile('(' + re.escape(json.dumps(key)) + r'\s*:\s*)"(?:[^"\\]|\\.)*"')
    if pattern.search(text):
        updated = pattern.sub(lambda match: match[1] + value, text, count=1)
    else:
        opening = text.index('{') + 1
        updated = text[:opening] + '\n    ' + json.dumps(key) + ': ' + value + ',' + text[opening:]
    json.loads(updated)
    return updated


def apply_vscode(theme):
    settings = theme.get('vscode', {})
    colour_theme = settings.get('theme')
    if not colour_theme or not VSCODE.is_file():
        return
    if settings.get('extension') and not extension_installed(settings['extension']):
        return
    # With window.autoDetectColorScheme VS Code uses the preferred theme for the system mode instead.
    preferred = 'workbench.preferredLightColorTheme' if theme.get('mode') == 'light' else 'workbench.preferredDarkColorTheme'
    try:
        text = VSCODE.read_text(encoding='utf-8')
        json.loads(text)
        updated = text
        for key in ('workbench.colorTheme', preferred):
            updated = vscode_settings(updated, key, colour_theme)
    except ValueError:
        return
    if updated != text:
        write_atomic(VSCODE, updated)


def apply_gsettings(theme):
    try:
        keys = set(subprocess.run(['gsettings', 'list-keys', SCHEMA], capture_output=True, text=True,
                                  check=True, timeout=5).stdout.split())
    except (OSError, subprocess.SubprocessError):
        return
    fonts = theme.get('fonts', {})
    system = theme.get('system', {})
    values = {
        'color-scheme': 'prefer-light' if theme.get('mode') == 'light' else 'prefer-dark',
        'gtk-theme': system.get('gtkTheme'),
        'icon-theme': system.get('iconTheme'),
        'font-name': fonts.get('sans') and f"{fonts['sans']} {fonts.get('size', 10)}",
        'monospace-font-name': fonts.get('mono') and f"{fonts['mono']} {fonts.get('size', 10)}",
        'cursor-theme': system.get('cursorTheme'),
        'cursor-size': system.get('cursorSize'),
        'accent-color': system.get('accentColor'),
    }
    for key, value in values.items():
        if key in keys and value not in (None, ''):
            subprocess.run(['gsettings', 'set', SCHEMA, key, str(value)], check=False, timeout=5)


def wallpaper_entries(name, theme):
    entries = []
    for entry in theme.get('wallpapers', []):
        path = WALLPAPERS / name / entry['file']
        entries.append(dict(entry, path=str(path), downloaded=path.is_file()))
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


def next_wallpaper(files, current):
    if not files:
        return None
    current = Path(current) if current else None
    if current in files:
        return files[(files.index(current) + 1) % len(files)]
    return files[0]


def memory():
    try:
        value = json.loads((STATE / 'wallpapers.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def remember(name, path):
    if path:
        write_atomic(STATE / 'wallpapers.json', json.dumps(dict(memory(), **{name: str(path)}), ensure_ascii=False) + '\n')


def current_wallpaper():
    try:
        return json.loads(SELECTION.read_text(encoding='utf-8')).get('source')
    except (OSError, ValueError, AttributeError):
        return None


# The remembered wallpaper while it still exists, else the first available one.
def wallpaper_for(name, theme):
    remembered = memory().get(name)
    if remembered and Path(remembered).is_file():
        return Path(remembered)
    files = wallpaper_files(name, theme)
    return files[0] if files else None


def apply_wallpaper(path):
    result = subprocess.run([sys.executable, str(WALLPAPER), str(path)], capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or str(path))


def download(entry, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=destination.parent, prefix='.' + destination.name + '.')
    digest = hashlib.sha256()
    try:
        with os.fdopen(handle, 'wb') as file, urllib.request.urlopen(entry['url'], timeout=30) as response:
            for block in iter(lambda: response.read(1024 * 1024), b''):
                digest.update(block)
                file.write(block)
        if digest.hexdigest() != entry['sha256']:
            raise ValueError(tr('theme.errors.checksum', [entry['file']]))
        os.chmod(temporary, 0o644)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


# Downloads what is missing, one JSON line per entry. With show, the theme's wallpaper is applied as soon
# as one is available, unless the user switched theme in the meantime.
def fetch(name, theme, show=False):
    shown = False
    def show_now():
        nonlocal shown
        if show and not shown and current() == name:
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
            download(entry, Path(entry['path']))
            print(json.dumps(dict(status, status='downloaded')), flush=True)
            show_now()
        except (OSError, ValueError) as error:
            failures += 1
            print(json.dumps(dict(status, status='failed', error=str(error)), ensure_ascii=False), flush=True)
    return failures


def spawn(arguments):
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'wallpapers.log').open('a') as log:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve())] + arguments, stdin=subprocess.DEVNULL,
                         stdout=log, stderr=log, start_new_session=True)


# Applications that do not watch their files are told to reload; missing ones are skipped.
def reload():
    for command in (['hyprctl', 'reload'], ['pkill', '-USR1', '-x', 'kitty'], ['pkill', '-USR2', '-x', 'btop']):
        try:
            subprocess.run(command, capture_output=True, check=False, timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('apply')
    choose = commands.add_parser('set')
    choose.add_argument('name')
    commands.add_parser('list')
    pack = commands.add_parser('wallpapers')
    pack.add_argument('name', nargs='?')
    getter = commands.add_parser('fetch')
    getter.add_argument('name', nargs='?')
    getter.add_argument('--show', action='store_true')
    commands.add_parser('next-wallpaper')
    preview = commands.add_parser('render')
    preview.add_argument('--theme', required=True)
    preview.add_argument('--out', required=True, type=Path)
    arguments = parser.parse_args()
    if arguments.command == 'apply':
        apply(current())
    elif arguments.command == 'set':
        previous = current()
        theme = apply(arguments.name)
        apply_vscode(theme)
        reload()
        # Colours switch at once; the wallpaper (a conversion, maybe a download) follows in the background.
        if previous != arguments.name:
            remember(previous, current_wallpaper())
            spawn(['fetch', arguments.name, '--show'])
    elif arguments.command == 'wallpapers':
        name = arguments.name or current()
        print(json.dumps({'theme': name, 'remembered': memory().get(name), 'current': current_wallpaper(),
                          'wallpapers': wallpaper_entries(name, load(name)),
                          'files': [str(path) for path in wallpaper_files(name, load(name))]}, ensure_ascii=False))
    elif arguments.command == 'fetch':
        name = arguments.name or current()
        return 1 if fetch(name, load(name), arguments.show) else 0
    elif arguments.command == 'next-wallpaper':
        name = current()
        theme = load(name)
        target = next_wallpaper(wallpaper_files(name, theme), current_wallpaper())
        if target is None:
            spawn(['fetch', name, '--show'])
            subprocess.run(['notify-send', tr('theme.wallpapers.title'), tr('theme.wallpapers.downloading', [theme.get('name', name)])],
                           check=False, timeout=5)
            return 0
        apply_wallpaper(target)
    elif arguments.command == 'list':
        print(json.dumps({'current': current(), 'themes': themes()}, ensure_ascii=False))
    else:
        for file, text in render_all(load(arguments.theme)).items():
            write_atomic(arguments.out / file, text)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

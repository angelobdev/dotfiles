#!/usr/bin/env python3
"""Render the desktop theme into the files the shell and applications read."""
from i18n import tr
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

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
    preview = commands.add_parser('render')
    preview.add_argument('--theme', required=True)
    preview.add_argument('--out', required=True, type=Path)
    arguments = parser.parse_args()
    if arguments.command == 'apply':
        apply(current())
    elif arguments.command == 'set':
        apply_vscode(apply(arguments.name))
        reload()
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

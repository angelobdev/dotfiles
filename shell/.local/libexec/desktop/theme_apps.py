"""The applications a theme reaches besides its templates: btop, Herdr, VS Code, GNOME's interface settings and
the cursor of the running Hyprland. Each one is best effort for theme.py (best_effort)."""
from common import write_atomic
import json
import re
import subprocess
import theme_core
import theme_paths


SCHEMA = 'org.gnome.desktop.interface'


def apply_cursor(theme):
    # Hyprland draws the cursor of every client that asks for a cursor shape (GTK 4, Qt 6): it takes the change
    # at once. Others read the environment (session.lua) or GSettings when they start.
    system = theme.get('system', {})
    if system.get('cursorTheme') and isinstance(system.get('cursorSize'), int):
        try:
            subprocess.run(['hyprctl', 'setcursor', system['cursorTheme'], str(system['cursorSize'])],
                           capture_output=True, check=False, timeout=5)
        except (OSError, subprocess.SubprocessError):
            pass


# btop rewrites btop.conf on exit, so it cannot be a stowed symlink: the theme goes into its themes
# directory as "desktop" and btop.conf only has its color_theme line pointed at it.
def apply_btop(text):
    config = theme_paths.BTOP / 'btop.conf'
    if text is None or not config.is_file():
        return
    write_atomic(theme_paths.BTOP / 'themes/desktop.theme', text)
    lines = config.read_text(encoding='utf-8').splitlines(keepends=True)
    wanted = 'color_theme = "desktop"\n'
    changed = [wanted if line.startswith('color_theme =') else line for line in lines]
    if not any(line.startswith('color_theme =') for line in lines):
        changed.append(wanted)
    if changed != lines:
        write_atomic(config, ''.join(changed))


def herdr_theme(theme):
    palette = theme['palette']
    hex6 = lambda value: '#' + theme_core.split_color(value, 'herdr')[0]
    colors = {
        'canvas': palette['base'], 'chrome': palette['base'], 'surface': palette['bg'], 'popover': palette['raised'],
        'raised': palette['raised'], 'hover': theme_core.mix(palette['raised'], palette['fg'], 0.08),
        'selected': theme_core.mix(palette['raised'], palette['accent'], 0.25), 'border': palette['border'],
        'input': theme_core.mix(palette['border'], palette['fg'], 0.2), 'muted': palette['muted'], 'dim': palette['dim'],
        'accent': palette['accent'], 'accent_foreground': palette['accentFg'], 'solid': palette['accent'],
        'solid_foreground': palette['accentFg'], 'working': palette['accent'], 'blocked': palette['danger'],
        'done': palette['success'],
    }
    return {
        'background': hex6(palette['bg']),
        'foreground': hex6(palette['fg']),
        # A background only: the text over it keeps its own color, so the accent is toned down to stay readable.
        'selection': theme_core.mix(palette['bg'], palette['accent'], 0.35),
        'cursor': hex6(palette['accent']),
        'ansi': [hex6(value) for value in theme['ansi'][:16]],
        'colors': {key: hex6(value) for key, value in colors.items()},
    }


def herdr_settings(current, wanted, last):
    # The new settings.json object: each wanted key set where it is unset or still the value written last time.
    updated = dict(current)
    for key, value in wanted.items():
        if key not in current or current[key] == last.get(key):
            updated[key] = value
    return updated


def apply_herdr(theme):
    if not theme_paths.HERDR.is_dir():
        return
    write_atomic(theme_paths.HERDR / 'themes/desktop.json', json.dumps(herdr_theme(theme), indent=2) + '\n')
    path = theme_paths.HERDR / 'settings.json'
    try:
        current = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    except (OSError, ValueError):
        return
    if not isinstance(current, dict):
        return
    fonts = theme.get('fonts', {})
    wanted = {'theme': 'desktop'}
    if fonts.get('mono'):
        wanted['font'] = fonts['mono']
        # Herdr sizes terminal text in pixels at zoom 1, the desktop in points.
        wanted['font_size'] = round(fonts.get('terminalSize', fonts.get('size', 11)) * 4 / 3)
    if fonts.get('sans'):
        wanted['ui_font'] = fonts['sans']
    try:
        last = json.loads((theme_paths.STATE / 'herdr-app.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        last = {}
    updated = herdr_settings(current, wanted, last if isinstance(last, dict) else {})
    if updated != current:
        write_atomic(path, json.dumps(updated, indent=2, ensure_ascii=False) + '\n')
    write_atomic(theme_paths.STATE / 'herdr-app.json', json.dumps(wanted, ensure_ascii=False) + '\n')


def extension_installed(extension):
    prefix = extension.lower() + '-'
    return theme_paths.VSCODE_EXTENSIONS.is_dir() and any(path.name.lower().startswith(prefix) for path in theme_paths.VSCODE_EXTENSIONS.iterdir())


# A targeted edit keeps the rest of settings.json, its order and formatting as VS Code wrote them.
def vscode_settings(text, key, colour_theme):
    value = json.dumps(colour_theme, ensure_ascii=False)
    pattern = re.compile('(' + re.escape(json.dumps(key)) + r'\s*:\s*)"(?:[^"\\]|\\.)*"')
    if pattern.search(text):
        updated = pattern.sub(lambda match: match[1] + value, text, count=1)
    else:
        opening = text.index('{') + 1
        # An empty object takes the key alone; a trailing comma would not be JSON.
        separator = '' if text[opening:].lstrip().startswith('}') else ','
        updated = text[:opening] + '\n    ' + json.dumps(key) + ': ' + value + separator + text[opening:]
    json.loads(updated)
    return updated


def apply_vscode(theme):
    settings = theme.get('vscode', {})
    colour_theme = settings.get('theme')
    if not colour_theme or not theme_paths.VSCODE.is_file():
        return
    if settings.get('extension') and not extension_installed(settings['extension']):
        return
    # With window.autoDetectColorScheme VS Code uses the preferred theme for the system mode instead.
    preferred = 'workbench.preferredLightColorTheme' if theme.get('mode') == 'light' else 'workbench.preferredDarkColorTheme'
    try:
        text = theme_paths.VSCODE.read_text(encoding='utf-8')
        json.loads(text)
        updated = text
        for key in ('workbench.colorTheme', preferred):
            updated = vscode_settings(updated, key, colour_theme)
    except ValueError:
        return
    if updated != text:
        write_atomic(theme_paths.VSCODE, updated)


# The keys of the schema with their values as gsettings prints them: a string without its quotes.
def gsettings_values(text):
    current = {}
    for line in text.splitlines():
        parts = line.split(' ', 2)
        if len(parts) == 3:
            value = parts[2]
            if len(value) >= 2 and value[0] == value[-1] == "'":
                value = value[1:-1].replace("\\'", "'")
            current[parts[1]] = value
    return current


def apply_gsettings(theme):
    # One call for the keys and their values; only a value that differs is set, so an apply that changes one
    # setting writes one key (each write makes running GTK apps re-read their settings).
    try:
        current = gsettings_values(subprocess.run(['gsettings', 'list-recursively', SCHEMA], capture_output=True, text=True,
                                                  check=True, timeout=5).stdout)
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
        if key in current and value not in (None, '') and current[key] != str(value):
            subprocess.run(['gsettings', 'set', SCHEMA, key, str(value)], check=False, timeout=5)

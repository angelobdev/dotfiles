#!/usr/bin/env python3
"""Render the desktop theme into the files the shell and applications read."""
from common import IMAGES, download as download_file, focused_monitor, install_command, magick, replacing, theme_name, write_atomic
from i18n import tr
import argparse
import colorsys
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import zipfile
import zlib

HOME = Path.home()
STATE = Path(os.environ.get('XDG_STATE_HOME') or HOME / '.local/state') / 'desktop-theme'
DATA = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'desktop'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'desktop'
# User themes override the ones shipped by the dotfiles.
THEME_DIRS = (CONFIG / 'themes', DATA / 'themes')
TEMPLATES = DATA / 'templates'
BTOP = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'btop'
# qtXct have no include: their whole config is rendered (fonts, icons, colours), like btop's theme.
QTCT = tuple(Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / f'{v}/{v}.conf' for v in ('qt5ct', 'qt6ct'))
ICON_DIRS = [Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'icons', HOME / '.icons'] + [
    Path(d) / 'icons' for d in (os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':') if d]
# Folder, terminal, browser, settings and document: enough to tell icon packs apart at a glance.
ICON_SAMPLES = ('folder', 'utilities-terminal', 'web-browser', 'preferences-system', 'text-x-generic')
VSCODE = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'Code/User/settings.json'
VSCODE_EXTENSIONS = HOME / '.vscode/extensions'
# Downloaded theme wallpapers live outside the repository; wallpaper.py owns applying them.
WALLPAPERS = DATA / 'wallpapers'
SELECTION = Path(os.environ.get('XDG_STATE_HOME') or HOME / '.local/state') / 'desktop-session/wallpaper/selection.json'
WALLPAPER = Path(__file__).resolve().with_name('wallpaper.py')
REQUIRED = ('bg', 'base', 'raised', 'border', 'fg', 'muted', 'dim', 'accent', 'accentFg', 'link', 'danger',
            'success', 'warning')
DEFAULT = 'graphite'
# The Hyprglass options of the "liquid" look that the Theming panel changes, per theme: option, default
# (the liquid preset in plugins.lua), minimum, maximum and step. A step of 1 is a whole number of px.
GLASS_TUNING = (('blur_strength', 0.45, 0.0, 2.0, 0.05), ('refraction_strength', 1.8, 0.0, 3.0, 0.05),
                ('chromatic_aberration', 0.5, 0.0, 1.0, 0.05), ('edge_thickness_px', 40, 0, 80, 1),
                ('edge_height', 60, 0, 120, 1), ('fresnel_reflection', 0.6, 0.0, 1.0, 0.05),
                ('specular_strength', 0.6, 0.0, 1.0, 0.05), ('bevel_strength', 0.5, 0.0, 1.0, 0.05),
                ('noise_strength', 0.0, 0.0, 0.5, 0.01))
GLASS_OPTIONS = {option: (default, low, high, step) for option, default, low, high, step in GLASS_TUNING}
# Window gaps: between windows and to the screen edges (Hyprland general.gaps_in / gaps_out).
WINDOW_KEYS = ('rounding', 'borderSize', 'gapsIn', 'gapsOut')
# {{ path }} or {{ path | filter }} or {{ path | filter:alpha }}; braces are free for CSS, Lua and JSON.
PLACEHOLDER = re.compile(r'\{\{\s*([A-Za-z0-9_.]+)\s*(?:\|\s*([a-z]+)(?::([0-9a-f]{2}))?\s*)?\}\}')
COLOR = re.compile(r'#([0-9a-f]{6})([0-9a-f]{2})?')
# A line break in a value would add lines to INI and conf outputs.
CONTROL = re.compile(r'[\x00-\x1f\x7f]')
SCHEMA = 'org.gnome.desktop.interface'


def split_color(value, path):
    match = COLOR.fullmatch(str(value))
    if not match:
        raise ValueError(tr('theme.errors.color', [path, value]))
    return match[1], match[2]


def convert(value, path, name, alpha):
    if isinstance(value, str) and CONTROL.search(value):
        raise ValueError(tr('theme.errors.control', [path]))
    if name is None:
        return str(value)
    # Quoted strings: a name with a quote or backslash stays one value instead of breaking (or extending) the file.
    if name == 'json':
        return json.dumps(str(value), ensure_ascii=False)
    if name == 'lua':
        return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'
    # true or false, as Lua and JSON both write it.
    if name == 'bool':
        return 'true' if value is True else 'false'
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
    # The terminal and the previews read 16 colours; a theme without them is invalid, not a crash later.
    if not isinstance(theme.get('ansi'), list) or len(theme['ansi']) != 16:
        raise ValueError(tr('theme.errors.invalid', [name, 'ansi']))
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
    # A light theme shades the bar with its own background, so its dark bar text stays readable.
    shade = palette['bg'] if theme.get('mode') == 'light' else '#000000'
    shade_top, shade_bottom = ('99', '88') if theme.get('mode') == 'light' else ('55', '44')
    for key, value in (('background', alpha(palette['bg'], 'f2')), ('surface', alpha(palette['bg'], 'd9')),
                       ('raised', alpha(palette['base'], 'e6')), ('tile', alpha(palette['raised'], 'e6')),
                       ('accentText', palette['accentFg']), ('track', alpha(mix(palette['dim'], palette['bg'], 0.3), '80')),
                       ('stroke', alpha(palette['fg'], '28')), ('text', palette['fg']), ('muted', palette['muted']),
                       ('accent', palette['accent']), ('danger', palette['danger']), ('scrim', '#00000014'),
                       ('scrimModal', '#00000099'), ('scrimStrong', '#000000bb'), ('tooltip', alpha(palette['raised'], 'f0')),
                       ('handlePressed', palette['brightText']), ('handleFocus', mix(palette['muted'], palette['dim'], 0.5)),
                       ('barShadeTop', alpha(shade, shade_top)), ('barShadeBottom', alpha(shade, shade_bottom)), ('shareShade', '#00000028')):
        shell.setdefault(key, value)
    # Popup notifications float over any content; a theme with very clear surfaces gives them more body.
    shell.setdefault('notice', shell['raised'])
    hyprland = theme.setdefault('hyprland', {})
    hyprland.setdefault('shadow', alpha(palette['shadow'], '66'))
    hyprland.setdefault('glassTint', alpha(palette['bg'], '22'))
    # The Hyprglass look: "desktop" is the restrained default, "liquid" the refractive one (plugins.lua).
    if hyprland.get('glassStyle') not in ('desktop', 'liquid'):
        hyprland['glassStyle'] = 'desktop'
    # Window borders take the theme colours; their width and the corner rounding are user preferences.
    hyprland.setdefault('activeBorder', palette['accent'])
    hyprland.setdefault('inactiveBorder', palette['border'])
    hyprland.setdefault('rounding', 16)
    hyprland.setdefault('borderSize', 0)
    hyprland.setdefault('gapsIn', 4)
    hyprland.setdefault('gapsOut', 4)
    theme.setdefault('terminal', {}).setdefault('opacity', 0.94)
    # Shell options the user sets in the Theming panel; these are the defaults.
    preferences = theme.setdefault('preferences', {})
    preferences.setdefault('iconSource', 'desktop')
    preferences.setdefault('barStyle', 'shade')
    preferences.setdefault('textScale', 1)
    # Reduce effects (Theming panel): no animations, blur, shadows or glass, and near-opaque shell surfaces.
    preferences.setdefault('reduceEffects', False)
    return theme


def themes(details=False):
    found = {}
    for directory in reversed(THEME_DIRS):
        for path in sorted(directory.glob('*/theme.json')):
            try:
                theme = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            found[path.parent.name] = {'id': path.parent.name, 'name': theme.get('name', path.parent.name),
                                       'mode': theme.get('mode', 'dark')}
            if details:
                try:
                    completed = load(path.parent.name)
                except ValueError:
                    del found[path.parent.name]
                    continue
                palette = completed['palette']
                found[path.parent.name]['preview'] = {key: palette[key] for key in ('bg', 'base', 'raised', 'border', 'fg', 'muted', 'accent', 'accentFg')}
                found[path.parent.name]['preview']['ansi'] = completed['ansi']
    return sorted(found.values(), key=lambda t: t['name'].lower())


def preferences():
    try:
        value = json.loads((STATE / 'preferences.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def glass_value(option, value):
    default, low, high, step = GLASS_OPTIONS[option]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    value = min(high, max(low, value))
    return int(round(value)) if step == 1 else round(value, 3)


# The glass tuning of one theme: its saved values over the defaults, each kept in its range.
def glass_tuning(name, chosen):
    saved = chosen.get('glass', {}).get(name, {})
    saved = saved if isinstance(saved, dict) else {}
    return {option: glass_value(option, saved.get(option, GLASS_OPTIONS[option][0])) for option in GLASS_OPTIONS}


def glass_tunable(theme):
    return theme.get('hyprland', {}).get('glassStyle') == 'liquid'


# Option names come from GLASS_OPTIONS and values are numbers, so the Lua table is safe to splice in.
def lua_table(values):
    if not values:
        return '{}'
    return '{ ' + ', '.join(f'{key} = {value!r}' for key, value in sorted(values.items())) + ' }'


# Fonts, icons and the bar style are the user's, across themes; whatever is unset keeps the theme's value.
# With the theme's name, a liquid glass theme also takes its own glass tuning.
def with_preferences(theme, chosen, name=None):
    theme = json.loads(json.dumps(theme))
    fonts = {key: value for key, value in chosen.get('fonts', {}).items() if value not in (None, '') and key != 'unified'}
    theme.setdefault('fonts', {}).update(fonts)
    # One font everywhere: the interface takes the monospace family.
    if chosen.get('fonts', {}).get('unified') and theme['fonts'].get('mono'):
        theme['fonts']['sans'] = theme['fonts']['mono']
    if theme_name(chosen.get('iconTheme')):
        theme.setdefault('system', {})['iconTheme'] = chosen['iconTheme']
    cursor = chosen.get('cursor', {})
    if theme_name(cursor.get('theme')):
        theme.setdefault('system', {})['cursorTheme'] = cursor['theme']
    if isinstance(cursor.get('size'), int):
        theme.setdefault('system', {})['cursorSize'] = cursor['size']
    for key, value in (('iconSource', chosen.get('shellIcons')), ('barStyle', chosen.get('barStyle')), ('textScale', chosen.get('textScale'))):
        if value:
            theme.setdefault('preferences', {})[key] = value
    if chosen.get('reduceEffects') is True:
        theme.setdefault('preferences', {})['reduceEffects'] = True
    for key in WINDOW_KEYS:
        if isinstance(chosen.get('windows', {}).get(key), int):
            theme.setdefault('hyprland', {})[key] = chosen['windows'][key]
    if name and glass_tunable(theme):
        theme['hyprland']['glassTuning'] = glass_tuning(name, chosen)
    return theme


def save_preferences(chosen):
    fonts = {key: value for key, value in chosen.get('fonts', {}).items() if value not in (None, '', False)}
    windows = {key: value for key, value in chosen.get('windows', {}).items() if isinstance(value, int)}
    # Only the mode is kept; a palette style saved by an older version is dropped.
    dynamic = {key: value for key, value in chosen.get('dynamic', {}).items() if key == 'mode' and value}
    # Only values that differ from the default are kept, so a reset theme leaves no entry.
    glass = {}
    for name, saved in chosen.get('glass', {}).items():
        if isinstance(saved, dict):
            values = {option: glass_value(option, value) for option, value in saved.items() if option in GLASS_OPTIONS}
            values = {option: value for option, value in values.items() if value != GLASS_OPTIONS[option][0]}
            if values:
                glass[name] = values
    cursor = {key: value for key, value in chosen.get('cursor', {}).items()
              if key == 'theme' and isinstance(value, str) and value or key == 'size' and isinstance(value, int)}
    cleaned = {key: value for key, value in (('fonts', fonts), ('iconTheme', chosen.get('iconTheme')), ('cursor', cursor),
                                              ('shellIcons', chosen.get('shellIcons')), ('barStyle', chosen.get('barStyle')),
                                              ('textScale', chosen.get('textScale') if chosen.get('textScale') in TEXT_SCALES[1:] else None),
                                              ('reduceEffects', chosen.get('reduceEffects') is True),
                                              ('windows', windows), ('dynamic', dynamic), ('glass', glass))
               if value}
    write_atomic(STATE / 'preferences.json', json.dumps(cleaned, ensure_ascii=False) + '\n')


SCRIPTS = re.compile(r'Emoji|Symbol|Math|Braille|Dingbat|Awesome|Icons|Fallback|Naskh|Kufi|CJK|Arabic|Armenian|Bengali|'
                     r'Canadian|Cherokee|Devanagari|Ethiopic|Georgian|Gothic|Gujarati|Gurmukhi|Hebrew|Kannada|Khmer|Lao|'
                     r'Meetei|NKo|Ol Chiki|Oriya|Sinhala|Syriac|Tamil|Telugu|Thaana|Thai|\bYi\b|PakType|RIT |Jomolhari|'
                     r'Madan|Padauk|Vazirmatn|Serif|Roman|Bookman|STIX|C059|P052|Z003|D050000L|Narrow|Caladea|Droid Sans ')


# fc-list lines of "family<TAB>spacing": 100 (or Mono in the name) is monospace, the rest interface fonts.
def font_families(lines):
    families = {'sans': set(), 'mono': set()}
    for line in lines:
        family, _, spacing = line.partition('\t')
        family = family.strip()
        if not family or SCRIPTS.search(family):
            continue
        # Variable fonts do not always declare their spacing, so the name counts too.
        families['mono' if spacing.strip() == '100' or re.search(r'\bMono\b', family) else 'sans'].add(family)
    return {kind: sorted(names, key=str.lower) for kind, names in families.items()}


USER_FONTS = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'fonts'
USER_ICONS = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'icons'


def fonts():
    result = subprocess.run(['fc-list', ':lang=en', '--format', '%{family[0]}\t%{spacing}\t%{file}\n'],
                            capture_output=True, text=True, check=True, timeout=20)
    lines, user = [], set()
    for line in result.stdout.splitlines():
        family, spacing, file = (line.split('\t') + ['', ''])[:3]
        lines.append(family + '\t' + spacing)
        # Fonts the user installed are always offered, whatever their name.
        if file.startswith(str(USER_FONTS) + '/') or file.startswith(str(HOME / '.fonts') + '/'):
            user.add((family.strip(), spacing.strip() == '100' or bool(re.search(r'\bMono\b', family))))
    families = font_families(lines)
    for family, mono in user:
        kind = 'mono' if mono else 'sans'
        if family and family not in families[kind]:
            families[kind] = sorted(families[kind] + [family], key=str.lower)
    name = current()
    own = load(name).get('fonts', {})
    effective = with_preferences(load(name), preferences()).get('fonts', {})
    return dict(families, theme=own, effective=effective, chosen=preferences().get('fonts', {}),
                folder=str(USER_FONTS))


def font_exists(family):
    result = subprocess.run(['fc-list', family, 'family'], capture_output=True, text=True, timeout=20)
    return result.returncode == 0 and result.stdout.strip() != ''


def icon_theme_exists(name):
    return theme_name(name) and bool(icon_theme_dirs(name, ICON_DIRS))


# Thumbnails make every format the gallery shows previewable (Qt lacks WebP here) and keep 8K
# wallpapers from being decoded at full size by the panel.
THUMBS = Path(os.environ.get('XDG_CACHE_HOME') or HOME / '.cache') / 'desktop-theme/thumbs'


def thumb_path(path):
    path = Path(path)
    try:
        info = path.stat()
        key = f'{path}\0{info.st_mtime_ns}\0{info.st_size}'
    except OSError:
        key = str(path)
    return THUMBS / (hashlib.sha1(key.encode()).hexdigest() + '.jpg')


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


def linear(channel):
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def contrast_ratio(first, second):
    high, low = max(first, second), min(first, second)
    return (high + 0.05) / (low + 0.05)


def relative_luminance(colour):
    rgb = split_color(colour, 'luminance')[0]
    red, green, blue = (linear(int(rgb[i:i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


# Bar text over the wallpaper strip: whichever of the theme's light and dark text colours contrasts more.
# The bar itself stays transparent; only text and icons change colour.
def bar_text(mean, light_text='#f0f0f2', dark_text='#191a1d'):
    background = linear(mean)
    light = contrast_ratio(relative_luminance(light_text), background)
    dark = contrast_ratio(relative_luminance(dark_text), background)
    return {'text': 'dark' if dark > light else 'light', 'contrast': round(max(light, dark), 2)}


def monitor_size():
    monitor = focused_monitor()
    try:
        scale = monitor.get('scale') or 1
        return round(monitor['width'] / scale), round(monitor['height'] / scale)
    except (AttributeError, KeyError, TypeError, ValueError):
        return 1920, 1080


# The strip under the bar of the current wallpaper as hyprpaper shows it (cover at the monitor size);
# cached per rendered file and size.
def tone():
    current_file = SELECTION.with_name('current.jpg')
    try:
        rendered = str(current_file.resolve(strict=True))
    except OSError:
        return dict(bar_text(0.0), mean=0.0)
    # The two text colours of the current theme, so the choice holds for every theme.
    shell = with_preferences(load(current()), preferences())['shell']
    light_text, dark_text = shell['text'], shell['accentText']
    width, height = monitor_size()
    key = f'{rendered}@{width}x{height}'
    cache = STATE / 'tone.json'
    try:
        stored = json.loads(cache.read_text(encoding='utf-8'))
        if stored.get('key') == key:
            return dict(bar_text(stored['mean'], light_text, dark_text), mean=stored['mean'])
    except (OSError, ValueError, KeyError):
        pass
    strip = max(1, round(height * 0.04))
    result = magick(rendered + '[0]', '-resize', f'{width}x{height}^', '-gravity', 'center', '-extent', f'{width}x{height}',
                    '-gravity', 'north', '-crop', f'{width}x{strip}+0+0', '+repage', '-colorspace', 'Gray',
                    '-format', '%[fx:mean]', 'info:', check=True)
    mean = round(float(result.stdout.strip()), 4)
    write_atomic(cache, json.dumps({'key': key, 'mean': mean}) + '\n')
    return dict(bar_text(mean, light_text, dark_text), mean=mean)


def read_index(path):
    sections, section = {}, None
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            section = sections.setdefault(line[1:-1], {})
        elif '=' in line and section is not None:
            key, _, value = line.partition('=')
            section[key.strip()] = value.strip()
    return sections


def icon_theme_dirs(name, roots):
    return [root / name for root in roots if (root / name / 'index.theme').is_file()]


# A Size that is not a plain number ("48px" in a downloaded pack) sorts last instead of failing the listing.
def index_size(section):
    size = section.get('Size', '').strip()
    return int(size) if size.isdigit() else 0


# Sample files resolved through the theme and its Inherits chain, so a preview shows that pack's icons.
def icon_samples(name, roots, names=ICON_SAMPLES):
    found, chain, seen = {}, [name], set()
    while chain:
        theme = chain.pop(0)
        # Every chain ends in hicolor, the fallback all icon themes share.
        if not chain and theme != 'hicolor' and 'hicolor' not in seen:
            chain.append('hicolor')
        if theme in seen:
            continue
        seen.add(theme)
        for base in icon_theme_dirs(theme, roots):
            index = read_index(base / 'index.theme')
            info = index.get('Icon Theme', {})
            directories = [d.strip() for d in info.get('Directories', '').split(',') if d.strip()]
            directories += [d.strip() for d in info.get('ScaledDirectories', '').split(',') if d.strip()]
            # Prefer scalable and large icons for a crisp preview.
            directories.sort(key=lambda d: (index.get(d, {}).get('Type') != 'Scalable', -index_size(index.get(d, {}))))
            for icon in names:
                if icon in found:
                    continue
                for directory in directories:
                    for extension in ('.svg', '.png'):
                        candidate = base / directory / (icon + extension)
                        if candidate.is_file():
                            found[icon] = str(candidate)
                            break
                    if icon in found:
                        break
            chain += [parent.strip() for parent in info.get('Inherits', '').split(',') if parent.strip()]
        if len(found) == len(names):
            break
    return [found.get(icon, '') for icon in names]


# Resolving samples walks every pack (about 2 s with Yaru's variants), so the result is cached until an
# icon directory changes.
def cached_icon_themes():
    # Bump the version when the discovery rules change.
    signature = [3] + [[str(root), root.stat().st_mtime] for root in ICON_DIRS if root.is_dir()]
    cache = STATE / 'icons-cache.json'
    try:
        stored = json.loads(cache.read_text(encoding='utf-8'))
        if stored.get('signature') == signature:
            return stored['themes']
    except (OSError, ValueError, AttributeError, KeyError):
        pass
    listed = icon_themes()
    write_atomic(cache, json.dumps({'signature': signature, 'themes': listed}, ensure_ascii=False))
    return listed


def icon_themes(roots=None):
    roots = roots or ICON_DIRS
    listed = {}
    for root in roots:
        if not root.is_dir():
            continue
        for base in sorted(root.iterdir()):
            index_file = base / 'index.theme'
            if base.name in listed or base.name in ('hicolor', 'default', 'locolor') or not theme_name(base.name) or not index_file.is_file():
                continue
            info = read_index(index_file).get('Icon Theme', {})
            # Hidden is not honoured: Fedora's Adwaita sets it, and the sample check below already drops
            # cursor-only and internal themes.
            if 'legacy' in base.name.lower():
                continue
            # One broken pack hides only itself.
            try:
                samples = icon_samples(base.name, roots)
            except (OSError, ValueError):
                continue
            # Cursor-only themes resolve nothing beyond hicolor. Adwaita draws folders and files but leaves
            # application icons to hicolor, so two samples of its own are enough.
            if sum(1 for sample in samples if sample and '/hicolor/' not in sample) < 2:
                continue
            listed[base.name] = {'id': base.name, 'name': info.get('Name', base.name), 'samples': samples}
    return sorted(listed.values(), key=lambda t: t['name'].lower())


# Text sizes of the shell offered, as factors of the drawn sizes (Theme.textSize in QML).
TEXT_SCALES = (1, 1.15, 1.3, 1.5)
# Cursor sizes offered, in logical pixels; Adwaita draws 24, 32, 48, 64 and 96, others scale the nearest.
CURSOR_SIZES = (24, 32, 40, 48)


# Cursor themes Fedora does not package, part of the desktop's set beside Adwaita and Breeze: pinned releases,
# checked by sha256, unpacked into ~/.local/share/icons. `apply` (every login) fetches the missing ones in the
# background; choosing one before that fetches it at once. member is the folder taken from the archive.
CURSOR_PACKS = {
    'macOS': {'name': 'macOS', 'file': 'macOS.tar.xz', 'member': 'macOS',
              'url': 'https://github.com/ful1e5/apple_cursor/releases/download/v2.0.1/macOS.tar.xz',
              'sha256': '9c6e5e13b068ce51a9e90a9abd6ce232ec7d25d4ceb05aa8ac76efbb99c76762'},
    'macOS-White': {'name': 'macOS White', 'file': 'macOS.tar.xz', 'member': 'macOS-White',
                    'url': 'https://github.com/ful1e5/apple_cursor/releases/download/v2.0.1/macOS.tar.xz',
                    'sha256': '9c6e5e13b068ce51a9e90a9abd6ce232ec7d25d4ceb05aa8ac76efbb99c76762'},
    'Bibata-Modern-Classic': {'name': 'Bibata Modern Classic', 'file': 'Bibata-Modern-Classic.tar.xz', 'member': 'Bibata-Modern-Classic',
                              'url': 'https://github.com/ful1e5/Bibata_Cursor/releases/download/v2.0.7/Bibata-Modern-Classic.tar.xz',
                              'sha256': '7d3495864e5bbef02f5e77de760b2905903b63c71495a78ef6306d19a3b556d8'},
    'Bibata-Modern-Ice': {'name': 'Bibata Modern Ice', 'file': 'Bibata-Modern-Ice.tar.xz', 'member': 'Bibata-Modern-Ice',
                          'url': 'https://github.com/ful1e5/Bibata_Cursor/releases/download/v2.0.7/Bibata-Modern-Ice.tar.xz',
                          'sha256': 'a68cae60c4dc706350e194ebc91c5fe48bc7bc9d59e119555834a2a7ee5078ef'},
}
CURSOR_DOWNLOADS = Path(os.environ.get('XDG_CACHE_HOME') or HOME / '.cache') / 'desktop/cursors'


def fetch_cursor(name):
    # One fetch at a time: the one apply starts at login and one from the panel would share the archive.
    CURSOR_DOWNLOADS.mkdir(parents=True, exist_ok=True)
    with open(CURSOR_DOWNLOADS / '.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Installed by the other one while this one waited.
        if (USER_ICONS / name / 'cursors').is_dir():
            return
        unpack_cursor(name)


def unpack_cursor(name):
    # The archive is kept, so the other variant of a pack (macOS, macOS White) needs no download. Only the pack's
    # own folder is unpacked, with tarfile's data filter: no links out of it, no devices, no absolute paths.
    pack = CURSOR_PACKS[name]
    archive = CURSOR_DOWNLOADS / pack['file']
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != pack['sha256']:
        download(pack, archive)
    # A folder of its own, hidden from the theme lists (a name starting with a dot is no theme name).
    USER_ICONS.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=USER_ICONS, prefix=f'.{name}.'))
    try:
        with tarfile.open(archive) as source:
            prefix = pack['member'].strip('/')
            members = [member for member in source.getmembers()
                       if member.name.lstrip('./') == prefix or member.name.lstrip('./').startswith(prefix + '/')]
            if not members:
                raise ValueError(tr('theme.errors.checksum', [pack['file']]))
            source.extractall(staging, members=members, filter='data')
        unpacked = staging / prefix
        target = USER_ICONS / name
        shutil.rmtree(target, ignore_errors=True)
        unpacked.rename(target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def fetch_missing_cursors():
    # The desktop's set, in the background after apply; one that fails is tried again at the next login.
    installed = {theme['id'] for theme in cursor_themes()}
    for name in CURSOR_PACKS:
        if name not in installed:
            try:
                fetch_cursor(name)
            except (OSError, ValueError, tarfile.TarError) as error:
                print(f'{name}: {error}', file=sys.stderr)


def cursor_themes(roots=None):
    # XCursor themes (a cursors folder) and hyprcursor ones (a manifest), by folder name; the "default" alias
    # only points at another theme.
    listed = {}
    for root in roots or ICON_DIRS:
        if not root.is_dir():
            continue
        for base in sorted(root.iterdir()):
            if base.name in listed or base.name == 'default' or not theme_name(base.name) or not ((base / 'cursors').is_dir() or (base / 'manifest.hl').is_file()):
                continue
            info = read_index(base / 'index.theme').get('Icon Theme', {}) if (base / 'index.theme').is_file() else {}
            listed[base.name] = {'id': base.name, 'name': info.get('Name', base.name)}
    return sorted(listed.values(), key=lambda t: t['name'].lower())


# The shapes a cursor preview shows: arrow, hand, text, busy and resize, each by its CSS name first and the
# X11 names older themes use.
CURSOR_SAMPLES = (('default', 'left_ptr', 'arrow'), ('pointer', 'hand2', 'hand1', 'pointing_hand'), ('text', 'xterm', 'ibeam'),
                  ('wait', 'watch'), ('ew-resize', 'sb_h_double_arrow', 'h_double_arrow', 'size_hor'))
CURSOR_PREVIEWS = Path(os.environ.get('XDG_CACHE_HOME') or HOME / '.cache') / 'desktop-theme/cursors'
# The largest image a preview takes: 48 logical pixels on a 2x screen.
CURSOR_PREVIEW_SIZE = 96
XCURSOR_IMAGE = 0xfffd0002


def png_bytes(width, height, rgba):
    # Enough PNG for a preview: 8-bit RGBA, no filtering.
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    stride = width * 4
    rows = b''.join(b'\0' + rgba[y * stride:(y + 1) * stride] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


def xcursor_png(data, largest=CURSOR_PREVIEW_SIZE):
    # The first frame of the largest nominal size up to `largest` (else the smallest), as PNG. Pixels are
    # premultiplied ARGB, little endian, which PNG wants straight.
    if data[:4] != b'Xcur' or len(data) < 16:
        raise ValueError('not an XCursor file')
    header, _version, count = struct.unpack_from('<III', data, 4)
    entries = []
    for index in range(count):
        offset = header + index * 12
        if offset + 12 > len(data):
            break
        kind, size, position = struct.unpack_from('<III', data, offset)
        if kind == XCURSOR_IMAGE:
            entries.append((size, position))
    if not entries:
        raise ValueError('no image in the XCursor file')
    fitting = [entry for entry in entries if entry[0] <= largest]
    size, position = max(fitting) if fitting else min(entries)
    if position + 36 > len(data):
        raise ValueError('truncated XCursor file')
    width, height = struct.unpack_from('<II', data, position + 16)
    if not (0 < width <= 1024 and 0 < height <= 1024) or position + 36 + width * height * 4 > len(data):
        raise ValueError('bad XCursor image')
    pixels = memoryview(data)[position + 36:position + 36 + width * height * 4]
    rgba = bytearray(width * height * 4)
    for index in range(width * height):
        b, g, r, a = pixels[index * 4:index * 4 + 4]
        if a:
            rgba[index * 4:index * 4 + 4] = bytes((min(255, r * 255 // a), min(255, g * 255 // a), min(255, b * 255 // a), a))
    return png_bytes(width, height, bytes(rgba))


def hyprcursor_image(path, largest=CURSOR_PREVIEW_SIZE):
    # A .hlc shape is a zip with meta.hl ("define_size = SIZE, FILE[, DELAY]", 0 for an SVG) and its images:
    # the SVG when there is one, else the largest PNG up to `largest`.
    with zipfile.ZipFile(path) as archive:
        sizes = []
        for line in archive.read('meta.hl').decode('utf-8', 'replace').splitlines():
            key, _, value = line.partition('=')
            if key.strip() == 'define_size':
                parts = [part.strip() for part in value.split(',')]
                if len(parts) >= 2 and parts[0].isdigit():
                    sizes.append((int(parts[0]), parts[1]))
        if not sizes:
            raise ValueError('no image in the hyprcursor shape')
        vector = [entry for entry in sizes if entry[0] == 0 or entry[1].lower().endswith('.svg')]
        fitting = [entry for entry in sizes if 0 < entry[0] <= largest]
        _size, name = vector[0] if vector else max(fitting) if fitting else min(sizes)
        return archive.read(name), Path(name).suffix.lower() or '.png'


def cursor_sample(base, names):
    # The preview of one shape, cached under the cursor file's path, size and time: '' when the theme lacks it.
    base = Path(base)
    candidates = [(base / 'cursors' / name, 'xcursor') for name in names]
    if (base / 'manifest.hl').is_file():
        folder = 'hyprcursors'
        for line in (base / 'manifest.hl').read_text(encoding='utf-8', errors='replace').splitlines():
            key, _, value = line.partition('=')
            if key.strip() == 'cursors_directory' and value.strip():
                folder = value.strip()
        candidates += [(base / folder / (name + '.hlc'), 'hyprcursor') for name in names]
    for path, kind in candidates:
        if not path.is_file():
            continue
        info = path.stat()
        key = hashlib.sha1(f'{path.resolve()}\0{info.st_mtime_ns}\0{info.st_size}'.encode()).hexdigest()
        cached = [CURSOR_PREVIEWS / (key + suffix) for suffix in ('.png', '.svg')]
        for target in cached:
            if target.is_file():
                return str(target)
        try:
            if kind == 'xcursor':
                image, suffix = xcursor_png(path.read_bytes()), '.png'
            else:
                image, suffix = hyprcursor_image(path)
        except (OSError, ValueError, KeyError, struct.error, zipfile.BadZipFile):
            continue
        target = CURSOR_PREVIEWS / (key + ('.svg' if suffix == '.svg' else '.png'))
        with replacing(target, suffix=target.suffix) as temporary:
            temporary.write_bytes(image)
        return str(target)
    return ''


def cursor_theme_dir(name, roots=None):
    # The folder cursor_themes() lists for this name: the first root wins, as there.
    for root in roots or ICON_DIRS:
        base = root / name
        if (base / 'cursors').is_dir() or (base / 'manifest.hl').is_file():
            return base
    return None


def cursor_samples(base):
    # One broken file hides only its own shape.
    return [cursor_sample(base, names) for names in CURSOR_SAMPLES]


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


def render_all(theme, templates=TEMPLATES):
    # Paths a template may need besides the theme itself, and sizes derived from the window rounding
    # (16 is the design size, so the lock screen field keeps its 26 px corners by default).
    scale = max(0, theme.get('hyprland', {}).get('rounding', 16)) / 16
    # Text the templates show (the lock screen), in the session language.
    strings = {'lockPassword': tr('lockScreen.password'), 'lockFingerprintReady': tr('lockScreen.fingerprintReady'),
               'lockFingerprintPresent': tr('lockScreen.fingerprintPresent')}
    derived = {'lockRounding': round(26 * scale), 'glassTuning': lua_table(theme.get('hyprland', {}).get('glassTuning', {}))}
    theme = dict(theme, paths={'state': str(STATE)}, derived=derived, strings=strings)
    outputs = {}
    for path in sorted(templates.glob('*.tpl')):
        outputs[path.stem] = render(path.read_text(encoding='utf-8'), theme, path.name)
    return outputs


DYNAMIC = 'dynamic'
MODES = {'auto': 'smart', 'dark': 'dark', 'light': 'light'}
# GNOME accent colours by hue, for the GSettings accent of a generated theme.
GNOME_ACCENTS = (('red', 0), ('orange', 30), ('yellow', 55), ('green', 120), ('teal', 180), ('blue', 215),
                 ('purple', 275), ('pink', 330), ('red', 360))
# Terminal hues in ANSI order (red, green, yellow, blue, magenta, cyan). matugen's base16 colours are the
# image's own, in no hue order, so a brown painting would give a brown red and a brown green.
ANSI_HUES = (4, 130, 45, 215, 300, 185)


def to_rgb(colour):
    rgb = split_color(colour, 'colour')[0]
    return tuple(int(rgb[i:i + 2], 16) / 255 for i in (0, 2, 4))


def to_hex(rgb):
    return '#' + ''.join('%02x' % round(max(0, min(1, channel)) * 255) for channel in rgb)


# Moves a colour's lightness away from the background until it reaches the contrast.
def readable(colour, background, minimum):
    hue, lightness, saturation = colorsys.rgb_to_hls(*to_rgb(colour))
    step = 0.02 if relative_luminance(background) < 0.18 else -0.02
    for _ in range(50):
        candidate = to_hex(colorsys.hls_to_rgb(hue, lightness, saturation))
        if contrast_ratio(relative_luminance(candidate), relative_luminance(background)) >= minimum:
            return candidate
        lightness = max(0.0, min(1.0, lightness + step))
    return candidate


# A standard hue turned up to 15 degrees toward the primary, as Material harmonizes custom colours, so the
# terminal colours stay recognisable and still belong to the image.
def harmonized(hue, primary, saturation, lightness):
    target = colorsys.rgb_to_hls(*to_rgb(primary))[0] * 360
    difference = (target - hue + 180) % 360 - 180
    rotation = max(-15, min(15, difference * 0.5))
    return to_hex(colorsys.hls_to_rgb(((hue + rotation) % 360) / 360, lightness, saturation))


def nearest_accent(colour):
    hue, lightness, saturation = colorsys.rgb_to_hls(*to_rgb(colour))
    if saturation < 0.18:
        return 'slate'
    degrees = hue * 360
    return min(GNOME_ACCENTS, key=lambda accent: abs(accent[1] - degrees))[0]


# matugen JSON (4.x: colors/base16 -> {dark, light, default: {color}}) -> a theme.json for this desktop.
def dynamic_theme(data, source):
    dark = (data.get('mode') or ('dark' if data.get('is_dark_mode', True) else 'light')) == 'dark'
    def role(name):
        return data['colors'][name]['default']['color'].lower()
    palette = {
        'bg': role('surface'),
        'base': role('surface_container_lowest' if dark else 'surface_container_low'),
        'raised': role('surface_container_high'),
        'border': role('outline_variant'),
        'fg': role('on_surface'),
        'muted': role('on_surface_variant'),
        'dim': role('outline'),
        'accent': role('primary'),
        'accentFg': role('on_primary'),
        'link': role('tertiary'),
        'danger': role('error'),
    }
    background, primary = palette['bg'], palette['accent']
    normal = [readable(harmonized(hue, primary, 0.55, 0.62 if dark else 0.42), background, 3) for hue in ANSI_HUES]
    bright = [readable(harmonized(hue, primary, 0.65, 0.72 if dark else 0.34), background, 4.5) for hue in ANSI_HUES]
    palette['success'], palette['warning'] = bright[1], bright[2]
    # Black and white ends follow the surfaces: dark themes keep the usual order, light ones invert it.
    if dark:
        ansi = [palette['raised']] + normal + [palette['muted'], palette['dim']] + bright + [palette['fg']]
    else:
        ansi = [palette['muted']] + normal + [palette['border'], palette['dim']] + bright + [palette['raised']]
    return {
        'name': 'Dynamic',
        'mode': 'dark' if dark else 'light',
        'source': str(source),
        'fonts': {'sans': 'Adwaita Sans', 'mono': 'Adwaita Mono', 'size': 10, 'terminalSize': 11},
        'system': {'gtkTheme': 'adw-gtk3-dark' if dark else 'adw-gtk3', 'iconTheme': 'Papirus-Dark' if dark else 'Papirus-Light',
                   'cursorTheme': 'Adwaita', 'cursorSize': 24, 'accentColor': nearest_accent(palette['accent'])},
        'palette': palette,
        'ansi': ansi,
        'terminal': {'opacity': 0.94},
        'wallpaperDirectories': [str(Path(source).parent)],
        'vscode': {'theme': 'Default Dark Modern' if dark else 'Default Light Modern'},
    }


def run_matugen(image, chosen):
    if shutil.which('matugen') is None:
        raise ValueError(tr('theme.errors.matugenMissing', [install_command(['matugen'])]))
    settings = chosen.get('dynamic', {})
    mode = MODES.get(settings.get('mode', 'auto'), 'smart')
    # Tonal spot, matugen's default: the other styles mostly moved the accent and were dropped.
    result = subprocess.run(['matugen', 'image', str(image), '--json', 'hex', '--dry-run', '-m', mode, '-t',
                             'scheme-tonal-spot', '--source-color-index', '0'], capture_output=True, text=True,
                            timeout=60)
    if result.returncode != 0:
        raise ValueError(tr('theme.errors.matugenFailed', [result.stderr.strip()[:300]]))
    # The JSON document is the whole output; anything before its first brace is a log line.
    return json.loads(result.stdout[result.stdout.index('{'):])


# Generates the dynamic theme from an image (the current wallpaper by default) and switches to it.
def generate(image=None):
    image = Path(image or current_wallpaper() or '')
    if not image.is_file():
        raise ValueError(tr('theme.errors.noWallpaper'))
    theme = dynamic_theme(run_matugen(image, preferences()), image)
    write_atomic(CONFIG / 'themes' / DYNAMIC / 'theme.json', json.dumps(theme, indent=2, ensure_ascii=False) + '\n')
    previous = current()
    applied = apply(DYNAMIC)
    best_effort(apply_vscode, applied)
    reload()
    if previous != DYNAMIC:
        remember(previous, wallpaper_chosen_under(previous))
    remember(DYNAMIC, image)
    if Path(current_wallpaper() or '') != image:
        apply_wallpaper(image)


def dynamic_info():
    try:
        source = json.loads((CONFIG / 'themes' / DYNAMIC / 'theme.json').read_text(encoding='utf-8')).get('source')
    except (OSError, ValueError, AttributeError):
        source = None
    settings = preferences().get('dynamic', {})
    return {'available': shutil.which('matugen') is not None, 'mode': settings.get('mode', 'auto'), 'source': source,
            'install': install_command(['matugen'])}


# A destination that is still an old Stow link is replaced, never written through into the repository.
def install(path, text):
    write_atomic(path, text, follow=False)


# A saved theme that no longer exists (removed by hand, a deleted dynamic theme) falls back to the default,
# so the session still renders and the panel can still list themes.
def current():
    try:
        name = json.loads((STATE / 'current.json').read_text(encoding='utf-8')).get('theme')
    except (OSError, ValueError, AttributeError):
        name = None
    if isinstance(name, str) and name:
        try:
            theme_path(name)
            return name
        except ValueError:
            pass
    return DEFAULT


# An app integration that fails (a hung dconf, an unwritable btop folder, a Herdr file it cannot read) is
# reported and skipped: the theme itself is written by then, and the rest of the switch (the reloads, the
# remembered wallpaper) must still happen. The reason goes to stderr, which the panel shows only on a failure.
def best_effort(step, *args):
    try:
        step(*args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'{step.__name__}: {error}', file=sys.stderr)


# Everything is rendered before anything is written, so a template error leaves the old theme intact.
def apply(name):
    theme = with_preferences(load(name), preferences(), name)
    outputs = render_all(theme)
    for file, text in outputs.items():
        write_atomic(STATE / file, text)
    write_atomic(STATE / 'current.json', json.dumps({'theme': name}, ensure_ascii=False) + '\n')
    if 'qtct.conf' in outputs:
        for config in QTCT:
            install(config, outputs['qtct.conf'])
    best_effort(apply_btop, outputs.get('btop.theme'))
    best_effort(apply_herdr, complete(theme))
    best_effort(apply_gsettings, theme)
    best_effort(apply_cursor, theme)
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


# The Herdr app (herdr.dev) redraws itself from files in ~/.config/herdr-app: the desktop theme becomes its theme
# "desktop" (themes/desktop.json, terminal and panel colors), and settings.json points at it with the desktop's
# fonts. A key of settings.json is changed only while it is unset or still what was written here last
# (STATE/herdr-app.json): a theme or font picked in Herdr itself stays. A settings.json that does not parse is
# left alone. Herdr reloads both live.
HERDR = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'herdr-app'


def herdr_theme(theme):
    palette = theme['palette']
    hex6 = lambda value: '#' + split_color(value, 'herdr')[0]
    colors = {
        'canvas': palette['base'], 'chrome': palette['base'], 'surface': palette['bg'], 'popover': palette['raised'],
        'raised': palette['raised'], 'hover': mix(palette['raised'], palette['fg'], 0.08),
        'selected': mix(palette['raised'], palette['accent'], 0.25), 'border': palette['border'],
        'input': mix(palette['border'], palette['fg'], 0.2), 'muted': palette['muted'], 'dim': palette['dim'],
        'accent': palette['accent'], 'accent_foreground': palette['accentFg'], 'solid': palette['accent'],
        'solid_foreground': palette['accentFg'], 'working': palette['accent'], 'blocked': palette['danger'],
        'done': palette['success'],
    }
    return {
        'background': hex6(palette['bg']),
        'foreground': hex6(palette['fg']),
        # A background only: the text over it keeps its own color, so the accent is toned down to stay readable.
        'selection': mix(palette['bg'], palette['accent'], 0.35),
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
    if not HERDR.is_dir():
        return
    write_atomic(HERDR / 'themes/desktop.json', json.dumps(herdr_theme(theme), indent=2) + '\n')
    path = HERDR / 'settings.json'
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
        last = json.loads((STATE / 'herdr-app.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        last = {}
    updated = herdr_settings(current, wanted, last if isinstance(last, dict) else {})
    if updated != current:
        write_atomic(path, json.dumps(updated, indent=2, ensure_ascii=False) + '\n')
    write_atomic(STATE / 'herdr-app.json', json.dumps(wanted, ensure_ascii=False) + '\n')


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
        # An empty object takes the key alone; a trailing comma would not be JSON.
        separator = '' if text[opening:].lstrip().startswith('}') else ','
        updated = text[:opening] + '\n    ' + json.dumps(key) + ': ' + value + separator + text[opening:]
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


def wallpaper_entries(name, theme):
    entries = []
    for entry in theme.get('wallpapers', []):
        path = WALLPAPERS / name / entry['file']
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


# The current wallpaper when it was chosen under the theme name. Switching away from a theme before its own
# wallpaper landed (a conversion or download still running, or offline) leaves the previous theme's image on
# screen, which is not this theme's. A selection from before wallpaper.py noted the theme counts as its.
def wallpaper_chosen_under(name):
    try:
        selection = json.loads(SELECTION.read_text(encoding='utf-8'))
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
    result = subprocess.run([sys.executable, str(WALLPAPER), str(path)], capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or str(path))


def download(entry, destination):
    download_file(entry['url'], destination, entry['sha256'], mismatch=tr('theme.errors.checksum', [entry['file']]))


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


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('apply')
    commands.add_parser('herdr')
    choose = commands.add_parser('set')
    choose.add_argument('name')
    listing = commands.add_parser('list')
    listing.add_argument('--details', action='store_true')
    commands.add_parser('fonts')
    commands.add_parser('icons')
    font = commands.add_parser('font')
    font.add_argument('--sans')
    font.add_argument('--mono')
    font.add_argument('--size', type=int)
    font.add_argument('--default', action='store_true')
    cursor = commands.add_parser('cursor')
    cursor.add_argument('--theme', help='an installed cursor theme, or default')
    cursor.add_argument('--size', type=int, choices=CURSOR_SIZES)
    cursor.add_argument('--default', action='store_true', help='back to the theme values')
    commands.add_parser('cursors')
    commands.add_parser('cursor-fetch')
    icons = commands.add_parser('icon-theme')
    icons.add_argument('name')
    keep = commands.add_parser('remember-wallpaper')
    keep.add_argument('path', type=Path)
    font.add_argument('--unified', choices=('on', 'off'))
    shell_icons = commands.add_parser('shell-icons')
    shell_icons.add_argument('source', choices=('desktop', 'pack'))
    generator = commands.add_parser('generate')
    generator.add_argument('--image', type=Path)
    dynamic = commands.add_parser('dynamic')
    dynamic.add_argument('--mode', choices=tuple(MODES))
    windows = commands.add_parser('window-style')
    windows.add_argument('--rounding', type=int, choices=range(0, 33), metavar='0-32')
    windows.add_argument('--border', type=int, choices=range(0, 9), metavar='0-8')
    windows.add_argument('--gaps-in', type=int, choices=range(0, 25), metavar='0-24')
    windows.add_argument('--gaps-out', type=int, choices=range(0, 49), metavar='0-48')
    windows.add_argument('--default', action='store_true')
    glass = commands.add_parser('glass')
    glass.add_argument('--option', choices=tuple(GLASS_OPTIONS))
    glass.add_argument('--value', type=float)
    glass.add_argument('--reset', action='store_true')
    text_scale = commands.add_parser('text-scale')
    text_scale.add_argument('scale', type=float, choices=TEXT_SCALES)
    effects = commands.add_parser('reduce-effects')
    effects.add_argument('action', choices=('on', 'off', 'toggle'))
    bar = commands.add_parser('bar-style')
    bar.add_argument('style', choices=('shade', 'transparent', 'toggle'))
    commands.add_parser('tone')
    thumbs = commands.add_parser('thumbs')
    thumbs.add_argument('name', nargs='?')
    check_font = commands.add_parser('check-font')
    check_font.add_argument('family')
    check_icons = commands.add_parser('check-icons')
    check_icons.add_argument('name')
    folder = commands.add_parser('open-folder')
    folder.add_argument('kind', choices=('fonts', 'icons'))
    pack = commands.add_parser('wallpapers')
    pack.add_argument('name', nargs='?')
    getter = commands.add_parser('fetch')
    getter.add_argument('name', nargs='?')
    getter.add_argument('--show', action='store_true')
    commands.add_parser('next-wallpaper')
    preview = commands.add_parser('render')
    preview.add_argument('--theme', required=True)
    preview.add_argument('--out', required=True, type=Path)
    return parser


# Commands that change the theme state run one at a time: the panel queue and DynamicTheme.qml can overlap,
# and each rewrites current.json, preferences.json and the rendered files.
LOCKED = {'apply', 'herdr', 'set', 'generate', 'dynamic', 'window-style', 'font', 'icon-theme', 'cursor', 'shell-icons',
          'bar-style', 'glass', 'text-scale', 'reduce-effects'}


# Read the preferences, change them, save them and apply the current theme with them.
def update_preferences(change, reloading=True):
    chosen = preferences()
    change(chosen)
    save_preferences(chosen)
    apply(current())
    if reloading:
        reload()


def command_apply(arguments):
    apply(current())
    if not set(CURSOR_PACKS) <= {theme['id'] for theme in cursor_themes()}:
        spawn(['cursor-fetch'])


# Herdr before its first start, which has no folder yet: the current theme goes there, so it opens in it.
def command_herdr(arguments):
    HERDR.mkdir(parents=True, exist_ok=True)
    name = current()
    apply_herdr(complete(with_preferences(load(name), preferences(), name)))


def command_cursor_fetch(arguments):
    fetch_missing_cursors()


def command_set(arguments):
    previous = current()
    theme = apply(arguments.name)
    best_effort(apply_vscode, theme)
    reload()
    # Colours switch at once; the wallpaper (a conversion, maybe a download) follows in the background.
    if previous != arguments.name:
        remember(previous, wallpaper_chosen_under(previous))
        spawn(['fetch', arguments.name, '--show'])


def command_wallpapers(arguments):
    name = arguments.name or current()
    theme = load(name)
    files = wallpaper_files(name, theme)
    print(json.dumps({'theme': name, 'remembered': memory().get(name), 'current': current_wallpaper(),
                      'wallpapers': wallpaper_entries(name, theme), 'files': [str(path) for path in files],
                      'thumbs': {str(path): str(thumb_path(path)) for path in files},
                      'thumbsReady': {str(path): thumb_path(path).is_file() for path in files}}, ensure_ascii=False))


def command_thumbs(arguments):
    name = arguments.name or current()
    make_thumbs([path for path in wallpaper_files(name, load(name)) if not thumb_path(path).is_file()])


def command_open_folder(arguments):
    target = USER_FONTS if arguments.kind == 'fonts' else USER_ICONS
    target.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(['xdg-open', str(target)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


def command_tone(arguments):
    print(json.dumps(tone()))


def command_check_font(arguments):
    if not font_exists(arguments.family):
        raise ValueError(tr('theming.errors.fontMissing', [arguments.family]))


def command_check_icons(arguments):
    if not icon_theme_exists(arguments.name):
        raise ValueError(tr('theming.errors.iconsMissing', [arguments.name]))


def command_generate(arguments):
    generate(arguments.image)


def command_dynamic(arguments):
    chosen = preferences()
    settings = dict(chosen.get('dynamic', {}))
    if arguments.mode:
        settings['mode'] = arguments.mode
    chosen['dynamic'] = settings
    save_preferences(chosen)
    # The new mode shows at once when the dynamic theme is the current one.
    if current() == DYNAMIC:
        generate(dynamic_info()['source'])


def command_window_style(arguments):
    def change(chosen):
        windows = {} if arguments.default else dict(chosen.get('windows', {}))
        for key, value in (('rounding', arguments.rounding), ('borderSize', arguments.border),
                           ('gapsIn', arguments.gaps_in), ('gapsOut', arguments.gaps_out)):
            if value is not None:
                windows[key] = value
        chosen['windows'] = windows
    update_preferences(change)


def command_glass(arguments):
    # The glass of the current theme; only Hyprland rereads it.
    name = current()
    if not glass_tunable(load(name)):
        raise ValueError(tr('theme.errors.glassUntunable', [load(name).get('name', name)]))
    chosen = preferences()
    glass = dict(chosen.get('glass', {}))
    if arguments.reset:
        glass.pop(name, None)
    elif arguments.option and arguments.value is not None:
        glass[name] = dict(glass.get(name, {}), **{arguments.option: arguments.value})
    chosen['glass'] = glass
    save_preferences(chosen)
    apply(name)
    subprocess.run(['hyprctl', 'reload'], capture_output=True, check=False, timeout=10)


def command_text_scale(arguments):
    update_preferences(lambda chosen: chosen.update(textScale=None if arguments.scale == 1 else arguments.scale), reloading=False)


def command_shell_icons(arguments):
    update_preferences(lambda chosen: chosen.update(shellIcons=None if arguments.source == 'desktop' else arguments.source), reloading=False)


# Hyprland reloads (animations, blur, shadows, glass in appearance.lua and plugins.lua); the shell follows
# quickshell.json by itself.
def command_reduce_effects(arguments):
    def change(chosen):
        reduced = not chosen.get('reduceEffects') if arguments.action == 'toggle' else arguments.action == 'on'
        chosen['reduceEffects'] = reduced or None
    update_preferences(change)


def command_bar_style(arguments):
    def change(chosen):
        style = arguments.style
        if style == 'toggle':
            style = 'shade' if chosen.get('barStyle') == 'transparent' else 'transparent'
        chosen['barStyle'] = None if style == 'shade' else style
    update_preferences(change, reloading=False)


def command_fetch(arguments):
    name = arguments.name or current()
    return 1 if fetch(name, load(name), arguments.show) else 0


def command_next_wallpaper(arguments):
    name = current()
    theme = load(name)
    target = next_wallpaper(wallpaper_files(name, theme), current_wallpaper())
    if target is None:
        spawn(['fetch', name, '--show'])
        subprocess.run(['notify-send', tr('theme.wallpapers.title'), tr('theme.wallpapers.downloading', [theme.get('name', name)])],
                       check=False, timeout=5)
        return 0
    apply_wallpaper(target)


def command_list(arguments):
    name = current()
    effective = with_preferences(load(name), preferences(), name)['hyprland']
    glass = None
    if 'glassTuning' in effective:
        glass = [{'option': option, 'value': effective['glassTuning'][option], 'default': default, 'min': low,
                  'max': high, 'step': step} for option, default, low, high, step in GLASS_TUNING]
    print(json.dumps({'current': name, 'themes': themes(arguments.details),
                      'windows': {key: effective[key] for key in WINDOW_KEYS},
                      'glass': glass, 'dynamic': dynamic_info()},
                     ensure_ascii=False))


def command_fonts(arguments):
    print(json.dumps(fonts(), ensure_ascii=False))


def command_icons(arguments):
    print(json.dumps({'themes': cached_icon_themes(), 'theme': load(current()).get('system', {}).get('iconTheme'),
                      'chosen': preferences().get('iconTheme')}, ensure_ascii=False))


def command_cursors(arguments):
    chosen = preferences()
    system = with_preferences(load(current()), chosen).get('system', {})
    installed = cursor_themes()
    # Each installed theme with its preview shapes (cursor_samples); a pack still to download has none yet.
    offered = [dict(theme, samples=cursor_samples(cursor_theme_dir(theme['id']))) for theme in installed]
    offered += [{'id': key, 'name': pack['name'], 'download': True, 'samples': []} for key, pack in CURSOR_PACKS.items()
                if key not in {theme['id'] for theme in installed}]
    print(json.dumps({'themes': sorted(offered, key=lambda t: t['name'].lower()), 'theme': system.get('cursorTheme'), 'size': system.get('cursorSize'),
                      'sizes': list(CURSOR_SIZES), 'chosen': chosen.get('cursor', {})}, ensure_ascii=False))


def command_cursor(arguments):
    def change(chosen):
        cursor = {} if arguments.default else dict(chosen.get('cursor', {}))
        if arguments.theme is not None:
            if arguments.theme in CURSOR_PACKS and arguments.theme not in {t['id'] for t in cursor_themes()}:
                fetch_cursor(arguments.theme)
            if arguments.theme != 'default' and arguments.theme not in {t['id'] for t in cursor_themes()}:
                raise ValueError(tr('theming.errors.cursorMissing', [arguments.theme]))
            cursor['theme'] = None if arguments.theme == 'default' else arguments.theme
        if arguments.size is not None:
            cursor['size'] = arguments.size
        chosen['cursor'] = cursor
    update_preferences(change)
    # X11 clients take theme and scaled size from X resources.
    subprocess.run([str(HOME / '.local/bin/desktop-xwayland'), 'apply'], capture_output=True, check=False, timeout=15)


def command_font(arguments):
    def change(chosen):
        chosen_fonts = {} if arguments.default else dict(chosen.get('fonts', {}))
        for key, value in (('sans', arguments.sans), ('mono', arguments.mono), ('size', arguments.size)):
            if value is not None:
                chosen_fonts[key] = value
        if arguments.unified is not None:
            chosen_fonts['unified'] = arguments.unified == 'on'
        chosen['fonts'] = chosen_fonts
    update_preferences(change)


def command_icon_theme(arguments):
    if arguments.name != 'default' and not icon_theme_exists(arguments.name):
        raise ValueError(tr('theming.errors.iconsMissing', [arguments.name]))
    update_preferences(lambda chosen: chosen.update(iconTheme=None if arguments.name == 'default' else arguments.name))


def command_remember_wallpaper(arguments):
    remember(current(), arguments.path.expanduser().resolve())


def command_render(arguments):
    for file, text in render_all(load(arguments.theme)).items():
        write_atomic(arguments.out / file, text)


# One function per command, by its name on the command line ('cursor-fetch' runs command_cursor_fetch).
COMMANDS = {name.removeprefix('command_').replace('_', '-'): function for name, function in list(globals().items())
            if name.startswith('command_') and callable(function)}


def main():
    arguments = build_parser().parse_args()
    if arguments.command in LOCKED:
        STATE.mkdir(parents=True, exist_ok=True)
        lock = open(STATE / '.lock', 'a')
        fcntl.flock(lock, fcntl.LOCK_EX)
    return COMMANDS[arguments.command](arguments) or 0

# The line the panel shows for a failed command. A ValueError raised here on purpose is translated already;
# anything else (a full disk, a file that is not JSON, a command that failed) is said in the catalog's words,
# with the system's own as the detail.
def failure_message(error):
    if isinstance(error, ValueError) and not isinstance(error, (json.JSONDecodeError, UnicodeDecodeError)):
        return str(error)
    return tr('theme.errors.failed', [error])


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(failure_message(error), file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""Render the desktop theme into the files the shell and applications read."""
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
# qtXct have no include: their whole config is rendered (fonts, icons, colours), like btop's theme.
QTCT = tuple(Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / f'{v}/{v}.conf' for v in ('qt5ct', 'qt6ct'))
ICON_DIRS = [HOME / '.local/share/icons', HOME / '.icons'] + [
    Path(d) / 'icons' for d in (os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':') if d]
# Folder, terminal, browser, settings and document: enough to tell icon packs apart at a glance.
ICON_SAMPLES = ('folder', 'utilities-terminal', 'web-browser', 'preferences-system', 'text-x-generic')
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
    hyprland = theme.setdefault('hyprland', {})
    hyprland.setdefault('shadow', alpha(palette['shadow'], '66'))
    hyprland.setdefault('glassTint', alpha(palette['bg'], '22'))
    # Window borders take the theme colours; their width and the corner rounding are user preferences.
    hyprland.setdefault('activeBorder', palette['accent'])
    hyprland.setdefault('inactiveBorder', palette['border'])
    hyprland.setdefault('rounding', 16)
    hyprland.setdefault('borderSize', 0)
    theme.setdefault('terminal', {}).setdefault('opacity', 0.94)
    # Shell options the user sets in the Theming panel; these are the defaults.
    preferences = theme.setdefault('preferences', {})
    preferences.setdefault('iconSource', 'desktop')
    preferences.setdefault('barStyle', 'shade')
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


# Fonts, icons and the bar style are the user's, across themes; whatever is unset keeps the theme's value.
def with_preferences(theme, chosen):
    theme = json.loads(json.dumps(theme))
    fonts = {key: value for key, value in chosen.get('fonts', {}).items() if value not in (None, '') and key != 'unified'}
    theme.setdefault('fonts', {}).update(fonts)
    # One font everywhere: the interface takes the monospace family.
    if chosen.get('fonts', {}).get('unified') and theme['fonts'].get('mono'):
        theme['fonts']['sans'] = theme['fonts']['mono']
    if chosen.get('iconTheme'):
        theme.setdefault('system', {})['iconTheme'] = chosen['iconTheme']
    for key, value in (('iconSource', chosen.get('shellIcons')), ('barStyle', chosen.get('barStyle'))):
        if value:
            theme.setdefault('preferences', {})[key] = value
    for key in ('rounding', 'borderSize'):
        if isinstance(chosen.get('windows', {}).get(key), int):
            theme.setdefault('hyprland', {})[key] = chosen['windows'][key]
    return theme


def save_preferences(chosen):
    fonts = {key: value for key, value in chosen.get('fonts', {}).items() if value not in (None, '', False)}
    windows = {key: value for key, value in chosen.get('windows', {}).items() if isinstance(value, int)}
    dynamic = {key: value for key, value in chosen.get('dynamic', {}).items() if value}
    cleaned = {key: value for key, value in (('fonts', fonts), ('iconTheme', chosen.get('iconTheme')),
                                              ('shellIcons', chosen.get('shellIcons')), ('barStyle', chosen.get('barStyle')),
                                              ('windows', windows), ('dynamic', dynamic))
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
    return bool(name) and '/' not in name and bool(icon_theme_dirs(name, ICON_DIRS))


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
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=target.parent, prefix='.thumb-', suffix='.jpg')
    os.close(handle)
    try:
        subprocess.run(['magick', '-limit', 'memory', '256MiB', '-limit', 'map', '512MiB', str(path) + '[0]',
                        '-auto-orient', '-thumbnail', '480x300^', '-gravity', 'center', '-extent', '480x300',
                        '-quality', '85', temporary], capture_output=True, check=True, timeout=60)
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
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
    try:
        monitors = json.loads(subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True, text=True,
                                             timeout=5).stdout)
        monitor = next((m for m in monitors if m.get('focused')), monitors[0])
        scale = monitor.get('scale') or 1
        return round(monitor['width'] / scale), round(monitor['height'] / scale)
    except (OSError, ValueError, subprocess.SubprocessError, IndexError, KeyError, StopIteration):
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
    result = subprocess.run(['magick', '-limit', 'memory', '256MiB', rendered + '[0]', '-resize', f'{width}x{height}^',
                             '-gravity', 'center', '-extent', f'{width}x{height}', '-gravity', 'north', '-crop',
                             f'{width}x{strip}+0+0', '+repage', '-colorspace', 'Gray', '-format', '%[fx:mean]', 'info:'],
                            capture_output=True, text=True, check=True, timeout=60)
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
            directories.sort(key=lambda d: (index.get(d, {}).get('Type') != 'Scalable', -int(index.get(d, {}).get('Size', '0') or 0)))
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
    signature = [2] + [[str(root), root.stat().st_mtime] for root in ICON_DIRS if root.is_dir()]
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
            if base.name in listed or base.name in ('hicolor', 'default', 'locolor') or not index_file.is_file():
                continue
            info = read_index(index_file).get('Icon Theme', {})
            # Hidden is not honoured: Fedora's Adwaita sets it, and the sample check below already drops
            # cursor-only and internal themes.
            if 'legacy' in base.name.lower():
                continue
            samples = icon_samples(base.name, roots)
            # Cursor-only themes resolve nothing beyond hicolor. Adwaita draws folders and files but leaves
            # application icons to hicolor, so two samples of its own are enough.
            if sum(1 for sample in samples if sample and '/hicolor/' not in sample) < 2:
                continue
            listed[base.name] = {'id': base.name, 'name': info.get('Name', base.name), 'samples': samples}
    return sorted(listed.values(), key=lambda t: t['name'].lower())


def render_all(theme, templates=TEMPLATES):
    # Paths a template may need besides the theme itself, and sizes derived from the window rounding
    # (16 is the design size, so the lock screen field keeps its 26 px corners by default).
    scale = max(0, theme.get('hyprland', {}).get('rounding', 16)) / 16
    # Text the templates show (the lock screen), in the session language.
    strings = {'lockPassword': tr('lockScreen.password'), 'lockFingerprintReady': tr('lockScreen.fingerprintReady'),
               'lockFingerprintPresent': tr('lockScreen.fingerprintPresent')}
    theme = dict(theme, paths={'state': str(STATE)}, derived={'lockRounding': round(26 * scale)}, strings=strings)
    outputs = {}
    for path in sorted(templates.glob('*.tpl')):
        outputs[path.stem] = render(path.read_text(encoding='utf-8'), theme, path.name)
    return outputs


DYNAMIC = 'dynamic'
SCHEMES = ('tonal-spot', 'vibrant', 'expressive', 'fidelity', 'neutral')
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
        'system': {'gtkTheme': 'Adwaita-dark' if dark else 'Adwaita', 'iconTheme': 'Papirus-Dark' if dark else 'Papirus-Light',
                   'cursorTheme': 'Adwaita', 'cursorSize': 24, 'accentColor': nearest_accent(palette['accent'])},
        'palette': palette,
        'ansi': ansi,
        'terminal': {'opacity': 0.94},
        'wallpaperDirectories': [str(Path(source).parent)],
        'vscode': {'theme': 'Default Dark Modern' if dark else 'Default Light Modern'},
    }


def run_matugen(image, chosen):
    if shutil.which('matugen') is None:
        raise ValueError(tr('theme.errors.matugenMissing'))
    settings = chosen.get('dynamic', {})
    mode = MODES.get(settings.get('mode', 'auto'), 'smart')
    scheme = settings.get('scheme') if settings.get('scheme') in SCHEMES else 'tonal-spot'
    result = subprocess.run(['matugen', 'image', str(image), '--json', 'hex', '--dry-run', '-m', mode, '-t',
                             'scheme-' + scheme, '--source-color-index', '0'], capture_output=True, text=True,
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
    apply_vscode(applied)
    reload()
    if previous != DYNAMIC:
        remember(previous, current_wallpaper())
    remember(DYNAMIC, image)
    if Path(current_wallpaper() or '') != image:
        apply_wallpaper(image)


def dynamic_info():
    try:
        source = json.loads((CONFIG / 'themes' / DYNAMIC / 'theme.json').read_text(encoding='utf-8')).get('source')
    except (OSError, ValueError, AttributeError):
        source = None
    settings = preferences().get('dynamic', {})
    return {'available': shutil.which('matugen') is not None, 'mode': settings.get('mode', 'auto'),
            'scheme': settings.get('scheme', 'tonal-spot'), 'source': source}


# A destination that is still an old Stow link is replaced, never written through into the repository.
def install(path, text):
    if path.is_symlink():
        path.unlink()
    write_atomic(path, text)


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write through a symlink to its target, and keep the permissions of a file being replaced.
    path = path.resolve() if path.is_symlink() else path
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as file:
            file.write(text)
        # mkstemp creates 0600; these are ordinary config files, readable like the rest of ~/.config.
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


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


# Everything is rendered before anything is written, so a template error leaves the old theme intact.
def apply(name):
    theme = with_preferences(load(name), preferences())
    outputs = render_all(theme)
    for file, text in outputs.items():
        write_atomic(STATE / file, text)
    write_atomic(STATE / 'current.json', json.dumps({'theme': name}, ensure_ascii=False) + '\n')
    if 'qtct.conf' in outputs:
        for config in QTCT:
            install(config, outputs['qtct.conf'])
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('apply')
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
    dynamic.add_argument('--scheme', choices=SCHEMES)
    windows = commands.add_parser('window-style')
    windows.add_argument('--rounding', type=int, choices=range(0, 33), metavar='0-32')
    windows.add_argument('--border', type=int, choices=range(0, 9), metavar='0-8')
    windows.add_argument('--default', action='store_true')
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
    arguments = parser.parse_args()
    # Commands that change the theme state run one at a time: the panel queue and DynamicTheme.qml can
    # overlap, and each rewrites current.json, preferences.json and the rendered files.
    if arguments.command in ('apply', 'set', 'generate', 'dynamic', 'window-style', 'font', 'icon-theme',
                             'shell-icons', 'bar-style'):
        STATE.mkdir(parents=True, exist_ok=True)
        lock = open(STATE / '.lock', 'a')
        fcntl.flock(lock, fcntl.LOCK_EX)
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
        files = wallpaper_files(name, load(name))
        print(json.dumps({'theme': name, 'remembered': memory().get(name), 'current': current_wallpaper(),
                          'wallpapers': wallpaper_entries(name, load(name)), 'files': [str(path) for path in files],
                          'thumbs': {str(path): str(thumb_path(path)) for path in files},
                          'thumbsReady': {str(path): thumb_path(path).is_file() for path in files}}, ensure_ascii=False))
    elif arguments.command == 'thumbs':
        name = arguments.name or current()
        make_thumbs([path for path in wallpaper_files(name, load(name)) if not thumb_path(path).is_file()])
    elif arguments.command == 'open-folder':
        target = USER_FONTS if arguments.kind == 'fonts' else USER_ICONS
        target.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(['xdg-open', str(target)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    elif arguments.command == 'tone':
        print(json.dumps(tone()))
    elif arguments.command == 'check-font':
        if not font_exists(arguments.family):
            raise ValueError(tr('theming.errors.fontMissing', [arguments.family]))
    elif arguments.command == 'check-icons':
        if not icon_theme_exists(arguments.name):
            raise ValueError(tr('theming.errors.iconsMissing', [arguments.name]))
    elif arguments.command == 'generate':
        generate(arguments.image)
    elif arguments.command == 'dynamic':
        chosen = preferences()
        settings = dict(chosen.get('dynamic', {}))
        if arguments.mode:
            settings['mode'] = arguments.mode
        if arguments.scheme:
            settings['scheme'] = arguments.scheme
        chosen['dynamic'] = settings
        save_preferences(chosen)
        # The new mode or style shows at once when the dynamic theme is the current one.
        if current() == DYNAMIC:
            generate(dynamic_info()['source'])
    elif arguments.command == 'window-style':
        chosen = preferences()
        windows = {} if arguments.default else dict(chosen.get('windows', {}))
        if arguments.rounding is not None:
            windows['rounding'] = arguments.rounding
        if arguments.border is not None:
            windows['borderSize'] = arguments.border
        chosen['windows'] = windows
        save_preferences(chosen)
        apply(current())
        reload()
    elif arguments.command in ('shell-icons', 'bar-style'):
        chosen = preferences()
        if arguments.command == 'shell-icons':
            chosen['shellIcons'] = None if arguments.source == 'desktop' else arguments.source
        else:
            style = arguments.style
            if style == 'toggle':
                style = 'shade' if chosen.get('barStyle') == 'transparent' else 'transparent'
            chosen['barStyle'] = None if style == 'shade' else style
        save_preferences(chosen)
        apply(current())
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
        effective = with_preferences(load(current()), preferences())['hyprland']
        print(json.dumps({'current': current(), 'themes': themes(arguments.details),
                          'windows': {'rounding': effective['rounding'], 'borderSize': effective['borderSize']},
                          'dynamic': dynamic_info()},
                         ensure_ascii=False))
    elif arguments.command == 'fonts':
        print(json.dumps(fonts(), ensure_ascii=False))
    elif arguments.command == 'icons':
        print(json.dumps({'themes': cached_icon_themes(), 'theme': load(current()).get('system', {}).get('iconTheme'),
                          'chosen': preferences().get('iconTheme')}, ensure_ascii=False))
    elif arguments.command in ('font', 'icon-theme'):
        chosen = preferences()
        if arguments.command == 'font':
            chosen_fonts = {} if arguments.default else dict(chosen.get('fonts', {}))
            for key, value in (('sans', arguments.sans), ('mono', arguments.mono), ('size', arguments.size)):
                if value is not None:
                    chosen_fonts[key] = value
            if arguments.unified is not None:
                chosen_fonts['unified'] = arguments.unified == 'on'
            chosen['fonts'] = chosen_fonts
        else:
            chosen['iconTheme'] = None if arguments.name == 'default' else arguments.name
        save_preferences(chosen)
        apply(current())
        reload()
    elif arguments.command == 'remember-wallpaper':
        remember(current(), arguments.path.expanduser().resolve())
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

#!/usr/bin/env python3
"""Render the desktop theme into the files the shell and applications read."""
from common import focused_monitor, install_command, magick, theme_name, write_atomic
from i18n import tr
import argparse
import colorsys
import fcntl
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import theme_apps
import theme_assets
import theme_core
import theme_paths
import theme_wallpapers


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


def fonts():
    result = subprocess.run(['fc-list', ':lang=en', '--format', '%{family[0]}\t%{spacing}\t%{file}\n'],
                            capture_output=True, text=True, check=True, timeout=20)
    lines, user = [], set()
    for line in result.stdout.splitlines():
        family, spacing, file = (line.split('\t') + ['', ''])[:3]
        lines.append(family + '\t' + spacing)
        # Fonts the user installed are always offered, whatever their name.
        if file.startswith(str(theme_paths.USER_FONTS) + '/') or file.startswith(str(theme_paths.HOME / '.fonts') + '/'):
            user.add((family.strip(), spacing.strip() == '100' or bool(re.search(r'\bMono\b', family))))
    families = font_families(lines)
    for family, mono in user:
        kind = 'mono' if mono else 'sans'
        if family and family not in families[kind]:
            families[kind] = sorted(families[kind] + [family], key=str.lower)
    name = theme_core.current()
    own = theme_core.load(name).get('fonts', {})
    effective = theme_core.with_preferences(theme_core.load(name), theme_core.preferences()).get('fonts', {})
    return dict(families, theme=own, effective=effective, chosen=theme_core.preferences().get('fonts', {}),
                folder=str(theme_paths.USER_FONTS))


def font_exists(family):
    result = subprocess.run(['fc-list', family, 'family'], capture_output=True, text=True, timeout=20)
    return result.returncode == 0 and result.stdout.strip() != ''


def icon_theme_exists(name):
    return theme_name(name) and bool(theme_assets.icon_theme_dirs(name, theme_assets.ICON_DIRS))


def linear(channel):
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def contrast_ratio(first, second):
    high, low = max(first, second), min(first, second)
    return (high + 0.05) / (low + 0.05)


def relative_luminance(colour):
    rgb = theme_core.split_color(colour, 'luminance')[0]
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
    current_file = theme_paths.SELECTION.with_name('current.jpg')
    try:
        rendered = str(current_file.resolve(strict=True))
    except OSError:
        return dict(bar_text(0.0), mean=0.0)
    # The two text colours of the current theme, so the choice holds for every theme.
    shell = theme_core.with_preferences(theme_core.load(theme_core.current()), theme_core.preferences())['shell']
    light_text, dark_text = shell['text'], shell['accentText']
    width, height = monitor_size()
    key = f'{rendered}@{width}x{height}'
    cache = theme_paths.STATE / 'tone.json'
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


# Resolving samples walks every pack (about 2 s with Yaru's variants), so the result is cached until an
# icon directory changes.
def cached_icon_themes():
    # Bump the version when the discovery rules change.
    signature = [3] + [[str(root), root.stat().st_mtime] for root in theme_assets.ICON_DIRS if root.is_dir()]
    cache = theme_paths.STATE / 'icons-cache.json'
    try:
        stored = json.loads(cache.read_text(encoding='utf-8'))
        if stored.get('signature') == signature:
            return stored['themes']
    except (OSError, ValueError, AttributeError, KeyError):
        pass
    listed = theme_assets.icon_themes()
    write_atomic(cache, json.dumps({'signature': signature, 'themes': listed}, ensure_ascii=False))
    return listed


DYNAMIC = 'dynamic'


MODES = {'auto': 'smart', 'dark': 'dark', 'light': 'light'}


# GNOME accent colours by hue, for the GSettings accent of a generated theme.
GNOME_ACCENTS = (('red', 0), ('orange', 30), ('yellow', 55), ('green', 120), ('teal', 180), ('blue', 215),
                 ('purple', 275), ('pink', 330), ('red', 360))


# Terminal hues in ANSI order (red, green, yellow, blue, magenta, cyan). matugen's base16 colours are the
# image's own, in no hue order, so a brown painting would give a brown red and a brown green.
ANSI_HUES = (4, 130, 45, 215, 300, 185)


def to_rgb(colour):
    rgb = theme_core.split_color(colour, 'colour')[0]
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
    image = Path(image or theme_wallpapers.current_wallpaper() or '')
    if not image.is_file():
        raise ValueError(tr('theme.errors.noWallpaper'))
    theme = dynamic_theme(run_matugen(image, theme_core.preferences()), image)
    write_atomic(theme_paths.CONFIG / 'themes' / DYNAMIC / 'theme.json', json.dumps(theme, indent=2, ensure_ascii=False) + '\n')
    previous = theme_core.current()
    applied = apply(DYNAMIC)
    best_effort(theme_apps.apply_vscode, applied)
    reload()
    if previous != DYNAMIC:
        theme_wallpapers.remember(previous, theme_wallpapers.wallpaper_chosen_under(previous))
    theme_wallpapers.remember(DYNAMIC, image)
    if Path(theme_wallpapers.current_wallpaper() or '') != image:
        theme_wallpapers.apply_wallpaper(image)


def dynamic_info():
    try:
        source = json.loads((theme_paths.CONFIG / 'themes' / DYNAMIC / 'theme.json').read_text(encoding='utf-8')).get('source')
    except (OSError, ValueError, AttributeError):
        source = None
    settings = theme_core.preferences().get('dynamic', {})
    return {'available': shutil.which('matugen') is not None, 'mode': settings.get('mode', 'auto'), 'source': source,
            'install': install_command(['matugen'])}


# A destination that is still an old Stow link is replaced, never written through into the repository.
def install(path, text):
    write_atomic(path, text, follow=False)


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
    theme = theme_core.with_preferences(theme_core.load(name), theme_core.preferences(), name)
    outputs = theme_core.render_all(theme)
    for file, text in outputs.items():
        write_atomic(theme_paths.STATE / file, text)
    write_atomic(theme_paths.STATE / 'current.json', json.dumps({'theme': name}, ensure_ascii=False) + '\n')
    if 'qtct.conf' in outputs:
        for config in theme_paths.QTCT:
            install(config, outputs['qtct.conf'])
    best_effort(theme_apps.apply_btop, outputs.get('btop.theme'))
    best_effort(theme_apps.apply_herdr, theme_core.complete(theme))
    best_effort(theme_apps.apply_gsettings, theme)
    best_effort(theme_apps.apply_cursor, theme)
    return theme


def spawn(arguments):
    theme_paths.STATE.mkdir(parents=True, exist_ok=True)
    with (theme_paths.STATE / 'wallpapers.log').open('a') as log:
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
    cursor.add_argument('--size', type=int, choices=theme_assets.CURSOR_SIZES)
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
    glass.add_argument('--option', choices=tuple(theme_core.GLASS_OPTIONS))
    glass.add_argument('--value', type=float)
    glass.add_argument('--reset', action='store_true')
    text_scale = commands.add_parser('text-scale')
    text_scale.add_argument('scale', type=float, choices=theme_core.TEXT_SCALES)
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
    chosen = theme_core.preferences()
    change(chosen)
    theme_core.save_preferences(chosen)
    apply(theme_core.current())
    if reloading:
        reload()


def command_apply(arguments):
    apply(theme_core.current())
    if not set(theme_assets.CURSOR_PACKS) <= {theme['id'] for theme in theme_assets.cursor_themes()}:
        spawn(['cursor-fetch'])


# Herdr before its first start, which has no folder yet: the current theme goes there, so it opens in it.
def command_herdr(arguments):
    theme_paths.HERDR.mkdir(parents=True, exist_ok=True)
    name = theme_core.current()
    theme_apps.apply_herdr(theme_core.complete(theme_core.with_preferences(theme_core.load(name), theme_core.preferences(), name)))


def command_cursor_fetch(arguments):
    theme_assets.fetch_missing_cursors()


def command_set(arguments):
    previous = theme_core.current()
    theme = apply(arguments.name)
    best_effort(theme_apps.apply_vscode, theme)
    reload()
    # Colours switch at once; the wallpaper (a conversion, maybe a download) follows in the background.
    if previous != arguments.name:
        theme_wallpapers.remember(previous, theme_wallpapers.wallpaper_chosen_under(previous))
        spawn(['fetch', arguments.name, '--show'])


def command_wallpapers(arguments):
    name = arguments.name or theme_core.current()
    theme = theme_core.load(name)
    files = theme_wallpapers.wallpaper_files(name, theme)
    print(json.dumps({'theme': name, 'remembered': theme_wallpapers.memory().get(name), 'current': theme_wallpapers.current_wallpaper(),
                      'wallpapers': theme_wallpapers.wallpaper_entries(name, theme), 'files': [str(path) for path in files],
                      'thumbs': {str(path): str(theme_wallpapers.thumb_path(path)) for path in files},
                      'thumbsReady': {str(path): theme_wallpapers.thumb_path(path).is_file() for path in files}}, ensure_ascii=False))


def command_thumbs(arguments):
    name = arguments.name or theme_core.current()
    theme_wallpapers.make_thumbs([path for path in theme_wallpapers.wallpaper_files(name, theme_core.load(name)) if not theme_wallpapers.thumb_path(path).is_file()])


def command_open_folder(arguments):
    target = theme_paths.USER_FONTS if arguments.kind == 'fonts' else theme_assets.USER_ICONS
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
    chosen = theme_core.preferences()
    settings = dict(chosen.get('dynamic', {}))
    if arguments.mode:
        settings['mode'] = arguments.mode
    chosen['dynamic'] = settings
    theme_core.save_preferences(chosen)
    # The new mode shows at once when the dynamic theme is the current one.
    if theme_core.current() == DYNAMIC:
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
    name = theme_core.current()
    if not theme_core.glass_tunable(theme_core.load(name)):
        raise ValueError(tr('theme.errors.glassUntunable', [theme_core.load(name).get('name', name)]))
    chosen = theme_core.preferences()
    glass = dict(chosen.get('glass', {}))
    if arguments.reset:
        glass.pop(name, None)
    elif arguments.option and arguments.value is not None:
        glass[name] = dict(glass.get(name, {}), **{arguments.option: arguments.value})
    chosen['glass'] = glass
    theme_core.save_preferences(chosen)
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
    name = arguments.name or theme_core.current()
    return 1 if theme_wallpapers.fetch(name, theme_core.load(name), arguments.show) else 0


def command_next_wallpaper(arguments):
    name = theme_core.current()
    theme = theme_core.load(name)
    target = theme_wallpapers.next_wallpaper(theme_wallpapers.wallpaper_files(name, theme), theme_wallpapers.current_wallpaper())
    if target is None:
        spawn(['fetch', name, '--show'])
        subprocess.run(['notify-send', tr('theme.wallpapers.title'), tr('theme.wallpapers.downloading', [theme.get('name', name)])],
                       check=False, timeout=5)
        return 0
    theme_wallpapers.apply_wallpaper(target)


def command_list(arguments):
    name = theme_core.current()
    effective = theme_core.with_preferences(theme_core.load(name), theme_core.preferences(), name)['hyprland']
    glass = None
    if 'glassTuning' in effective:
        glass = [{'option': option, 'value': effective['glassTuning'][option], 'default': default, 'min': low,
                  'max': high, 'step': step} for option, default, low, high, step in theme_core.GLASS_TUNING]
    print(json.dumps({'current': name, 'themes': theme_core.themes(arguments.details),
                      'windows': {key: effective[key] for key in theme_core.WINDOW_KEYS},
                      'glass': glass, 'dynamic': dynamic_info()},
                     ensure_ascii=False))


def command_fonts(arguments):
    print(json.dumps(fonts(), ensure_ascii=False))


def command_icons(arguments):
    print(json.dumps({'themes': cached_icon_themes(), 'theme': theme_core.load(theme_core.current()).get('system', {}).get('iconTheme'),
                      'chosen': theme_core.preferences().get('iconTheme')}, ensure_ascii=False))


def command_cursors(arguments):
    chosen = theme_core.preferences()
    system = theme_core.with_preferences(theme_core.load(theme_core.current()), chosen).get('system', {})
    installed = theme_assets.cursor_themes()
    # Each installed theme with its preview shapes (cursor_samples); a pack still to download has none yet.
    offered = [dict(theme, samples=theme_assets.cursor_samples(theme_assets.cursor_theme_dir(theme['id']))) for theme in installed]
    offered += [{'id': key, 'name': pack['name'], 'download': True, 'samples': []} for key, pack in theme_assets.CURSOR_PACKS.items()
                if key not in {theme['id'] for theme in installed}]
    print(json.dumps({'themes': sorted(offered, key=lambda t: t['name'].lower()), 'theme': system.get('cursorTheme'), 'size': system.get('cursorSize'),
                      'sizes': list(theme_assets.CURSOR_SIZES), 'chosen': chosen.get('cursor', {})}, ensure_ascii=False))


def command_cursor(arguments):
    def change(chosen):
        cursor = {} if arguments.default else dict(chosen.get('cursor', {}))
        if arguments.theme is not None:
            if arguments.theme in theme_assets.CURSOR_PACKS and arguments.theme not in {t['id'] for t in theme_assets.cursor_themes()}:
                theme_assets.fetch_cursor(arguments.theme)
            if arguments.theme != 'default' and arguments.theme not in {t['id'] for t in theme_assets.cursor_themes()}:
                raise ValueError(tr('theming.errors.cursorMissing', [arguments.theme]))
            cursor['theme'] = None if arguments.theme == 'default' else arguments.theme
        if arguments.size is not None:
            cursor['size'] = arguments.size
        chosen['cursor'] = cursor
    update_preferences(change)
    # X11 clients take theme and scaled size from X resources.
    subprocess.run([str(theme_paths.HOME / '.local/bin/desktop-xwayland'), 'apply'], capture_output=True, check=False, timeout=15)


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
    theme_wallpapers.remember(theme_core.current(), arguments.path.expanduser().resolve())


def command_render(arguments):
    for file, text in theme_core.render_all(theme_core.load(arguments.theme)).items():
        write_atomic(arguments.out / file, text)


# One function per command, by its name on the command line ('cursor-fetch' runs command_cursor_fetch).
COMMANDS = {name.removeprefix('command_').replace('_', '-'): function for name, function in list(globals().items())
            if name.startswith('command_') and callable(function)}


def main():
    arguments = build_parser().parse_args()
    if arguments.command in LOCKED:
        theme_paths.STATE.mkdir(parents=True, exist_ok=True)
        lock = open(theme_paths.STATE / '.lock', 'a')
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

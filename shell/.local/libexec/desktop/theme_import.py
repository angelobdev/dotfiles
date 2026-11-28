"""Themes of Omarchy (a colors.toml) turned into themes of this desktop: theme.py import SOURCE, theme.py remove ID.

A colors.toml has about 30 flat keys (mode, accent, selection, muted, four backgrounds and four foregrounds, eight
colours and their bright variants). They map onto the 13 colours of a palette and the 16 of a terminal; the rest
theme_core derives. An import goes into ~/.config/desktop/themes/<id>/, with the backgrounds of the theme folder when
it has some, and shows in the Theming panel and the switcher like the shipped themes. Only themes written there by an
import are removed.
"""
from common import IMAGES, theme_name, write_atomic
from i18n import tr
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import theme_paths
import tomllib

# Written beside theme.json: what an import made, so remove takes only those.
MARK = 'imported.json'
HEX = re.compile(r'#?([0-9a-fA-F]{6})')


def color(colors, *keys):
    for key in keys:
        found = HEX.fullmatch(str(colors.get(key, '')).strip())
        if found:
            return '#' + found[1].lower()
    return ''


def luminance(value):
    channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(first, second):
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def mix(first, second, amount):
    a, b = first.lstrip('#'), second.lstrip('#')
    return '#' + ''.join('%02x' % round(int(a[i:i + 2], 16) * (1 - amount) + int(b[i:i + 2], 16) * amount) for i in (0, 2, 4))


def readable(value, against, ratio):
    """value moved toward black or white, whichever is away from against, just until it reads at ratio on it."""
    target = '#000000' if luminance(value) <= luminance(against) else '#ffffff'
    amount = 0.0
    while contrast(value if amount == 0 else mix(value, target, amount), against) < ratio and amount < 1:
        amount = min(1.0, amount + 0.02)
    return value if amount == 0 else mix(value, target, amount)


def convert(colors, name):
    """A theme.json (dict) from the parsed colors.toml; ValueError when its basic colours are missing."""
    bg, fg, accent = color(colors, 'background'), color(colors, 'bright_foreground', 'foreground'), color(colors, 'accent', 'blue')
    if not bg or not fg or not accent:
        raise ValueError(tr('theme.errors.importColors'))
    light = str(colors.get('mode', '')).strip() == 'light' or luminance(bg) > 0.5
    text = color(colors, 'foreground') or fg
    red, green, yellow = color(colors, 'red') or accent, color(colors, 'green') or accent, color(colors, 'yellow') or accent
    blue, magenta, cyan = color(colors, 'blue') or accent, color(colors, 'magenta') or accent, color(colors, 'cyan') or accent
    selection = color(colors, 'selection') or mix(bg, fg, 0.15)
    raised = color(colors, 'lighter_background') or mix(bg, fg, 0.08)
    # The darkest background of the theme, or its text colour, whichever reads on the accent.
    dark = color(colors, 'darker_background', 'dark_background') or mix(bg, '#000000', 0.4)
    palette = {
        'bg': bg,
        'base': color(colors, 'dark_background') or mix(bg, '#000000' if not light else '#ffffff', 0.15),
        'raised': raised,
        'border': mix(selection, color(colors, 'muted') or selection, 0.5),
        'fg': fg,
        'muted': color(colors, 'light_foreground') or text,
        'dim': color(colors, 'dark_foreground', 'muted') or mix(fg, bg, 0.5),
        'accent': accent,
        'accentFg': max((dark, bg, fg), key=lambda candidate: contrast(candidate, accent)),
        'link': color(colors, 'bright_cyan', 'cyan') or accent,
        'danger': red,
        'success': green,
        'warning': yellow,
    }
    # The contrasts every shipped theme keeps (scripts/tests/test_theme.py): text 7:1 on the background, secondary
    # text 4.5:1, text on the accent 4.5:1; on a light theme the dark text also reads 3:1 on a mid-grey wallpaper
    # under a transparent bar. A theme that falls short gets its colours moved just enough.
    palette['fg'] = readable(palette['fg'], bg, 7.2)
    if light:
        palette['fg'] = readable(palette['fg'], '#999999', 3.1)
    palette['muted'] = readable(palette['muted'], bg, 4.6)
    # Text on the accent is the light background on a light theme and the darkest background on a dark one (the bar
    # takes it as its other text colour, so it must stay the opposite of the text); a mid-tone accent that does not
    # read with it is darkened, or lightened, just enough.
    if light:
        palette['accentFg'] = bg
        palette['accent'] = readable(accent, bg, 4.6)
    elif contrast(palette['accentFg'], accent) < 4.6:
        palette['accentFg'] = dark
        palette['accent'] = readable(accent, dark, 4.6)
    ansi = [selection, red, green, yellow, blue, magenta, cyan, color(colors, 'light_foreground') or text,
            color(colors, 'dark_foreground') or mix(fg, bg, 0.5)]
    for key, normal in (('bright_red', red), ('bright_green', green), ('bright_yellow', yellow), ('bright_blue', blue),
                        ('bright_magenta', magenta), ('bright_cyan', cyan)):
        ansi.append(color(colors, key) or normal)
    ansi.append(fg)
    return {
        'name': name,
        'mode': 'light' if light else 'dark',
        'fonts': {'sans': 'Adwaita Sans', 'mono': 'Adwaita Mono', 'size': 10, 'terminalSize': 11},
        'system': {'gtkTheme': 'adw-gtk3' if light else 'adw-gtk3-dark', 'iconTheme': 'Papirus-Light' if light else 'Papirus-Dark',
                   'cursorTheme': 'Adwaita', 'cursorSize': 24, 'accentColor': 'blue'},
        'palette': palette,
        'ansi': ansi,
        'terminal': {'opacity': 0.94},
    }


def identity(source):
    """An id from a folder or repository name: omarchy-nord-theme, nord-theme.git and nord all give nord."""
    stem = re.sub(r'\.git$', '', Path(str(source).rstrip('/')).name).lower()
    stem = re.sub(r'^omarchy-|-theme$', '', stem)
    stem = re.sub(r'[^a-z0-9]+', '-', stem).strip('-')
    return stem[:48] or 'imported'


def fetch(url, folder):
    # Only a public https repository, as git clones it: no ssh prompt, no credentials asked.
    if not re.fullmatch(r'https://[A-Za-z0-9.-]+/[A-Za-z0-9._/~-]+', url):
        raise ValueError(tr('theme.errors.importSource', [url]))
    result = subprocess.run(['git', 'clone', '--depth', '1', '--quiet', url, str(folder)], capture_output=True, text=True,
                            timeout=120, env={'GIT_TERMINAL_PROMPT': '0', 'PATH': '/usr/bin:/bin'})
    if result.returncode != 0:
        raise ValueError(tr('theme.errors.importFetch', [result.stderr.strip()[:200]]))
    return folder


def install(source, name=None):
    """Imports SOURCE (a colors.toml, a folder with one, or an https git URL); returns the theme id."""
    with tempfile.TemporaryDirectory() as scratch:
        if str(source).startswith('https://'):
            folder = fetch(str(source), Path(scratch) / 'theme')
        else:
            folder = Path(source).expanduser()
        colors_file = folder if folder.is_file() else folder / 'colors.toml'
        if not colors_file.is_file():
            raise ValueError(tr('theme.errors.importSource', [source]))
        folder = colors_file.parent
        try:
            colors = tomllib.loads(colors_file.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            raise ValueError(tr('theme.errors.importColors') + f' ({error})') from None
        theme_id = identity(name or (source if str(source).startswith('https://') else folder))
        title = name or theme_id.replace('-', ' ').title()
        if not theme_name(theme_id) or not theme_name(title):
            raise ValueError(tr('theme.errors.importSource', [source]))
        target = theme_paths.CONFIG / 'themes' / theme_id
        if target.exists() and not (target / MARK).exists():
            raise ValueError(tr('theme.errors.importExists', [theme_id]))
        theme = convert(colors, title)
        images = sorted(path for path in (folder / 'backgrounds').glob('*') if path.suffix.lower() in IMAGES and path.is_file()) \
            if (folder / 'backgrounds').is_dir() else []
        if target.exists():
            shutil.rmtree(target)
        (target / 'backgrounds').mkdir(parents=True)
        for image in images:
            shutil.copy2(image, target / 'backgrounds' / image.name)
        if images:
            theme['wallpaperDirectories'] = [str(target / 'backgrounds')]
        write_atomic(target / 'theme.json', json.dumps(theme, indent=2, ensure_ascii=False) + '\n')
        write_atomic(target / MARK, json.dumps({'source': str(source)}, ensure_ascii=False) + '\n')
    return theme_id


def remove(theme_id):
    target = theme_paths.CONFIG / 'themes' / theme_id
    if not theme_name(theme_id) or not (target / MARK).is_file():
        raise ValueError(tr('theme.errors.importNotImported', [theme_id]))
    shutil.rmtree(target)

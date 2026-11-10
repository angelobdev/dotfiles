"""The colour themes: theme files and their validation, the palette and the values a theme may leave out,
the preferences that apply across themes, the current theme, and the rendering of every template."""
from common import theme_name, write_atomic
from i18n import tr
import json
import re
import theme_paths


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
    for directory in theme_paths.THEME_DIRS:
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
    for directory in reversed(theme_paths.THEME_DIRS):
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
        value = json.loads((theme_paths.STATE / 'preferences.json').read_text(encoding='utf-8'))
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
    write_atomic(theme_paths.STATE / 'preferences.json', json.dumps(cleaned, ensure_ascii=False) + '\n')


# Text sizes of the shell offered, as factors of the drawn sizes (Theme.textSize in QML).
TEXT_SCALES = (1, 1.15, 1.3, 1.5)


def render_all(theme, templates=theme_paths.TEMPLATES):
    # Paths a template may need besides the theme itself, and sizes derived from the window rounding
    # (16 is the design size, so the lock screen field keeps its 26 px corners by default).
    scale = max(0, theme.get('hyprland', {}).get('rounding', 16)) / 16
    # Text the templates show (the lock screen), in the session language.
    strings = {'lockPassword': tr('lockScreen.password'), 'lockFingerprintReady': tr('lockScreen.fingerprintReady'),
               'lockFingerprintPresent': tr('lockScreen.fingerprintPresent')}
    derived = {'lockRounding': round(26 * scale), 'glassTuning': lua_table(theme.get('hyprland', {}).get('glassTuning', {}))}
    theme = dict(theme, paths={'state': str(theme_paths.STATE)}, derived=derived, strings=strings)
    outputs = {}
    for path in sorted(templates.glob('*.tpl')):
        outputs[path.stem] = render(path.read_text(encoding='utf-8'), theme, path.name)
    return outputs


# A saved theme that no longer exists (removed by hand, a deleted dynamic theme) falls back to the default,
# so the session still renders and the panel can still list themes.
def current():
    try:
        name = json.loads((theme_paths.STATE / 'current.json').read_text(encoding='utf-8')).get('theme')
    except (OSError, ValueError, AttributeError):
        name = None
    if isinstance(name, str) and name:
        try:
            theme_path(name)
            return name
        except ValueError:
            pass
    return DEFAULT

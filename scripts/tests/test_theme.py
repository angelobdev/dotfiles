#!/usr/bin/env python3
"""Graphite rendered by theme.py must match the fallbacks the stowed configs keep."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import theme  # noqa: E402

TEMPLATES = REPO / 'shell/.local/share/desktop/templates'
GRAPHITE = json.loads((REPO / 'shell/.local/share/desktop/themes/graphite/theme.json').read_text(encoding='utf-8'))


class GraphiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The stowed fallbacks hold the English text: render as an en_US session whatever the machine says,
        # with the catalogs of this tree, which are not stowed in CI.
        with mock.patch('i18n.language', return_value='en_US'), \
                mock.patch.dict('os.environ', XDG_CONFIG_HOME=str(REPO / 'quickshell/.config')):
            cls.out = theme.render_all(theme.complete(GRAPHITE), TEMPLATES)

    def test_hyprlock_matches_the_stowed_fallback(self):
        self.assertEqual(self.out['hyprlock.conf'], (REPO / 'hyprlock/.config/hypr/hyprlock.conf').read_text(encoding='utf-8'))

    def test_qt_scheme_has_every_role_of_each_group(self):
        lines = self.out['qt-colors.conf'].splitlines()
        self.assertEqual(lines[0], '[ColorScheme]')
        groups = dict(line.split('=', 1) for line in lines[1:])
        self.assertEqual(sorted(groups), ['active_colors', 'disabled_colors', 'inactive_colors'])
        for colors in groups.values():
            self.assertRegex(colors, r'^#ff[0-9a-f]{6}(, #ff[0-9a-f]{6}){20}$')
        # WindowText, Window and Highlight of the active group are the Graphite fg, bg and accent.
        active = groups['active_colors'].split(', ')
        self.assertEqual((active[0], active[10], active[12]), ('#fff0f0f2', '#ff191a1d', '#ffd4d6dc'))

    def test_kitty_matches_the_values_in_kitty_conf(self):
        stowed = {}
        for line in (REPO / 'kitty/.config/kitty/kitty.conf').read_text(encoding='utf-8').splitlines():
            if line and not line.startswith('#') and not line.startswith('include '):
                key, _, value = line.partition(' ')
                stowed[key] = value.strip()
        for line in self.out['kitty.conf'].splitlines():
            if line and not line.startswith('#'):
                key, _, value = line.partition(' ')
                self.assertEqual(stowed.get(key), value.strip(), key)

    def test_quickshell_matches_the_theme_defaults(self):
        source = (REPO / 'quickshell/.config/quickshell/desktop/Theme.qml').read_text(encoding='utf-8')
        defaults = dict(re.findall(r'^\s+property (?:color|string|real) (\w+): "?([^"\n]+?)"?$', source, re.M))
        rendered = json.loads(self.out['quickshell.json'])
        self.assertEqual(set(rendered), set(defaults))
        for key, value in rendered.items():
            self.assertEqual(str(value).lower(), defaults[key].lower(), key)

    def test_hyprland_matches_the_lua_defaults(self):
        source = (REPO / 'hypr/.config/hypr/config/theme.lua').read_text(encoding='utf-8')
        defaults = dict(re.findall(r'^    (\w+) = (\S+),$', source, re.M))
        rendered = dict(re.findall(r'^    (\w+) = (\S+),$', self.out['hyprland.lua'], re.M))
        self.assertEqual(rendered, defaults)

    def test_gtk_defines_every_colour(self):
        names = re.findall(r'^@define-color (\w+) #[0-9a-f]{6};$', self.out['gtk.css'], re.M)
        self.assertEqual(len(names), 37)
        self.assertNotIn('{{', self.out['gtk.css'])


def luminance(colour):
    channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(first, second):
    a, b = sorted((luminance(first), luminance(second)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def over(colour, background):
    """A #rrggbbaa colour composited over an opaque one."""
    if len(colour) == 7:
        return colour
    alpha = int(colour[7:9], 16) / 255
    return '#' + ''.join('%02x' % round(int(colour[i:i + 2], 16) * alpha + int(background[i:i + 2], 16) * (1 - alpha))
                         for i in (1, 3, 5))


class ShippedThemeTests(unittest.TestCase):
    def test_every_theme_renders_and_reads_well(self):
        theme.THEME_DIRS = (REPO / 'shell/.local/share/desktop/themes',)
        ids = [path.parent.name for path in sorted(theme.THEME_DIRS[0].glob('*/theme.json'))]
        self.assertGreaterEqual(len(ids), 5)
        for name in ids:
            with self.subTest(theme=name):
                loaded = theme.load(name)
                out = theme.render_all(loaded, TEMPLATES)
                self.assertEqual(set(out), {path.stem for path in TEMPLATES.glob('*.tpl')})
                self.assertEqual(len(loaded['ansi']), 16)
                palette, shell = loaded['palette'], loaded['shell']
                self.assertGreaterEqual(contrast(palette['fg'], palette['bg']), 7)
                self.assertGreaterEqual(contrast(palette['muted'], palette['bg']), 4.5)
                self.assertGreaterEqual(contrast(palette['accentFg'], palette['accent']), 4.5)
                self.assertGreaterEqual(contrast(shell['text'], over(shell['background'], palette['bg'])), 7)

    def test_completion_never_overrides_explicit_values(self):
        completed = theme.complete(GRAPHITE)
        for section in ('palette', 'shell', 'hyprland'):
            for key, value in GRAPHITE[section].items():
                self.assertEqual(completed[section][key], value, section + '.' + key)


class WallpaperTests(unittest.TestCase):
    def test_manifests_are_pinned_and_checksummed(self):
        for path in sorted((REPO / 'shell/.local/share/desktop/themes').glob('*/theme.json')):
            entries = json.loads(path.read_text(encoding='utf-8')).get('wallpapers', [])
            files = [entry['file'] for entry in entries]
            self.assertEqual(len(files), len(set(files)), path.parent.name)
            for entry in entries:
                with self.subTest(theme=path.parent.name, file=entry['file']):
                    self.assertRegex(entry['url'], r'^https://raw\.githubusercontent\.com/[^/]+/[^/]+/[0-9a-f]{40}/')
                    self.assertRegex(entry['sha256'], r'^[0-9a-f]{64}$')
                    self.assertRegex(entry['file'], r'^\d{2}-[a-z0-9-]+\.(webp|jpg|png)$')

    def test_next_wallpaper_cycles_and_starts_over(self):
        files = [Path('/w/a.jpg'), Path('/w/b.jpg'), Path('/w/c.jpg')]
        self.assertEqual(theme.next_wallpaper(files, '/w/a.jpg'), files[1])
        self.assertEqual(theme.next_wallpaper(files, '/w/c.jpg'), files[0])
        self.assertEqual(theme.next_wallpaper(files, '/elsewhere.jpg'), files[0])
        self.assertIsNone(theme.next_wallpaper([], '/w/a.jpg'))

    def test_files_and_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = theme.STATE, theme.WALLPAPERS
            theme.STATE, theme.WALLPAPERS = root / 'state', root / 'walls'
            try:
                (root / 'mine').mkdir()
                for name in ('b.png', 'a.jpg', 'notes.txt'):
                    (root / 'mine' / name).write_text('x')
                listed = theme.wallpaper_files('local', {'wallpaperDirectories': [str(root / 'mine')]})
                self.assertEqual([path.name for path in listed], ['a.jpg', 'b.png'])
                pack = {'wallpapers': [{'file': '01-one.jpg'}, {'file': '02-two.jpg'}]}
                self.assertEqual(theme.wallpaper_files('pack', pack), [])
                (root / 'walls/pack').mkdir(parents=True)
                (root / 'walls/pack/02-two.jpg').write_text('x')
                self.assertEqual(theme.wallpaper_for('pack', pack), root / 'walls/pack/02-two.jpg')
                theme.remember('pack', root / 'mine/a.jpg')
                self.assertEqual(theme.wallpaper_for('pack', pack), root / 'mine/a.jpg')
                (root / 'mine/a.jpg').unlink()
                self.assertEqual(theme.wallpaper_for('pack', pack), root / 'walls/pack/02-two.jpg')
            finally:
                theme.STATE, theme.WALLPAPERS = saved


class PreferenceTests(unittest.TestCase):
    def test_preferences_override_and_default_restores(self):
        merged = theme.with_preferences(GRAPHITE, {'fonts': {'sans': 'Inter', 'size': 11}, 'iconTheme': 'breeze'})
        self.assertEqual(merged['fonts']['sans'], 'Inter')
        self.assertEqual(merged['fonts']['size'], 11)
        self.assertEqual(merged['fonts']['mono'], GRAPHITE['fonts']['mono'])
        self.assertEqual(merged['system']['iconTheme'], 'breeze')
        self.assertEqual(theme.with_preferences(GRAPHITE, {'fonts': {'sans': ''}}), GRAPHITE)

    def test_qtct_follows_fonts_and_icons(self):
        default = theme.render_all(theme.complete(GRAPHITE), TEMPLATES)['qtct.conf']
        self.assertIn('icon_theme=Papirus-Dark\n', default)
        self.assertIn('general="Adwaita Sans,10,-1,5,50,0,0,0,0,0"\n', default)
        self.assertIn('fixed="Adwaita Mono,10,-1,5,50,0,0,0,0,0"\n', default)
        self.assertIn('color_scheme_path=' + str(theme.STATE) + '/qt-colors.conf\n', default)
        chosen = theme.render_all(theme.complete(theme.with_preferences(GRAPHITE, {'fonts': {'sans': 'Inter'}, 'iconTheme': 'breeze'})), TEMPLATES)['qtct.conf']
        self.assertIn('icon_theme=breeze\n', chosen)
        self.assertIn('general="Inter,10,', chosen)

    def test_install_replaces_a_link_instead_of_writing_through(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'repo.conf').write_text('stowed')
            (root / 'link.conf').symlink_to(root / 'repo.conf')
            theme.install(root / 'link.conf', 'generated')
            self.assertEqual((root / 'repo.conf').read_text(), 'stowed')
            self.assertFalse((root / 'link.conf').is_symlink())
            self.assertEqual((root / 'link.conf').read_text(), 'generated')


class PanelOptionTests(unittest.TestCase):
    def test_unified_font_uses_the_monospace_family(self):
        merged = theme.with_preferences(GRAPHITE, {'fonts': {'mono': 'JetBrains Mono', 'unified': True}})
        self.assertEqual(merged['fonts']['sans'], 'JetBrains Mono')
        self.assertNotIn('unified', merged['fonts'])
        merged = theme.with_preferences(GRAPHITE, {'fonts': {'unified': True}})
        self.assertEqual(merged['fonts']['sans'], GRAPHITE['fonts']['mono'])

    def test_shell_options_reach_the_render_with_defaults(self):
        default = json.loads(theme.render_all(theme.complete(GRAPHITE), TEMPLATES)['quickshell.json'])
        self.assertEqual((default['iconSource'], default['barStyle']), ('desktop', 'shade'))
        chosen = theme.complete(theme.with_preferences(GRAPHITE, {'shellIcons': 'pack', 'barStyle': 'transparent'}))
        rendered = json.loads(theme.render_all(chosen, TEMPLATES)['quickshell.json'])
        self.assertEqual((rendered['iconSource'], rendered['barStyle']), ('pack', 'transparent'))

    def test_window_style_reaches_hyprland_with_theme_colours(self):
        default = theme.render_all(theme.complete(GRAPHITE), TEMPLATES)['hyprland.lua']
        self.assertIn('rounding = 16,', default)
        self.assertIn('borderSize = 0,', default)
        self.assertIn('activeBorder = "rgba(d4d6dcff)",', default)
        chosen = theme.complete(theme.with_preferences(GRAPHITE, {'windows': {'rounding': 8, 'borderSize': 2}}))
        rendered = theme.render_all(chosen, TEMPLATES)['hyprland.lua']
        self.assertIn('rounding = 8,', rendered)
        self.assertIn('borderSize = 2,', rendered)

    def test_thumbnail_names_change_with_the_file(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'a.jpg'
            image.write_bytes(b'one')
            first = theme.thumb_path(image)
            self.assertEqual(first, theme.thumb_path(image))
            self.assertEqual(first.suffix, '.jpg')
            image.write_bytes(b'longer content')
            self.assertNotEqual(first, theme.thumb_path(image))

    def test_bar_text_picks_the_higher_contrast_for_every_theme(self):
        # A mid-tone painted sky (Gruvbox 03-village-square) needs dark text; dark and light strips the obvious one.
        self.assertEqual(theme.bar_text(0.58)['text'], 'dark')
        self.assertEqual(theme.bar_text(0.82)['text'], 'dark')
        self.assertEqual(theme.bar_text(0.098)['text'], 'light')
        theme.THEME_DIRS = (REPO / 'shell/.local/share/desktop/themes',)
        for path in sorted(theme.THEME_DIRS[0].glob('*/theme.json')):
            shell = theme.load(path.parent.name)['shell']
            for mean in (0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0):
                with self.subTest(theme=path.parent.name, mean=mean):
                    choice = theme.bar_text(mean, shell['text'], shell['accentText'])
                    # The better of the two colours never drops below the 3:1 large-text minimum,
                    # and is always at least as good as the other one.
                    self.assertGreaterEqual(choice['contrast'], 3)


class FontAndIconTests(unittest.TestCase):
    def test_font_families_are_filtered_and_split(self):
        sample = ['Inter\t0', 'Inter\t', 'JetBrains Mono\t100', 'Noto Sans Mono\t0', 'Noto Sans Bengali\t0',
                  'Noto Serif\t0', 'Noto Color Emoji\t0', 'C059\t0', 'Source Code Pro\t100', 'Cantarell\t0']
        self.assertEqual(theme.font_families(sample), {'sans': ['Cantarell', 'Inter'],
                                                      'mono': ['JetBrains Mono', 'Noto Sans Mono', 'Source Code Pro']})

    def test_icon_themes_follow_inherits_and_skip_cursor_themes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def theme_dir(name, index, icons=()):
                (root / name).mkdir()
                (root / name / 'index.theme').write_text(index)
                for icon in icons:
                    (root / name / 'scalable/apps').mkdir(parents=True, exist_ok=True)
                    (root / name / 'scalable/apps' / (icon + '.svg')).write_text('<svg/>')
            directories = '[Icon Theme]\nName={}\nInherits={}\nDirectories=scalable/apps\n[scalable/apps]\nSize=48\nType=Scalable\n'
            theme_dir('Base', directories.format('Base', 'hicolor'), ('folder', 'utilities-terminal', 'web-browser'))
            theme_dir('Child', directories.format('Child Pack', 'Base'), ('folder', 'preferences-system'))
            theme_dir('Pointers', '[Icon Theme]\nName=Pointers\n')
            theme_dir('hicolor', directories.format('Hicolor', ''), ('text-x-generic',))
            listed = theme.icon_themes([root])
            self.assertEqual([entry['id'] for entry in listed], ['Base', 'Child'])
            child = next(entry for entry in listed if entry['id'] == 'Child')
            self.assertEqual(child['name'], 'Child Pack')
            self.assertEqual([Path(path).parts[-4] if path else '' for path in child['samples']],
                             ['Child', 'Base', 'Base', 'Child', 'hicolor'])


class VscodeTests(unittest.TestCase):
    def test_replaces_or_inserts_the_colour_theme(self):
        existing = '{\n    "a": 1,\n    "workbench.colorTheme": "Old"\n}\n'
        self.assertEqual(theme.vscode_settings(existing, 'workbench.colorTheme', 'New'), existing.replace('"Old"', '"New"'))
        inserted = theme.vscode_settings('{\n    "a": 1\n}\n', 'workbench.preferredDarkColorTheme', 'New')
        self.assertEqual(json.loads(inserted), {'workbench.preferredDarkColorTheme': 'New', 'a': 1})

    def test_invalid_results_raise(self):
        with self.assertRaises(ValueError):
            theme.vscode_settings('{"a": 1,}', 'workbench.colorTheme', 'New')


class RendererTests(unittest.TestCase):
    def test_filters(self):
        values = {'c': '#11223344', 'o': '#112233'}
        self.assertEqual(theme.render('{{ c | hex }}', values, 't'), '#112233')
        self.assertEqual(theme.render('{{ c | rgba }} {{ o | rgba }} {{ o | rgba:cc }}', values, 't'), '11223344 112233ff 112233cc')
        self.assertEqual(theme.render('{{ c | qt }} {{ o | qt }} {{ o | qt:ff }}', values, 't'), '#44112233 #112233 #ff112233')
        self.assertEqual(theme.render('{{ c | hypr }} {{ c | hexrgba }}', values, 't'), '0x44112233 0x11223344')

    def test_unknown_values_and_bad_colours_fail(self):
        with self.assertRaises(ValueError):
            theme.render('{{ missing }}', {}, 't')
        with self.assertRaises(ValueError):
            theme.render('{{ group }}', {'group': {'a': 1}}, 't')
        with self.assertRaises(ValueError):
            theme.render('{{ c | hex }}', {'c': 'red'}, 't')

    def test_theme_names_are_checked(self):
        with self.assertRaises(ValueError):
            theme.theme_path('../etc')


def matugen_output(mode):
    """The shape of matugen image --json hex output, with the Material roles of a blue seed."""
    roles = {
        'dark': {'surface': '#111318', 'surface_container_lowest': '#0c0e13', 'surface_container_low': '#191c20',
                 'surface_container_high': '#282a2f', 'outline_variant': '#44474e', 'on_surface': '#e2e2e9',
                 'on_surface_variant': '#c4c6d0', 'outline': '#8e9099', 'primary': '#aac7ff', 'on_primary': '#0a305f',
                 'tertiary': '#dcbce0', 'error': '#ffb4ab'},
        'light': {'surface': '#f9f9ff', 'surface_container_lowest': '#ffffff', 'surface_container_low': '#f3f3fa',
                  'surface_container_high': '#e7e8ee', 'outline_variant': '#c4c6d0', 'on_surface': '#191c20',
                  'on_surface_variant': '#44474e', 'outline': '#74777f', 'primary': '#415f91', 'on_primary': '#ffffff',
                  'tertiary': '#705575', 'error': '#ba1a1a'},
    }[mode]
    # Image colours in no hue order, as matugen reports them for a brown painting; the theme ignores them.
    tones = {'base08': '#bdbaa4', 'base0a': '#c5c0aa', 'base0b': '#beb79c', 'base0d': '#bcb295'}
    wrap = lambda value: {'dark': {'color': value}, 'light': {'color': value}, 'default': {'color': value.upper()}}
    return {'mode': mode, 'is_dark_mode': mode == 'dark', 'colors': {k: wrap(v) for k, v in roles.items()},
            'base16': {k: wrap(v) for k, v in tones.items()}}


class DynamicThemeTests(unittest.TestCase):
    def test_material_roles_map_to_the_palette(self):
        generated = theme.dynamic_theme(matugen_output('dark'), '/pictures/sea.jpg')
        palette = generated['palette']
        self.assertEqual((palette['bg'], palette['base'], palette['raised']), ('#111318', '#0c0e13', '#282a2f'))
        self.assertEqual((palette['fg'], palette['accent'], palette['accentFg']), ('#e2e2e9', '#aac7ff', '#0a305f'))
        self.assertEqual(generated['mode'], 'dark')
        self.assertEqual(generated['source'], '/pictures/sea.jpg')
        self.assertEqual(generated['wallpaperDirectories'], ['/pictures'])
        self.assertEqual(generated['system']['gtkTheme'], 'Adwaita-dark')
        light = theme.dynamic_theme(matugen_output('light'), '/pictures/snow.jpg')
        self.assertEqual((light['mode'], light['palette']['base']), ('light', '#f3f3fa'))
        self.assertEqual(light['system']['iconTheme'], 'Papirus-Light')
        self.assertEqual(light['vscode']['theme'], 'Default Light Modern')

    def test_ansi_keeps_its_hues_and_stays_readable(self):
        for mode in ('dark', 'light'):
            with self.subTest(mode=mode):
                generated = theme.dynamic_theme(matugen_output(mode), '/pictures/a.jpg')
                ansi, background = generated['ansi'], generated['palette']['bg']
                self.assertEqual(len(ansi), 16)
                for index in (1, 2, 3, 4, 5, 6):
                    self.assertGreaterEqual(contrast(ansi[index], background), 3, index)
                for index in (9, 10, 11, 12, 13, 14):
                    self.assertGreaterEqual(contrast(ansi[index], background), 4.5, index)
                self.assertGreaterEqual(contrast(ansi[15 if mode == 'dark' else 0], background), 4.5)
                # Red, green, yellow and blue stay themselves, whatever the image colours are.
                for index, accent in ((1, 'red'), (2, 'green'), (3, 'yellow'), (4, 'blue'), (9, 'red'), (10, 'green')):
                    self.assertEqual(theme.nearest_accent(ansi[index]), accent, index)

    def test_harmonizing_turns_at_most_fifteen_degrees(self):
        hue = lambda colour: theme.colorsys.rgb_to_hls(*theme.to_rgb(colour))[0] * 360
        self.assertAlmostEqual(hue(theme.harmonized(130, '#ff0000', 0.6, 0.5)), 115, delta=1.5)
        self.assertAlmostEqual(hue(theme.harmonized(130, '#20e040', 0.6, 0.5)), 129.5, delta=1.5)

    def test_accent_colour_is_the_nearest_hue(self):
        self.assertEqual(theme.nearest_accent('#aac7ff'), 'blue')
        self.assertEqual(theme.nearest_accent('#f0c040'), 'yellow')
        self.assertEqual(theme.nearest_accent('#40c070'), 'green')
        self.assertEqual(theme.nearest_accent('#e05090'), 'pink')
        self.assertEqual(theme.nearest_accent('#8a8d93'), 'slate')

    def test_generated_themes_read_like_the_shipped_ones(self):
        for mode in ('dark', 'light'):
            with self.subTest(mode=mode):
                loaded = theme.complete(theme.dynamic_theme(matugen_output(mode), '/pictures/a.jpg'))
                out = theme.render_all(loaded, TEMPLATES)
                self.assertEqual(set(out), {path.stem for path in TEMPLATES.glob('*.tpl')})
                palette, shell = loaded['palette'], loaded['shell']
                self.assertGreaterEqual(contrast(palette['fg'], palette['bg']), 7)
                self.assertGreaterEqual(contrast(palette['muted'], palette['bg']), 4.5)
                self.assertGreaterEqual(contrast(palette['accentFg'], palette['accent']), 4.5)
                self.assertGreaterEqual(contrast(palette['success'], palette['bg']), 4.5)
                self.assertGreaterEqual(contrast(palette['warning'], palette['bg']), 4.5)

    def test_light_themes_shade_the_bar_with_their_background(self):
        light = theme.complete(theme.dynamic_theme(matugen_output('light'), '/pictures/a.jpg'))
        self.assertEqual(light['shell']['barShadeTop'], '#f9f9ff99')
        self.assertEqual(theme.complete(GRAPHITE)['shell']['barShadeTop'], GRAPHITE['shell'].get('barShadeTop', '#00000055'))
        dark = theme.complete(theme.dynamic_theme(matugen_output('dark'), '/pictures/a.jpg'))
        self.assertEqual(dark['shell']['barShadeTop'], '#00000055')

    def test_dynamic_preferences_are_kept_and_cleaned(self):
        chosen = {'dynamic': {'mode': 'light', 'scheme': ''}}
        with tempfile.TemporaryDirectory() as directory:
            original = theme.STATE
            theme.STATE = Path(directory)
            try:
                theme.save_preferences(chosen)
                self.assertEqual(theme.preferences().get('dynamic'), {'mode': 'light'})
            finally:
                theme.STATE = original

    @unittest.skipUnless(theme.shutil.which('matugen'), 'matugen is not installed')
    def test_real_matugen_output_converts(self):
        image = REPO / 'shell/.local/share/icons/hicolor/scalable/apps/desktopai.svg'
        wallpapers = sorted((Path.home() / '.local/share/desktop/wallpapers').glob('*/*.jp*g'))
        if wallpapers:
            image = wallpapers[0]
        for mode in ('dark', 'light'):
            with self.subTest(mode=mode):
                data = theme.run_matugen(image, {'dynamic': {'mode': mode}})
                generated = theme.complete(theme.dynamic_theme(data, image))
                self.assertEqual(generated['mode'], mode)
                self.assertGreaterEqual(contrast(generated['palette']['fg'], generated['palette']['bg']), 7)


class ReviewRegressionTests(unittest.TestCase):
    def test_empty_vscode_settings_get_valid_json(self):
        self.assertEqual(json.loads(theme.vscode_settings('{}', 'workbench.colorTheme', 'X')), {'workbench.colorTheme': 'X'})

    def test_next_wallpaper_compares_resolved_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            target = folder / 'real.jpg'
            target.write_bytes(b'')
            (folder / 'b.jpg').write_bytes(b'')
            link = folder / 'a.jpg'
            link.symlink_to(target)
            files = [link, folder / 'b.jpg']
            self.assertEqual(theme.next_wallpaper(files, str(target)), folder / 'b.jpg')

    def test_a_removed_saved_theme_falls_back_to_the_default(self):
        with tempfile.TemporaryDirectory() as directory:
            original = theme.STATE
            theme.STATE = Path(directory)
            try:
                (theme.STATE / 'current.json').write_text('{"theme": "gone"}', encoding='utf-8')
                self.assertEqual(theme.current(), theme.DEFAULT)
            finally:
                theme.STATE = original

    def test_a_theme_without_ansi_is_invalid(self):
        broken = dict(GRAPHITE)
        broken.pop('ansi')
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'broken'
            folder.mkdir()
            (folder / 'theme.json').write_text(json.dumps(broken), encoding='utf-8')
            original = theme.THEME_DIRS
            theme.THEME_DIRS = (Path(directory),)
            try:
                with self.assertRaises(ValueError):
                    theme.load('broken')
            finally:
                theme.THEME_DIRS = original


if __name__ == '__main__':
    unittest.main()

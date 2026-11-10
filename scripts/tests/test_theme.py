#!/usr/bin/env python3
"""Graphite rendered by theme.py must match the fallbacks the stowed configs keep."""
import atexit
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
# Never the real state or caches, even for a test that forgets to redirect a folder: the theme modules read them from
# the environment when they are imported.
SANDBOX = tempfile.TemporaryDirectory()
atexit.register(SANDBOX.cleanup)
os.environ['XDG_STATE_HOME'] = str(Path(SANDBOX.name) / 'state')
os.environ['XDG_CACHE_HOME'] = str(Path(SANDBOX.name) / 'cache')
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import theme  # noqa: E402
import theme_apps  # noqa: E402
import theme_assets  # noqa: E402
import theme_core  # noqa: E402
import theme_paths  # noqa: E402
import theme_wallpapers  # noqa: E402

TEMPLATES = REPO / 'shell/.local/share/desktop/templates'
GRAPHITE = json.loads((REPO / 'shell/.local/share/desktop/themes/graphite/theme.json').read_text(encoding='utf-8'))


class GraphiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The stowed fallbacks hold the English text: render as an en_US session whatever the machine says,
        # with the catalogs of this tree, which are not stowed in CI.
        with mock.patch('i18n.language', return_value='en_US'), \
                mock.patch.dict('os.environ', XDG_CONFIG_HOME=str(REPO / 'quickshell/.config')):
            cls.out = theme_core.render_all(theme_core.complete(GRAPHITE), TEMPLATES)

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
        defaults = dict(re.findall(r'^\s+property (?:color|string|real|bool) (\w+): "?([^"\n]+?)"?$', source, re.M))
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
        theme_paths.THEME_DIRS = (REPO / 'shell/.local/share/desktop/themes',)
        ids = [path.parent.name for path in sorted(theme_paths.THEME_DIRS[0].glob('*/theme.json'))]
        self.assertGreaterEqual(len(ids), 5)
        for name in ids:
            with self.subTest(theme=name):
                loaded = theme_core.load(name)
                out = theme_core.render_all(loaded, TEMPLATES)
                self.assertEqual(set(out), {path.stem for path in TEMPLATES.glob('*.tpl')})
                self.assertEqual(len(loaded['ansi']), 16)
                palette, shell = loaded['palette'], loaded['shell']
                self.assertGreaterEqual(contrast(palette['fg'], palette['bg']), 7)
                self.assertGreaterEqual(contrast(palette['muted'], palette['bg']), 4.5)
                self.assertGreaterEqual(contrast(palette['accentFg'], palette['accent']), 4.5)
                self.assertGreaterEqual(contrast(shell['text'], over(shell['background'], palette['bg'])), 7)

    def test_completion_never_overrides_explicit_values(self):
        completed = theme_core.complete(GRAPHITE)
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
        self.assertEqual(theme_wallpapers.next_wallpaper(files, '/w/a.jpg'), files[1])
        self.assertEqual(theme_wallpapers.next_wallpaper(files, '/w/c.jpg'), files[0])
        self.assertEqual(theme_wallpapers.next_wallpaper(files, '/elsewhere.jpg'), files[0])
        self.assertIsNone(theme_wallpapers.next_wallpaper([], '/w/a.jpg'))

    def test_files_and_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = theme_paths.STATE, theme_paths.WALLPAPERS
            theme_paths.STATE, theme_paths.WALLPAPERS = root / 'state', root / 'walls'
            try:
                (root / 'mine').mkdir()
                for name in ('b.png', 'a.jpg', 'notes.txt'):
                    (root / 'mine' / name).write_text('x')
                listed = theme_wallpapers.wallpaper_files('local', {'wallpaperDirectories': [str(root / 'mine')]})
                self.assertEqual([path.name for path in listed], ['a.jpg', 'b.png'])
                pack = {'wallpapers': [{'file': '01-one.jpg'}, {'file': '02-two.jpg'}]}
                self.assertEqual(theme_wallpapers.wallpaper_files('pack', pack), [])
                (root / 'walls/pack').mkdir(parents=True)
                (root / 'walls/pack/02-two.jpg').write_text('x')
                self.assertEqual(theme_wallpapers.wallpaper_for('pack', pack), root / 'walls/pack/02-two.jpg')
                theme_wallpapers.remember('pack', root / 'mine/a.jpg')
                self.assertEqual(theme_wallpapers.wallpaper_for('pack', pack), root / 'mine/a.jpg')
                (root / 'mine/a.jpg').unlink()
                self.assertEqual(theme_wallpapers.wallpaper_for('pack', pack), root / 'walls/pack/02-two.jpg')
            finally:
                theme_paths.STATE, theme_paths.WALLPAPERS = saved


    def test_a_wallpaper_is_remembered_only_for_the_theme_it_was_chosen_under(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(theme_paths, 'SELECTION', Path(directory) / 'selection.json'):
            self.assertIsNone(theme_wallpapers.wallpaper_chosen_under('gruvbox'))
            theme_paths.SELECTION.write_text(json.dumps({'source': '/w/a.jpg', 'theme': 'gruvbox'}))
            self.assertEqual(theme_wallpapers.wallpaper_chosen_under('gruvbox'), '/w/a.jpg')
            # Switched again before the new theme's wallpaper landed: the image on screen is the earlier theme's.
            self.assertIsNone(theme_wallpapers.wallpaper_chosen_under('everforest'))
            # Written before selections noted their theme.
            theme_paths.SELECTION.write_text(json.dumps({'source': '/w/b.jpg'}))
            self.assertEqual(theme_wallpapers.wallpaper_chosen_under('everforest'), '/w/b.jpg')


class PreferenceTests(unittest.TestCase):
    def test_preferences_override_and_default_restores(self):
        merged = theme_core.with_preferences(GRAPHITE, {'fonts': {'sans': 'Inter', 'size': 11}, 'iconTheme': 'breeze'})
        self.assertEqual(merged['fonts']['sans'], 'Inter')
        self.assertEqual(merged['fonts']['size'], 11)
        self.assertEqual(merged['fonts']['mono'], GRAPHITE['fonts']['mono'])
        self.assertEqual(merged['system']['iconTheme'], 'breeze')
        self.assertEqual(theme_core.with_preferences(GRAPHITE, {'fonts': {'sans': ''}}), GRAPHITE)

    def test_qtct_follows_fonts_and_icons(self):
        default = theme_core.render_all(theme_core.complete(GRAPHITE), TEMPLATES)['qtct.conf']
        self.assertIn('icon_theme=Papirus-Dark\n', default)
        self.assertIn('general="Adwaita Sans,10,-1,5,50,0,0,0,0,0"\n', default)
        self.assertIn('fixed="Adwaita Mono,10,-1,5,50,0,0,0,0,0"\n', default)
        self.assertIn('color_scheme_path=' + str(theme_paths.STATE) + '/qt-colors.conf\n', default)
        chosen = theme_core.render_all(theme_core.complete(theme_core.with_preferences(GRAPHITE, {'fonts': {'sans': 'Inter'}, 'iconTheme': 'breeze'})), TEMPLATES)['qtct.conf']
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


class TextScaleTests(unittest.TestCase):
    def test_the_shell_text_scale_reaches_quickshell(self):
        rendered = theme_core.render_all(theme_core.complete(theme_core.with_preferences(GRAPHITE, {'textScale': 1.3})), TEMPLATES)['quickshell.json']
        self.assertEqual(json.loads(rendered)['textScale'], 1.3)
        default = theme_core.render_all(theme_core.complete(GRAPHITE), TEMPLATES)['quickshell.json']
        self.assertEqual(json.loads(default)['textScale'], 1)

    def test_only_offered_scales_are_saved(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(theme_paths, 'STATE', Path(folder)):
            theme_core.save_preferences({'textScale': 1.15})
            self.assertEqual(json.loads((Path(folder) / 'preferences.json').read_text()), {'textScale': 1.15})
            theme_core.save_preferences({'textScale': 3})
            self.assertEqual(json.loads((Path(folder) / 'preferences.json').read_text()), {})


class ReduceEffectsTests(unittest.TestCase):
    def render(self, chosen):
        out = theme_core.render_all(theme_core.complete(theme_core.with_preferences(GRAPHITE, chosen)), TEMPLATES)
        return json.loads(out['quickshell.json'])['reduceEffects'], dict(re.findall(r'^    (\w+) = (\S+),$', out['hyprland.lua'], re.M))['reduceEffects']

    def test_the_choice_reaches_hyprland_and_the_shell(self):
        self.assertEqual(self.render({'reduceEffects': True}), (True, 'true'))
        self.assertEqual(self.render({}), (False, 'false'))
        # Only a real true counts: a hand-edited "yes" leaves the effects on.
        self.assertEqual(self.render({'reduceEffects': 'yes'}), (False, 'false'))

    def test_only_on_is_saved_and_toggle_flips_it(self):
        import argparse
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(theme_paths, 'STATE', Path(folder)), \
                mock.patch.object(theme, 'apply'), mock.patch.object(theme, 'reload') as reloaded, \
                mock.patch.object(theme_core, 'current', return_value='graphite'):
            saved = Path(folder) / 'preferences.json'
            for action, expected in (('on', {'reduceEffects': True}), ('toggle', {}), ('toggle', {'reduceEffects': True}), ('off', {})):
                theme.command_reduce_effects(argparse.Namespace(action=action))
                self.assertEqual(json.loads(saved.read_text()), expected, action)
            # Hyprland reloads each time: animations, blur, shadows and glass are its config.
            self.assertEqual(reloaded.call_count, 4)

    def test_compositor_and_glass_read_the_switch(self):
        appearance = (REPO / 'hypr/.config/hypr/config/appearance.lua').read_text(encoding='utf-8')
        self.assertIn('local effects = not theme.reduceEffects', appearance)
        self.assertEqual(appearance.count('enabled = effects'), 3)
        plugins = (REPO / 'hypr/.config/hypr/config/plugins.lua').read_text(encoding='utf-8')
        self.assertIn('enabled = not theme.reduceEffects,', plugins)
        self.assertIn('layers = { enabled = not theme.reduceEffects,', plugins)


class HerdrTests(unittest.TestCase):
    def test_every_theme_gives_herdr_a_complete_theme(self):
        for name in [t['id'] for t in theme_core.themes() if t['id'] != 'dynamic']:
            data = theme_apps.herdr_theme(theme_core.complete(theme_core.load(name)))
            self.assertEqual(len(data['ansi']), 16, name)
            colors = [data['background'], data['foreground'], data['selection'], data['cursor']] + data['ansi'] + list(data['colors'].values())
            for color in colors:
                self.assertRegex(color, r'^#[0-9a-f]{6}$', name)
            self.assertEqual(data['colors']['accent'], data['cursor'], name)

    def test_only_unset_or_own_keys_change(self):
        wanted = {'theme': 'desktop', 'font': 'Fira Code', 'font_size': 15}
        # A first run sets what is unset and keeps a value picked by hand.
        self.assertEqual(theme_apps.herdr_settings({'zoom': 1, 'font': 'Iosevka'}, wanted, {}),
                         {'zoom': 1, 'font': 'Iosevka', 'theme': 'desktop', 'font_size': 15})
        # A later run follows the desktop where the value is still the one written last time.
        self.assertEqual(theme_apps.herdr_settings({'theme': 'desktop', 'font': 'Fira Code'}, {'theme': 'desktop', 'font': 'JetBrains Mono'}, {'theme': 'desktop', 'font': 'Fira Code'}),
                         {'theme': 'desktop', 'font': 'JetBrains Mono'})
        self.assertEqual(theme_apps.herdr_settings({'theme': 'moss'}, wanted, {'theme': 'desktop'})['theme'], 'moss')

    def test_apply_writes_the_theme_and_leaves_a_broken_settings_alone(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            herdr, state = root / 'herdr-app', root / 'state'
            completed = theme_core.complete(GRAPHITE)
            with mock.patch.object(theme_paths, 'HERDR', herdr), mock.patch.object(theme_paths, 'STATE', state):
                theme_apps.apply_herdr(completed)
                self.assertFalse(herdr.exists(), 'no Herdr app, nothing written')
                herdr.mkdir()
                (herdr / 'settings.json').write_text('{"zoom": 1.2, "sounds": {"enabled": true}}')
                theme_apps.apply_herdr(completed)
                self.assertEqual(json.loads((herdr / 'themes/desktop.json').read_text())['background'], completed['palette']['bg'])
                settings = json.loads((herdr / 'settings.json').read_text())
                self.assertEqual((settings['zoom'], settings['theme'], settings['font']), (1.2, 'desktop', completed['fonts']['mono']))
                (herdr / 'settings.json').write_text('{ "zoom": 1.2, // a comment\n }')
                theme_apps.apply_herdr(completed)
                self.assertEqual((herdr / 'settings.json').read_text(), '{ "zoom": 1.2, // a comment\n }')

    def test_the_first_start_gets_the_current_theme(self):
        # desktop-ai runs theme.py herdr before Herdr has a folder: it opens in the desktop theme.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            herdr, state = root / 'herdr-app', root / 'state'
            with mock.patch.object(theme_paths, 'HERDR', herdr), mock.patch.object(theme_paths, 'STATE', state), \
                    mock.patch.object(theme_core, 'current', return_value='graphite'), mock.patch.object(theme_core, 'preferences', return_value={}), \
                    mock.patch.object(theme_core, 'load', return_value=GRAPHITE):
                theme.command_herdr(None)
            self.assertEqual(json.loads((herdr / 'themes/desktop.json').read_text())['background'], theme_core.complete(GRAPHITE)['palette']['bg'])
            self.assertEqual(json.loads((herdr / 'settings.json').read_text())['theme'], 'desktop')


class IconThemeTests(unittest.TestCase):
    def test_a_malformed_size_hides_no_other_theme(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, size in (('Sloppy', '48px'), ('Tidy', '48')):
                (root / name / '48/apps').mkdir(parents=True)
                (root / name / 'index.theme').write_text(f'[Icon Theme]\nName={name}\nDirectories=48/apps\n\n[48/apps]\nSize={size}\nType=Fixed\n')
                for icon in theme_assets.ICON_SAMPLES:
                    (root / name / '48/apps' / (icon + '.svg')).write_text('<svg/>')
            self.assertEqual([listed['id'] for listed in theme_assets.icon_themes([root])], ['Sloppy', 'Tidy'])


class GsettingsTests(unittest.TestCase):
    def test_only_values_that_differ_are_set(self):
        listing = ("org.gnome.desktop.interface color-scheme 'prefer-dark'\n"
                   "org.gnome.desktop.interface cursor-size 24\n"
                   "org.gnome.desktop.interface font-name 'Sans 10'\n")
        def run(command, **_):
            return mock.Mock(stdout=listing) if command[1] == 'list-recursively' else mock.Mock()
        merged = dict(GRAPHITE, mode='dark', fonts={'sans': 'Sans', 'size': 11}, system={'cursorSize': 24})
        with mock.patch('subprocess.run', side_effect=run) as called:
            theme_apps.apply_gsettings(merged)
        sets = [call.args[0][3:] for call in called.call_args_list if call.args[0][1] == 'set']
        self.assertEqual(sets, [['font-name', 'Sans 11']])


class CursorTests(unittest.TestCase):
    def test_the_chosen_cursor_reaches_gsettings_and_hyprland(self):
        merged = theme_core.with_preferences(GRAPHITE, {'cursor': {'theme': 'Bibata', 'size': 32}})
        self.assertEqual((merged['system']['cursorTheme'], merged['system']['cursorSize']), ('Bibata', 32))
        lua = theme_core.render_all(theme_core.complete(merged), TEMPLATES)['hyprland.lua']
        self.assertIn('cursorTheme = "Bibata"', lua)
        self.assertIn('cursorSize = 32', lua)
        self.assertEqual(theme_core.with_preferences(GRAPHITE, {'cursor': {}}), GRAPHITE)

    def test_names_stay_quoted_values_in_lua_and_json(self):
        merged = dict(GRAPHITE, system=dict(GRAPHITE['system'], cursorTheme='a"b\\'), fonts=dict(GRAPHITE['fonts'], sans='Sans "Q"'))
        outputs = theme_core.render_all(theme_core.complete(merged), TEMPLATES)
        self.assertIn('cursorTheme = "a\\"b\\\\",', outputs['hyprland.lua'])
        self.assertEqual(json.loads(outputs['quickshell.json'])['font'], 'Sans "Q"')
        with self.assertRaises(ValueError):
            theme_core.render_all(theme_core.complete(dict(GRAPHITE, system=dict(GRAPHITE['system'], iconTheme='A\nicon_theme=B'))), TEMPLATES)

    def test_unplain_names_are_never_taken_from_preferences(self):
        merged = theme_core.with_preferences(GRAPHITE, {'iconTheme': 'x\ny', 'cursor': {'theme': 'x", os = "'}})
        self.assertEqual(merged['system'], GRAPHITE['system'])

    def test_the_lua_defaults_match_the_shipped_themes(self):
        defaults = (REPO / 'hypr/.config/hypr/config/theme.lua').read_text()
        self.assertIn(f'cursorTheme = "{GRAPHITE["system"]["cursorTheme"]}"', defaults)
        self.assertIn(f'cursorSize = {GRAPHITE["system"]["cursorSize"]}', defaults)

    def test_cursor_themes_are_folders_with_cursors(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'Bibata/cursors').mkdir(parents=True)
            (root / 'Bibata/index.theme').write_text('[Icon Theme]\nName=Bibata Modern\n')
            (root / 'Hypr').mkdir()
            (root / 'Hypr/manifest.hl').write_text('')
            (root / 'Papirus').mkdir()
            (root / 'default/cursors').mkdir(parents=True)
            self.assertEqual(theme_assets.cursor_themes([root]), [{'id': 'Bibata', 'name': 'Bibata Modern'}, {'id': 'Hypr', 'name': 'Hypr'}])

    def test_a_cursor_pack_unpacks_only_its_folder(self):
        import hashlib
        import io
        import tarfile as tar
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'packs.tar.bz2'
            with tar.open(archive, 'w:bz2') as pack:
                for name, data in (('./pack-light/cursors/left_ptr', b'light'), ('./pack-light/index.theme', b'[Icon Theme]\nName=Pack Light\n'),
                                   ('./pack-dark/cursors/left_ptr', b'dark')):
                    info = tar.TarInfo(name)
                    info.size = len(data)
                    pack.addfile(info, io.BytesIO(data))
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            packs = {'pack-light': {'name': 'Pack Light', 'file': 'packs.tar.bz2', 'member': 'pack-light', 'url': 'https://example.com/packs.tar.bz2', 'sha256': digest}}

            def download(entry, destination):
                destination.write_bytes(archive.read_bytes())
            with mock.patch.object(theme_assets, 'CURSOR_PACKS', packs), mock.patch.object(theme_assets, 'USER_ICONS', root / 'icons'), \
                    mock.patch.object(theme_assets, 'CURSOR_DOWNLOADS', root / 'cache'), mock.patch.object(theme_assets, 'download', side_effect=download) as fetched:
                theme_assets.fetch_cursor('pack-light')
                self.assertEqual((root / 'icons/pack-light/cursors/left_ptr').read_bytes(), b'light')
                self.assertFalse((root / 'icons/pack-dark').exists())
                self.assertEqual(theme_assets.cursor_themes([root / 'icons']), [{'id': 'pack-light', 'name': 'Pack Light'}])
                # Installed meanwhile (the other of two fetches): nothing more to do.
                theme_assets.fetch_cursor('pack-light')
                self.assertEqual(fetched.call_count, 1)
                import shutil
                shutil.rmtree(root / 'icons/pack-light')
                theme_assets.fetch_cursor('pack-light')
                self.assertEqual(fetched.call_count, 1)  # The archive is kept.
                # A kept archive that no longer matches is fetched again (download() checks the new one).
                shutil.rmtree(root / 'icons/pack-light')
                packs['pack-light']['sha256'] = '0' * 64
                theme_assets.fetch_cursor('pack-light')
                self.assertEqual(fetched.call_count, 2)
                self.assertEqual(sorted(path.name for path in (root / 'icons').iterdir()), ['pack-light'])

    @staticmethod
    def xcursor(*images):
        # An XCursor file with one image chunk per (nominal size, width, height, ARGB pixel) entry.
        import struct
        chunks, toc, position = b'', b'', 16 + 12 * len(images)
        for size, width, height, pixel in images:
            chunk = struct.pack('<IIIIIIIII', 36, theme_assets.XCURSOR_IMAGE, size, 1, width, height, 0, 0, 0) + pixel * (width * height)
            toc += struct.pack('<III', theme_assets.XCURSOR_IMAGE, size, position)
            chunks += chunk
            position += len(chunk)
        return b'Xcur' + struct.pack('<III', 16, 0x10000, len(images)) + toc + chunks

    @staticmethod
    def png_size_and_first_pixel(data):
        import struct
        import zlib
        width, height = struct.unpack('>II', data[16:24])
        rows = zlib.decompress(data[data.index(b'IDAT') + 4:data.index(b'IEND') - 8])
        return (width, height), rows[1:5]

    def test_an_xcursor_preview_takes_the_largest_fitting_size_unpremultiplied(self):
        # Premultiplied half-transparent red (B, G, R, A little endian) becomes straight red at alpha 128.
        data = self.xcursor((24, 24, 24, bytes((0, 0, 255, 255))), (48, 48, 48, bytes((0, 0, 64, 128))), (128, 128, 128, bytes((0, 0, 0, 0))))
        self.assertEqual(self.png_size_and_first_pixel(theme_assets.xcursor_png(data)), ((48, 48), bytes((127, 0, 0, 128))))
        # Only sizes above the largest: the smallest of them.
        self.assertEqual(self.png_size_and_first_pixel(theme_assets.xcursor_png(data, largest=16))[0], (24, 24))
        for broken in (b'not a cursor', data[:40], b'Xcur' + data[4:16]):
            with self.assertRaises(ValueError):
                theme_assets.xcursor_png(broken)

    def test_cursor_samples_fall_back_to_x11_names_and_are_cached(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'Old/cursors').mkdir(parents=True)
            (root / 'Old/cursors/left_ptr').write_bytes(self.xcursor((32, 32, 32, bytes((0, 0, 0, 255)))))
            (root / 'Old/cursors/hand2').write_bytes(b'broken')
            (root / 'Old/cursors/pointer').symlink_to('hand2')
            with mock.patch.object(theme_assets, 'CURSOR_PREVIEWS', root / 'cache'):
                samples = theme_assets.cursor_samples(theme_assets.cursor_theme_dir('Old', [root]))
                # Arrow from left_ptr; the broken hand and the missing shapes stay empty.
                self.assertTrue(samples[0].endswith('.png'))
                self.assertEqual(samples[1:], ['', '', '', ''])
                self.assertEqual(self.png_size_and_first_pixel(Path(samples[0]).read_bytes())[0], (32, 32))
                # A second listing reads the cache; a changed file gets a new preview.
                self.assertEqual(theme_assets.cursor_samples(root / 'Old')[0], samples[0])
                (root / 'Old/cursors/left_ptr').write_bytes(self.xcursor((24, 24, 24, bytes((0, 0, 0, 255)))))
                self.assertNotEqual(theme_assets.cursor_samples(root / 'Old')[0], samples[0])
            self.assertIsNone(theme_assets.cursor_theme_dir('Missing', [root]))

    def test_hyprcursor_samples_come_from_the_shape_archives(self):
        import zipfile
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'Hypr/shapes').mkdir(parents=True)
            (root / 'Hypr/manifest.hl').write_text('name = Hypr\ncursors_directory = shapes\n')
            with zipfile.ZipFile(root / 'Hypr/shapes/default.hlc', 'w') as shape:
                shape.writestr('meta.hl', 'resize_algorithm = bilinear\ndefine_size = 32, small.png\ndefine_size = 64, large.png\ndefine_size = 256, huge.png\n')
                for name in ('small.png', 'large.png', 'huge.png'):
                    shape.writestr(name, name.encode())
            with zipfile.ZipFile(root / 'Hypr/shapes/text.hlc', 'w') as shape:
                shape.writestr('meta.hl', 'define_size = 0, text.svg\n')
                shape.writestr('text.svg', b'<svg/>')
            with mock.patch.object(theme_assets, 'CURSOR_PREVIEWS', root / 'cache'):
                samples = theme_assets.cursor_samples(theme_assets.cursor_theme_dir('Hypr', [root]))
            self.assertEqual(Path(samples[0]).read_bytes(), b'large.png')
            self.assertEqual((Path(samples[2]).suffix, Path(samples[2]).read_bytes()), ('.svg', b'<svg/>'))
            self.assertEqual(samples[1], '')

    def test_a_second_fetch_waits_for_the_first_and_finds_it_done(self):
        import fcntl
        import threading
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            packs = {'pack': {'name': 'Pack', 'file': 'p.tar', 'member': 'pack', 'url': 'https://example.com/p.tar', 'sha256': '0' * 64}}
            with mock.patch.object(theme_assets, 'CURSOR_PACKS', packs), mock.patch.object(theme_assets, 'USER_ICONS', root / 'icons'), \
                    mock.patch.object(theme_assets, 'CURSOR_DOWNLOADS', root / 'cache'), mock.patch.object(theme_assets, 'download') as fetched:
                (root / 'cache').mkdir()
                with open(root / 'cache/.lock', 'a') as first:
                    fcntl.flock(first, fcntl.LOCK_EX)
                    second = threading.Thread(target=theme_assets.fetch_cursor, args=('pack',))
                    second.start()
                    second.join(0.3)
                    self.assertTrue(second.is_alive())  # Waiting for the first.
                    (root / 'icons/pack/cursors').mkdir(parents=True)
                second.join(5)
                self.assertFalse(second.is_alive())
                fetched.assert_not_called()

    def test_only_valid_cursor_choices_are_saved(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(theme_paths, 'STATE', Path(folder)):
            theme_core.save_preferences({'cursor': {'theme': None, 'size': 32}})
            self.assertEqual(json.loads((Path(folder) / 'preferences.json').read_text()), {'cursor': {'size': 32}})
            theme_core.save_preferences({'cursor': {'theme': None}})
            self.assertEqual(json.loads((Path(folder) / 'preferences.json').read_text()), {})


class PanelOptionTests(unittest.TestCase):
    def test_unified_font_uses_the_monospace_family(self):
        merged = theme_core.with_preferences(GRAPHITE, {'fonts': {'mono': 'JetBrains Mono', 'unified': True}})
        self.assertEqual(merged['fonts']['sans'], 'JetBrains Mono')
        self.assertNotIn('unified', merged['fonts'])
        merged = theme_core.with_preferences(GRAPHITE, {'fonts': {'unified': True}})
        self.assertEqual(merged['fonts']['sans'], GRAPHITE['fonts']['mono'])

    def test_shell_options_reach_the_render_with_defaults(self):
        default = json.loads(theme_core.render_all(theme_core.complete(GRAPHITE), TEMPLATES)['quickshell.json'])
        self.assertEqual((default['iconSource'], default['barStyle']), ('desktop', 'shade'))
        chosen = theme_core.complete(theme_core.with_preferences(GRAPHITE, {'shellIcons': 'pack', 'barStyle': 'transparent'}))
        rendered = json.loads(theme_core.render_all(chosen, TEMPLATES)['quickshell.json'])
        self.assertEqual((rendered['iconSource'], rendered['barStyle']), ('pack', 'transparent'))

    def test_window_style_reaches_hyprland_with_theme_colours(self):
        default = theme_core.render_all(theme_core.complete(GRAPHITE), TEMPLATES)['hyprland.lua']
        self.assertIn('rounding = 16,', default)
        self.assertIn('borderSize = 0,', default)
        self.assertIn('activeBorder = "rgba(d4d6dcff)",', default)
        chosen = theme_core.complete(theme_core.with_preferences(GRAPHITE, {'windows': {'rounding': 8, 'borderSize': 2}}))
        rendered = theme_core.render_all(chosen, TEMPLATES)['hyprland.lua']
        self.assertIn('rounding = 8,', rendered)
        self.assertIn('borderSize = 2,', rendered)

    def test_thumbnail_names_change_with_the_file(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'a.jpg'
            image.write_bytes(b'one')
            first = theme_wallpapers.thumb_path(image)
            self.assertEqual(first, theme_wallpapers.thumb_path(image))
            self.assertEqual(first.suffix, '.jpg')
            image.write_bytes(b'longer content')
            self.assertNotEqual(first, theme_wallpapers.thumb_path(image))

    def test_bar_text_picks_the_higher_contrast_for_every_theme(self):
        # A mid-tone painted sky (Gruvbox 03-village-square) needs dark text; dark and light strips the obvious one.
        self.assertEqual(theme.bar_text(0.58)['text'], 'dark')
        self.assertEqual(theme.bar_text(0.82)['text'], 'dark')
        self.assertEqual(theme.bar_text(0.098)['text'], 'light')
        theme_paths.THEME_DIRS = (REPO / 'shell/.local/share/desktop/themes',)
        for path in sorted(theme_paths.THEME_DIRS[0].glob('*/theme.json')):
            shell = theme_core.load(path.parent.name)['shell']
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
            listed = theme_assets.icon_themes([root])
            self.assertEqual([entry['id'] for entry in listed], ['Base', 'Child'])
            child = next(entry for entry in listed if entry['id'] == 'Child')
            self.assertEqual(child['name'], 'Child Pack')
            self.assertEqual([Path(path).parts[-4] if path else '' for path in child['samples']],
                             ['Child', 'Base', 'Base', 'Child', 'hicolor'])


class VscodeTests(unittest.TestCase):
    def test_replaces_or_inserts_the_colour_theme(self):
        existing = '{\n    "a": 1,\n    "workbench.colorTheme": "Old"\n}\n'
        self.assertEqual(theme_apps.vscode_settings(existing, 'workbench.colorTheme', 'New'), existing.replace('"Old"', '"New"'))
        inserted = theme_apps.vscode_settings('{\n    "a": 1\n}\n', 'workbench.preferredDarkColorTheme', 'New')
        self.assertEqual(json.loads(inserted), {'workbench.preferredDarkColorTheme': 'New', 'a': 1})

    def test_invalid_results_raise(self):
        with self.assertRaises(ValueError):
            theme_apps.vscode_settings('{"a": 1,}', 'workbench.colorTheme', 'New')


class RendererTests(unittest.TestCase):
    def test_filters(self):
        values = {'c': '#11223344', 'o': '#112233'}
        self.assertEqual(theme_core.render('{{ c | hex }}', values, 't'), '#112233')
        self.assertEqual(theme_core.render('{{ c | rgba }} {{ o | rgba }} {{ o | rgba:cc }}', values, 't'), '11223344 112233ff 112233cc')
        self.assertEqual(theme_core.render('{{ c | qt }} {{ o | qt }} {{ o | qt:ff }}', values, 't'), '#44112233 #112233 #ff112233')
        self.assertEqual(theme_core.render('{{ c | hypr }} {{ c | hexrgba }}', values, 't'), '0x44112233 0x11223344')

    def test_unknown_values_and_bad_colours_fail(self):
        with self.assertRaises(ValueError):
            theme_core.render('{{ missing }}', {}, 't')
        with self.assertRaises(ValueError):
            theme_core.render('{{ group }}', {'group': {'a': 1}}, 't')
        with self.assertRaises(ValueError):
            theme_core.render('{{ c | hex }}', {'c': 'red'}, 't')

    def test_theme_names_are_checked(self):
        with self.assertRaises(ValueError):
            theme_core.theme_path('../etc')


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
        self.assertEqual(generated['system']['gtkTheme'], 'adw-gtk3-dark')
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
                loaded = theme_core.complete(theme.dynamic_theme(matugen_output(mode), '/pictures/a.jpg'))
                out = theme_core.render_all(loaded, TEMPLATES)
                self.assertEqual(set(out), {path.stem for path in TEMPLATES.glob('*.tpl')})
                palette, shell = loaded['palette'], loaded['shell']
                self.assertGreaterEqual(contrast(palette['fg'], palette['bg']), 7)
                self.assertGreaterEqual(contrast(palette['muted'], palette['bg']), 4.5)
                self.assertGreaterEqual(contrast(palette['accentFg'], palette['accent']), 4.5)
                self.assertGreaterEqual(contrast(palette['success'], palette['bg']), 4.5)
                self.assertGreaterEqual(contrast(palette['warning'], palette['bg']), 4.5)

    def test_light_themes_shade_the_bar_with_their_background(self):
        light = theme_core.complete(theme.dynamic_theme(matugen_output('light'), '/pictures/a.jpg'))
        self.assertEqual(light['shell']['barShadeTop'], '#f9f9ff99')
        self.assertEqual(theme_core.complete(GRAPHITE)['shell']['barShadeTop'], GRAPHITE['shell'].get('barShadeTop', '#00000055'))
        dark = theme_core.complete(theme.dynamic_theme(matugen_output('dark'), '/pictures/a.jpg'))
        self.assertEqual(dark['shell']['barShadeTop'], '#00000055')

    def test_dynamic_preferences_are_kept_and_cleaned(self):
        chosen = {'dynamic': {'mode': 'light', 'scheme': 'vibrant'}}
        with tempfile.TemporaryDirectory() as directory:
            original = theme_paths.STATE
            theme_paths.STATE = Path(directory)
            try:
                theme_core.save_preferences(chosen)
                self.assertEqual(theme_core.preferences().get('dynamic'), {'mode': 'light'})
            finally:
                theme_paths.STATE = original

    @unittest.skipUnless(theme.shutil.which('matugen'), 'matugen is not installed')
    def test_real_matugen_output_converts(self):
        image = REPO / 'hyprpaper/.local/share/wallpapers/desktop-night.jpg'
        for mode in ('dark', 'light'):
            with self.subTest(mode=mode):
                data = theme.run_matugen(image, {'dynamic': {'mode': mode}})
                generated = theme_core.complete(theme.dynamic_theme(data, image))
                self.assertEqual(generated['mode'], mode)
                self.assertGreaterEqual(contrast(generated['palette']['fg'], generated['palette']['bg']), 7)


class ReviewRegressionTests(unittest.TestCase):
    def test_a_failing_app_integration_does_not_stop_the_switch(self):
        # A hung dconf or an unwritable btop folder: reported, and the steps after it still run.
        with tempfile.TemporaryDirectory() as directory:
            original = theme_paths.STATE
            theme_paths.STATE = Path(directory)
            try:
                with mock.patch.object(theme_core, 'load', return_value=GRAPHITE), \
                        mock.patch.object(theme_core, 'preferences', return_value={}), \
                        mock.patch.object(theme_core, 'render_all', return_value={}), \
                        mock.patch.object(theme_apps, 'apply_btop', side_effect=OSError('read-only')), \
                        mock.patch.object(theme_apps, 'apply_herdr') as herdr, \
                        mock.patch.object(theme_apps, 'apply_gsettings', side_effect=theme.subprocess.TimeoutExpired('gsettings', 5)), \
                        mock.patch.object(theme_apps, 'apply_cursor') as cursor, \
                        mock.patch('sys.stderr', new_callable=io.StringIO) as errors:
                    theme_apps.apply_btop.__name__ = 'apply_btop'
                    theme_apps.apply_gsettings.__name__ = 'apply_gsettings'
                    theme.apply('graphite')
                self.assertEqual(json.loads((theme_paths.STATE / 'current.json').read_text()), {'theme': 'graphite'})
                herdr.assert_called_once()
                cursor.assert_called_once()
                self.assertIn('apply_btop: read-only', errors.getvalue())
                self.assertIn('apply_gsettings:', errors.getvalue())
            finally:
                theme_paths.STATE = original

    def test_empty_vscode_settings_get_valid_json(self):
        self.assertEqual(json.loads(theme_apps.vscode_settings('{}', 'workbench.colorTheme', 'X')), {'workbench.colorTheme': 'X'})

    def test_next_wallpaper_compares_resolved_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            target = folder / 'real.jpg'
            target.write_bytes(b'')
            (folder / 'b.jpg').write_bytes(b'')
            link = folder / 'a.jpg'
            link.symlink_to(target)
            files = [link, folder / 'b.jpg']
            self.assertEqual(theme_wallpapers.next_wallpaper(files, str(target)), folder / 'b.jpg')

    def test_a_removed_saved_theme_falls_back_to_the_default(self):
        with tempfile.TemporaryDirectory() as directory:
            original = theme_paths.STATE
            theme_paths.STATE = Path(directory)
            try:
                (theme_paths.STATE / 'current.json').write_text('{"theme": "gone"}', encoding='utf-8')
                self.assertEqual(theme_core.current(), theme_core.DEFAULT)
            finally:
                theme_paths.STATE = original

    def test_a_theme_without_ansi_is_invalid(self):
        broken = dict(GRAPHITE)
        broken.pop('ansi')
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'broken'
            folder.mkdir()
            (folder / 'theme.json').write_text(json.dumps(broken), encoding='utf-8')
            original = theme_paths.THEME_DIRS
            theme_paths.THEME_DIRS = (Path(directory),)
            try:
                with self.assertRaises(ValueError):
                    theme_core.load('broken')
            finally:
                theme_paths.THEME_DIRS = original



GLASS = json.loads((REPO / 'shell/.local/share/desktop/themes/glass/theme.json').read_text(encoding='utf-8'))


class GlassTuningTests(unittest.TestCase):
    def test_defaults_match_the_liquid_preset(self):
        # theme.py shows these as the defaults; plugins.lua must start from the same values.
        lua = (REPO / 'hypr/.config/hypr/config/plugins.lua').read_text(encoding='utf-8')
        preset = lua[lua.index('local liquid = {'):lua.index('glass.preset("liquid"')]
        for option, default, *_ in theme_core.GLASS_TUNING:
            match = re.search(r'\b' + option + r' = ([0-9.]+),', preset)
            self.assertIsNotNone(match, option)
            self.assertEqual(float(match[1]), default, option)

    def test_tuning_is_rendered_clamped_and_per_theme(self):
        chosen = {'glass': {'glass': {'refraction_strength': 9, 'edge_height': 30.4, 'unknown': 1},
                            'glass-light': {'blur_strength': 0.1}}}
        merged = theme_core.with_preferences(theme_core.complete(GLASS), chosen, 'glass')
        tuning = merged['hyprland']['glassTuning']
        self.assertEqual(tuning['refraction_strength'], 3.0)
        self.assertEqual(tuning['edge_height'], 30)
        self.assertEqual(tuning['blur_strength'], 0.45)
        self.assertNotIn('unknown', tuning)
        rendered = theme_core.render_all(merged, TEMPLATES)['hyprland.lua']
        self.assertIn('edge_height = 30,', rendered)
        self.assertIn('refraction_strength = 3.0,', rendered)

    def test_themes_without_liquid_glass_get_no_tuning(self):
        merged = theme_core.with_preferences(theme_core.complete(GRAPHITE), {'glass': {'graphite': {'blur_strength': 1}}}, 'graphite')
        self.assertNotIn('glassTuning', merged['hyprland'])
        self.assertIn('glassTuning = {},', theme_core.render_all(merged, TEMPLATES)['hyprland.lua'])

    def test_saved_tuning_drops_defaults_and_unknown_options(self):
        chosen = {'glass': {'glass': {'blur_strength': 0.45, 'bevel_strength': 0.2, 'xray': 1}, 'glass-light': {'noise_strength': 0}}}
        with tempfile.TemporaryDirectory() as directory:
            original = theme_paths.STATE
            theme_paths.STATE = Path(directory)
            try:
                theme_core.save_preferences(chosen)
                self.assertEqual(theme_core.preferences().get('glass'), {'glass': {'bevel_strength': 0.2}})
            finally:
                theme_paths.STATE = original

    def test_gaps_reach_hyprland(self):
        default = theme_core.render_all(theme_core.complete(GRAPHITE), TEMPLATES)['hyprland.lua']
        self.assertIn('gapsIn = 4,', default)
        self.assertIn('gapsOut = 4,', default)
        chosen = theme_core.complete(theme_core.with_preferences(GRAPHITE, {'windows': {'gapsIn': 8, 'gapsOut': 16}}))
        rendered = theme_core.render_all(chosen, TEMPLATES)['hyprland.lua']
        self.assertIn('gapsIn = 8,', rendered)
        self.assertIn('gapsOut = 16,', rendered)



class WrapperTests(unittest.TestCase):
    """desktop-theme apply with a stand-in gsettings and theme.py, in a temporary home."""

    def run_apply(self, gsettings):
        import os
        import subprocess
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        home = Path(directory.name)
        (home / 'bin').mkdir()
        (home / 'bin/gsettings').write_text('#!/bin/sh\n' + gsettings)
        (home / 'bin/gsettings').chmod(0o755)
        helper = home / '.local/libexec/desktop/theme.py'
        helper.parent.mkdir(parents=True)
        helper.write_text('import pathlib, sys\npathlib.Path(sys.argv[0]).with_name("applied").write_text(sys.argv[1])\n')
        result = subprocess.run(['bash', str(REPO / 'shell/.local/bin/desktop-theme'), 'apply'], capture_output=True, text=True,
                                env={**os.environ, 'HOME': str(home), 'XDG_STATE_HOME': str(home / 'state'),
                                     'PATH': f"{home / 'bin'}:{os.environ['PATH']}"}, timeout=30)
        return result, home

    def test_the_interface_backup_is_complete_and_kept(self):
        result, home = self.run_apply("echo 'org.gnome.desktop.interface gtk-theme Adwaita'\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        backup = home / 'state/dotfiles/interface-before-theme.ini'
        self.assertEqual(backup.read_text(), 'org.gnome.desktop.interface gtk-theme Adwaita\n')
        self.assertEqual((home / '.local/libexec/desktop/applied').read_text(), 'apply')

    def test_a_failing_gsettings_leaves_no_backup_and_the_theme_applies(self):
        result, home = self.run_apply('echo "No such schema" >&2; exit 1\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list((home / 'state/dotfiles').iterdir()), [])
        self.assertEqual((home / '.local/libexec/desktop/applied').read_text(), 'apply')


class MainErrorTests(unittest.TestCase):
    def test_an_unexpected_failure_is_said_in_the_catalogs_words(self):
        with mock.patch.object(theme, 'tr', side_effect=lambda key, values=(): f'{key} {values[0]}'):
            self.assertEqual(theme.failure_message(OSError(28, 'No space left on device')),
                             'theme.errors.failed [Errno 28] No space left on device')
            self.assertTrue(theme.failure_message(json.JSONDecodeError('Expecting value', '', 0)).startswith('theme.errors.failed'))
            self.assertEqual(theme.failure_message(ValueError('Unknown theme: x')), 'Unknown theme: x')


if __name__ == '__main__':
    unittest.main()

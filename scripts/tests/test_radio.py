#!/usr/bin/env python3
"""Tests for radio.py station catalog, ytfzf JSON parsing, saved playlists, and state persistence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import radio  # noqa: E402


class RadioTests(unittest.TestCase):
    def test_station_catalog_and_aliases(self):
        self.assertGreaterEqual(len(radio.STATIONS), 20)
        categories = {s['category'] for s in radio.STATIONS}
        self.assertEqual(categories, {'jazz', 'dreamwave', 'lofi', 'rnb'})
        for key in ('linn-jazz', 'swiss', 'plaza', 'nightride', 'bluenote', 'nujabes', 'jdilla', 'mfdoom', 'funk', 'neosoul'):
            matched = radio.match_station(key, saved_items=[])
            self.assertIsNotNone(matched, f'Expected station match for {key}')
            self.assertTrue(matched['url'].startswith(('http://', 'https://')))

    def test_parse_ytfzf_multi_array_and_playlist_fix(self):
        raw = (
            '[]\n'
            + json.dumps([
                {
                    'ID': 'BACK-BUTTON',
                    'title': '[BACK]',
                    'url': 'back',
                },
                {
                    'ID': 'UC12345',
                    'title': '[channel] LOFIMIX',
                    'url': 'https://youtube.com/channel/UC12345',
                    'action': 'scrape type=invidious-channel search=https://yt.example/channel/UC12345',
                },
                {
                    'ID': '9CE6-2DwPK4',
                    'title': 'Nujabes Compilation',
                    'url': 'https://youtube.com/watch?v=9CE6-2DwPK4',
                    'channel': 'LOFIMIX',
                    'duration': '119:50',
                },
            ])
            + '\n'
            + json.dumps([
                {
                    'ID': 'PLTOLG4HoV_HZBwO9uP49QZ5TshUUaAq5x',
                    'title': '[playlist] Nujabes relax LO-FI',
                    'url': 'https://www.youtube.com/playlist?list=null',
                    'channel': 'Harima Kenji',
                    'duration': '144 videos',
                    'views': 'playlist',
                },
            ])
        )
        parsed = radio.parse_ytfzf_output(raw)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['kind'], 'youtube')
        self.assertEqual(parsed[0]['url'], 'https://www.youtube.com/watch?v=9CE6-2DwPK4')
        self.assertEqual(parsed[0]['subtitle'], 'LOFIMIX · 119:50')
        self.assertEqual(parsed[1]['kind'], 'playlist')
        self.assertEqual(parsed[1]['title'], 'Nujabes relax LO-FI')
        self.assertEqual(parsed[1]['url'], 'https://www.youtube.com/playlist?list=PLTOLG4HoV_HZBwO9uP49QZ5TshUUaAq5x')

    def test_parse_ytfzf_ansi_and_html_entities(self):
        raw = (
            '\x1b[2K\r'
            + json.dumps([
                {
                    'ID': 'abc12345',
                    'title': '\x1b[32mTom &amp; Jerry &#39;Special&#39;   Mix\x1b[0m',
                    'url': 'https://youtube.com/watch?v=abc12345&amp;feature=share',
                    'channel': 'Jazz &amp; Soul Club',
                    'duration': '\x1b[1m45:10\x1b[0m',
                }
            ])
            + '\x1b[0m\n'
        )
        parsed = radio.parse_ytfzf_output(raw)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['title'], "Tom & Jerry 'Special' Mix")
        self.assertEqual(parsed[0]['channel'], "Jazz & Soul Club")
        self.assertEqual(parsed[0]['duration'], "45:10")
        self.assertEqual(parsed[0]['url'], "https://youtube.com/watch?v=abc12345&feature=share")
        self.assertEqual(parsed[0]['subtitle'], "Jazz & Soul Club · 45:10")

    def test_parse_ytfzf_malformed_input(self):
        self.assertEqual(radio.parse_ytfzf_output(''), [])
        self.assertEqual(radio.parse_ytfzf_output('   '), [])
        self.assertEqual(radio.parse_ytfzf_output('some random text without json'), [])
        mixed = 'Random header\n[{"ID": "1", "title": "Good Item", "url": "https://youtube.com/watch?v=1"}]\nTrailing footer'
        parsed = radio.parse_ytfzf_output(mixed)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['title'], "Good Item")

    def test_saved_items_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / 'radio.json'
            self.assertEqual(radio.load_saved(cfg), [])
            entry = radio.add_saved_item({
                'title': 'Jazz Hop Playlist',
                'subtitle': 'ChilledCow · 50 videos',
                'url': 'https://www.youtube.com/playlist?list=PL12345',
            }, path=cfg)
            self.assertEqual(entry['kind'], 'playlist')
            saved = radio.load_saved(cfg)
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]['title'], 'Jazz Hop Playlist')
            self.assertTrue(radio.remove_saved_item('https://www.youtube.com/playlist?list=PL12345', path=cfg))
            self.assertEqual(radio.load_saved(cfg), [])

    def test_state_resets_dead_pid(self):
        with tempfile.TemporaryDirectory() as tmp:
            st_path = Path(tmp) / 'state.json'
            radio.write_state({
                'active': True,
                'playing': True,
                'pid': 99999999,
                'title': 'Nightwave Plaza',
            }, path=st_path)
            loaded = radio.load_state(st_path)
            self.assertFalse(loaded['active'])
            self.assertEqual(loaded['pid'], 0)

            # Phantom active state with pid 0 must also be reset
            radio.write_state({
                'active': True,
                'playing': True,
                'pid': 0,
                'title': 'Ghost Stream',
            }, path=st_path)
            loaded = radio.load_state(st_path)
            self.assertFalse(loaded['active'])
            self.assertEqual(loaded['pid'], 0)

    def test_resolve_play_item_schemeless_url(self):
        resolved = radio.resolve_play_item('youtube.com/watch?v=12345')
        self.assertEqual(resolved['url'], 'https://youtube.com/watch?v=12345')
        self.assertEqual(resolved['kind'], 'youtube')

        resolved_pl = radio.resolve_play_item('youtube.com/playlist?list=PL12345')
        self.assertEqual(resolved_pl['url'], 'https://youtube.com/playlist?list=PL12345')
        self.assertEqual(resolved_pl['kind'], 'playlist')

    def test_saved_item_removal_with_trailing_slash(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / 'radio.json'
            radio.add_saved_item({
                'title': 'Test Station',
                'url': 'https://example.com/stream/',
            }, path=cfg)
            self.assertEqual(len(radio.load_saved(cfg)), 1)
            # Remove using URL without trailing slash
            self.assertTrue(radio.remove_saved_item('https://example.com/stream', path=cfg))
            self.assertEqual(len(radio.load_saved(cfg)), 0)

    def test_parse_ytfzf_relative_and_http_urls(self):
        raw = json.dumps([
            {
                'ID': '\x1b[33mrel123\x1b[0m',
                'title': 'Relative Video',
                'url': '/watch?v=rel123',
                'channel': 'Rel Channel',
                'duration': '10:00',
            },
            {
                'ID': 'http123',
                'title': 'HTTP Video',
                'url': 'http://youtube.com/watch?v=http123',
                'channel': 'HTTP Channel',
                'duration': '20:00',
            },
        ])
        parsed = radio.parse_ytfzf_output(raw)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['url'], 'https://www.youtube.com/watch?v=rel123')
        self.assertEqual(parsed[0]['id'], 'yt-rel123')
        self.assertEqual(parsed[1]['url'], 'https://www.youtube.com/watch?v=http123')

    def test_match_station_youtube_id_and_short_url(self):
        # Pe_zj-WZotg is the YouTube ID of rnb-slowjam
        matched_id = radio.match_station('Pe_zj-WZotg')
        self.assertIsNotNone(matched_id)
        self.assertEqual(matched_id['id'], 'rnb-slowjam')

        matched_short = radio.match_station('https://youtu.be/Pe_zj-WZotg')
        self.assertIsNotNone(matched_short)
        self.assertEqual(matched_short['id'], 'rnb-slowjam')

        resolved_short = radio.resolve_play_item('youtu.be/Pe_zj-WZotg')
        self.assertEqual(resolved_short['id'], 'rnb-slowjam')
        self.assertEqual(resolved_short['title'], '2000s R&B Slow Jam Mix')

        resolved_full = radio.resolve_play_item('youtube.com/watch?v=Pe_zj-WZotg')
        self.assertEqual(resolved_full['id'], 'rnb-slowjam')

    def test_saved_item_removal_with_youtube_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / 'radio.json'
            radio.add_saved_item({
                'title': 'My Vinyl Set',
                'url': 'https://www.youtube.com/watch?v=Pe_zj-WZotg',
            }, path=cfg)
            self.assertEqual(len(radio.load_saved(cfg)), 1)
            # Remove using bare video ID or short URL
            self.assertTrue(radio.remove_saved_item('Pe_zj-WZotg', path=cfg))
            self.assertEqual(len(radio.load_saved(cfg)), 0)

    def test_resolve_play_item_invalid_raises(self):
        with self.assertRaises(ValueError):
            radio.resolve_play_item('nonexistent_station_or_random_text')

    def test_main_value_error_handling(self):
        code = radio.main(['play', 'nonexistent_station_xyz'])
        self.assertEqual(code, 1)


if __name__ == '__main__':
    unittest.main()

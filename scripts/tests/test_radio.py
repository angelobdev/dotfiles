#!/usr/bin/env python3
"""radio.py: the station catalog, ytfzf and yt-dlp results, saved items, state, and the radio's own mpv only."""
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import radio  # noqa: E402

STATIONS = REPO / 'shell/.local/share/desktop/radio/stations.json'


class Sandbox(unittest.TestCase):
    """The shipped stations from this repository; the user's config and the runtime folder in a temporary one."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.runtime = self.root / 'run'
        self.runtime.mkdir()
        for patcher in (mock.patch.object(radio, 'SHIPPED', STATIONS),
                        mock.patch.object(radio, 'config_path', return_value=self.root / 'radio.json'),
                        mock.patch.object(radio, 'runtime_dir', return_value=self.runtime),
                        mock.patch.object(radio, 'tr', side_effect=lambda key, args=(): ' '.join([key, *map(str, args)]))):
            patcher.start()
            self.addCleanup(patcher.stop)


class RadioTests(Sandbox):
    def test_station_catalog_and_aliases(self):
        categories, stations = radio.catalog()
        self.assertGreaterEqual(len(stations), 20)
        self.assertEqual(categories, ['jazz', 'dreamwave', 'lofi', 'rnb'])
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
        # youtube.com becomes www.youtube.com, as for every other result.
        self.assertEqual(parsed[0]['url'], "https://www.youtube.com/watch?v=abc12345&feature=share")
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
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(radio.main(['play', 'nonexistent_station_xyz']), 1)
            self.assertEqual(radio.main(['nonexistent_command']), 2)


class CatalogTests(Sandbox):
    def test_own_stations_replace_and_add(self):
        own = {'stations': [
            {'id': 'plaza', 'title': 'My Plaza', 'category': 'dreamwave', 'url': 'https://example.com/plaza.mp3'},
            {'id': 'mine', 'title': 'Mine', 'category': 'talk', 'url': 'https://example.com/talk.mp3'},
            {'id': 'bad', 'title': 'An option, not a URL', 'url': '--script=/tmp/x.lua'},
            {'title': 'No id', 'url': 'https://example.com/x'},
        ]}
        (self.root / 'radio.json').write_text(json.dumps(own))
        categories, stations = radio.catalog()
        by_id = {item['id']: item for item in stations}
        self.assertEqual(by_id['plaza']['title'], 'My Plaza')
        self.assertEqual(by_id['mine']['kind'], 'radio')
        self.assertNotIn('bad', by_id)
        self.assertEqual(categories[-1], 'talk')

    def test_saving_keeps_the_own_stations(self):
        (self.root / 'radio.json').write_text(json.dumps({'stations': [{'id': 'mine', 'url': 'https://example.com/a'}]}))
        radio.add_saved_item({'title': 'Set', 'url': 'https://www.youtube.com/watch?v=Pe_zj-WZotg'})
        data = json.loads((self.root / 'radio.json').read_text())
        self.assertEqual(data['stations'][0]['id'], 'mine')
        self.assertEqual(len(data['saved']), 1)


class PlayTests(Sandbox):
    def test_only_streams_links_and_files_reach_mpv(self):
        for item in ({'url': '--script=/tmp/x.lua'}, '{"url": "--script=/tmp/x.lua"}', {'url': 'javascript:alert(1)'}):
            with self.assertRaises(ValueError):
                radio.resolve_play_item(item)
        song = self.root / 'song.ogg'
        song.write_bytes(b'')
        self.assertEqual(radio.resolve_play_item(str(song))['url'], str(song))

    def test_the_url_comes_after_the_options(self):
        with mock.patch.object(radio, 'stop_playback'), mock.patch('subprocess.Popen') as popen:
            popen.return_value.pid = 4242
            state = radio.play_target({'id': 'x', 'title': 'Station', 'url': 'https://example.com/s.mp3'})
        command = popen.call_args.args[0]
        self.assertEqual(command[-2:], ['--', 'https://example.com/s.mp3'])
        self.assertIn(f'--input-ipc-server={self.runtime / "radio-mpv.sock"}', command)
        self.assertFalse(any(part.startswith('--force-media-title') for part in command))
        self.assertEqual((state['pid'], state['active']), (4242, True))

    def test_without_mpv(self):
        with mock.patch.object(radio, 'stop_playback'), mock.patch('subprocess.Popen', side_effect=FileNotFoundError):
            with self.assertRaisesRegex(ValueError, 'radio.errors.noMpv'):
                radio.play_target({'url': 'https://example.com/s.mp3'})


class OwnMpvTests(Sandbox):
    """The radio talks to its own mpv only: another mpv, with a socket of its own, is never touched."""

    def serve(self, path, replies):
        # A stand-in mpv: answers each request with an event first, then the reply carrying its request_id.
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(path))
        server.listen(4)
        received = []

        def loop():
            while True:
                try:
                    connection, _ = server.accept()
                except OSError:
                    return
                with connection:
                    request = json.loads(connection.recv(4096).decode().splitlines()[0])
                    received.append(request['command'])
                    reply = replies.get(request['command'][-1], {'error': 'success'})
                    connection.sendall(b'{"event":"property-change","name":"pause"}\n'
                                       + json.dumps({**reply, 'request_id': request['request_id']}).encode() + b'\n')

        threading.Thread(target=loop, daemon=True).start()
        self.addCleanup(server.close)
        return received

    def test_commands_go_to_the_radio_socket_only(self):
        own = self.serve(self.runtime / 'radio-mpv.sock', {})
        other = self.serve(self.runtime / 'mpv-1234.sock', {})
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(radio.main(['toggle']), 0)
            self.assertEqual(radio.main(['next']), 0)
        self.assertIn(['cycle', 'pause'], own)
        self.assertIn(['playlist-next', 'weak'], own)
        self.assertEqual(other, [])

    def test_stop_quits_only_its_own_mpv(self):
        own = self.serve(self.runtime / 'radio-mpv.sock', {})
        other = self.serve(self.runtime / 'mpv-1234.sock', {})
        import subprocess
        player = subprocess.Popen(['sleep', '30'])
        self.addCleanup(player.kill)
        radio.write_state({'active': True, 'pid': player.pid, 'socket': str(self.runtime / 'radio-mpv.sock')})
        radio.stop_playback()
        self.assertIsNotNone(player.wait(timeout=5))
        self.assertEqual(own, [['quit']])
        self.assertEqual(other, [])
        self.assertFalse(radio.load_state()['active'])

    def test_live_title_and_pause(self):
        self.serve(self.runtime / 'radio-mpv.sock', {
            'media-title': {'error': 'success', 'data': 'Artist &amp; Track'},
            'pause': {'error': 'success', 'data': True},
            'vid': {'error': 'success', 'data': False},
        })
        import os
        radio.write_state({'active': True, 'pid': os.getpid(), 'title': 'Station', 'socket': str(self.runtime / 'radio-mpv.sock')})
        state = radio.live_state()
        self.assertEqual((state['title'], state['paused'], state['playing']), ('Artist & Track', True, False))

    def test_no_mpv_no_reply(self):
        self.assertIsNone(radio.mpv_ipc(['get_property', 'pause']))


class VideoTests(Sandbox):
    """The picture plays in the panel: handoff pauses mpv and gives one stream from where it was; resume gives back."""

    def handoff(self, state, properties, stream_lines='https://rr1.googlevideo.com/videoplayback?x\n', code=0):
        import subprocess
        values = {'time-pos': 95.5, 'media-title': 'Track', **properties}
        with mock.patch.object(radio, 'live_state', return_value=radio.default_state() | state), \
                mock.patch.object(radio, 'mpv_property', side_effect=lambda name: values.get(name)), \
                mock.patch.object(radio, 'mpv_ipc') as ipc, mock.patch.object(radio.shutil, 'which', return_value='/usr/bin/yt-dlp'), \
                mock.patch('subprocess.run', return_value=subprocess.CompletedProcess([], code, stream_lines, '')) as run:
            result = radio.handoff()
        return result, ipc, run

    def test_a_youtube_item_gives_one_stream_from_where_mpv_was(self):
        result, ipc, run = self.handoff({'active': True, 'kind': 'youtube', 'url': 'https://www.youtube.com/watch?v=Pe_zj-WZotg'},
                                        {'path': 'https://www.youtube.com/watch?v=Pe_zj-WZotg'})
        self.assertEqual(result, {'stream': 'https://rr1.googlevideo.com/videoplayback?x', 'position': 95.5, 'title': 'Track'})
        command = run.call_args.args[0]
        self.assertEqual(command[-2:], ['--', 'https://www.youtube.com/watch?v=Pe_zj-WZotg'])
        self.assertIn('best[vcodec!=none][acodec!=none]', command)
        ipc.assert_called_once_with(['set_property', 'pause', True])

    def test_the_item_of_a_playlist(self):
        _, _, run = self.handoff({'active': True, 'kind': 'playlist', 'url': 'https://www.youtube.com/playlist?list=PL1'},
                                 {'path': 'ytdl://Pe_zj-WZotg'})
        self.assertEqual(run.call_args.args[0][-1], 'https://www.youtube.com/watch?v=Pe_zj-WZotg')

    def test_a_file_plays_as_is(self):
        result, _, run = self.handoff({'active': True, 'kind': 'file', 'url': '/music/clip.mkv'}, {'path': '/music/clip.mkv'})
        self.assertEqual(result['stream'], 'file:///music/clip.mkv')
        run.assert_not_called()

    def test_a_web_radio_or_no_stream_keeps_mpv_playing(self):
        for state, lines, code in (({'active': True, 'kind': 'radio', 'url': 'https://radio.plaza.one/mp3'}, '', 0),
                                   ({'active': True, 'kind': 'youtube', 'url': 'https://www.youtube.com/watch?v=Pe_zj-WZotg'}, '', 1)):
            with self.assertRaisesRegex(ValueError, 'radio.errors.noVideo'):
                _, ipc, _ = self.handoff(state, {}, stream_lines=lines, code=code)

    def test_resume_seeks_and_plays(self):
        import contextlib
        import io
        with mock.patch.object(radio, 'mpv_ipc') as ipc, mock.patch.object(radio, 'live_state', return_value={}), \
                contextlib.redirect_stdout(io.StringIO()):
            radio.main(['resume', '125'])
            radio.main(['resume', '--1'])
        self.assertEqual(ipc.call_args_list[0].args[0], ['seek', 125.0, 'absolute'])
        self.assertEqual(ipc.call_args_list[1].args[0], ['set_property', 'pause', False])
        # Not a number: no seek, only play.
        self.assertEqual(ipc.call_args_list[2].args[0], ['set_property', 'pause', False])

    def test_mpv_plays_sound_only(self):
        with mock.patch.object(radio, 'stop_playback'), mock.patch('subprocess.Popen') as popen:
            popen.return_value.pid = 1
            radio.play_target({'url': 'https://www.youtube.com/watch?v=Pe_zj-WZotg'})
        self.assertIn('--no-video', popen.call_args.args[0])

if __name__ == '__main__':
    unittest.main()

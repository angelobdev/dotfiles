#!/usr/bin/env python3
"""Web radio, vinyl mixes, YouTube search (ytfzf/yt-dlp), and mpv MPRIS2 D-Bus bridge."""
from common import write_atomic
import html
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid

ANSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

STATIONS = [
    # Jazz & Vinyl (camino.sh & radio)
    {
        'id': 'linn-jazz',
        'aliases': ['linn', 'linnjazz'],
        'title': 'Linn Jazz',
        'subtitle': 'Audiophile Web Radio · 320 kbps',
        'category': 'jazz',
        'kind': 'radio',
        'url': 'http://radio.linn.co.uk:8000/autodj',
    },
    {
        'id': 'swiss-jazz',
        'aliases': ['swiss', 'swissjazz', 'rsj'],
        'title': 'Radio Swiss Jazz',
        'subtitle': 'Live Web Radio · 24/7',
        'category': 'jazz',
        'kind': 'radio',
        'url': 'http://stream.srg-ssr.ch/m/rsj/mp3_128',
    },
    {
        'id': 'rmc-jazz',
        'aliases': ['rmcjazz'],
        'title': 'Radio Monte Carlo Jazz',
        'subtitle': 'Live Web Radio · RMC Jazz',
        'category': 'jazz',
        'kind': 'radio',
        'url': 'https://icy.unitedradio.it/rmcweb019',
    },
    {
        'id': 'bluenote',
        'aliases': ['bop', 'hardbop'],
        'title': 'Blue Note Hours — Hard Bop Classics',
        'subtitle': 'Vinyl Set · Hard Bop Classics',
        'category': 'jazz',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=_nZyKKJEMUI',
    },
    {
        'id': 'coulou',
        'aliases': ['vinylcafe'],
        'title': "Coulou's Vinyl Cafe — Jazz Selections",
        'subtitle': 'Vinyl DJ Set · Jazz Selections',
        'category': 'jazz',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=ziOus5-1kXw',
    },
    # Dreamwave & Chillsynth (dreamwave.sh & radio)
    {
        'id': 'plaza',
        'aliases': ['nightwave', 'vaporwave'],
        'title': 'Nightwave Plaza',
        'subtitle': 'Live Web Radio · Vaporwave & Ethereal',
        'category': 'dreamwave',
        'kind': 'radio',
        'url': 'https://radio.plaza.one/mp3',
    },
    {
        'id': 'nightride',
        'aliases': ['chillsynth'],
        'title': 'Nightride FM Chillsynth',
        'subtitle': 'Live Web Radio · 24/7 Chillsynth',
        'category': 'dreamwave',
        'kind': 'radio',
        'url': 'https://stream.nightride.fm/chillsynth.mp3',
    },
    {
        'id': 'prettychill',
        'aliases': ['vinylchill'],
        'title': 'Pretty Chill — All-Vinyl Chillsynth Set',
        'subtitle': 'Vinyl DJ Set · Big Baby Profit',
        'category': 'dreamwave',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=5oTUjK6mnzA',
    },
    {
        'id': 'bliss',
        'aliases': ['chillwave'],
        'title': 'Bliss — Vinyl Chillsynth & Chillwave',
        'subtitle': 'Vinyl DJ Set · Big Baby Profit',
        'category': 'dreamwave',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=UjKQ0cwcr2k',
    },
    {
        'id': 'ambient-dreamcore',
        'aliases': ['dreamcore', 'oneheart'],
        'title': 'Ambient Dreamcore Mix',
        'subtitle': 'øneheart, antent, reidenshi, tilekid',
        'category': 'dreamwave',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=NaZeslUINF4',
    },
    # Lo-Fi & Boom Bap (lofi.sh, radio & ytMix)
    {
        'id': 'laut-lofi',
        'aliases': ['lofi', 'radio-lofi'],
        'title': 'Lo-Fi Web Radio (Laut.fm)',
        'subtitle': 'Live Web Radio · Laut.fm',
        'category': 'lofi',
        'kind': 'radio',
        'url': 'https://stream.laut.fm/lofi',
    },
    {
        'id': 'nujabes',
        'aliases': ['ytmix'],
        'title': 'The Nujabes Compilation',
        'subtitle': 'Jazzhop & Chillhop Classics',
        'category': 'lofi',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=zKGrm4l62Wc',
    },
    {
        'id': 'jdilla',
        'aliases': ['dilla'],
        'title': 'J Dilla Instrumentals Mix (Vol. 1 & 2)',
        'subtitle': 'Boom Bap · Jedi1200',
        'category': 'lofi',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=B8FmQFpruSE',
    },
    {
        'id': 'mfdoom',
        'aliases': ['doom'],
        'title': 'Full Vinyl MF DOOM Tribute Set',
        'subtitle': 'Live Vinyl DJ Set',
        'category': 'lofi',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=Sxw4cltvJkE',
    },
    {
        'id': 'boombap',
        'aliases': ['madlib'],
        'title': 'Boom Bap Vinyl Mix',
        'subtitle': 'J Dilla, MF DOOM, Madlib, 9th Wonder',
        'category': 'lofi',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=FnvMmP-UCJc',
    },
    # 2000s R&B, Neo-Soul & Funk (rnb2000.sh & radio)
    {
        'id': 'rmc-rnb',
        'aliases': ['rmcrnb', 'radio-rnb'],
        'title': 'Radio Monte Carlo R&B',
        'subtitle': 'Live Web Radio · 24/7',
        'category': 'rnb',
        'kind': 'radio',
        'url': 'https://icy.unitedradio.it/rmcweb003',
    },
    {
        'id': 'capital-funk',
        'aliases': ['funk', 'funkytown', 'capital'],
        'title': 'Radio Capital Funky Town',
        'subtitle': 'Live Web Radio · Funk, Soul & R&B',
        'category': 'rnb',
        'kind': 'radio',
        'url': 'https://4c4b867c89244861ac216426883d1ad0.msvdn.net/radiocapitalfunkytown/radiocapitalfunkytown/play1.m3u8',
    },
    {
        'id': 'rnb-slowjam',
        'aliases': ['slowjam', 'rnb2000'],
        'title': '2000s R&B Slow Jam Mix',
        'subtitle': 'Live Mix · DJ SUMAIRU',
        'category': 'rnb',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=Pe_zj-WZotg',
    },
    {
        'id': 'neosoul-djni',
        'aliases': ['neosoul', 'badu', 'dangelo'],
        'title': 'Neo-Soul Classics DJ Set',
        'subtitle': "DJ Ni · Erykah Badu, D'Angelo, Maxwell",
        'category': 'rnb',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=K6en74gqBSM',
    },
    {
        'id': 'soulection',
        'aliases': ['soul'],
        'title': 'Soulection Soul & Edits Takeover',
        'subtitle': 'Soul, Classics, Edits & Samples',
        'category': 'rnb',
        'kind': 'youtube',
        'url': 'https://www.youtube.com/watch?v=LcN8QINjvWM',
    },
]


def runtime_dir():
    base = Path(os.environ.get('XDG_RUNTIME_DIR') or f'/tmp/runtime-{os.getuid()}')
    directory = base / 'desktop-shell'
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def state_path():
    return runtime_dir() / 'radio.json'


def radio_socket_path():
    return runtime_dir() / 'radio-mpv.sock'


def config_path():
    base = Path(os.environ.get('XDG_CONFIG_HOME') or (Path.home() / '.config'))
    return base / 'desktop' / 'radio.json'


def pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def load_saved(path=None):
    target = Path(path) if path else config_path()
    try:
        data = json.loads(target.read_text(encoding='utf-8'))
        items = data.get('saved', []) if isinstance(data, dict) else []
        return [item for item in items if isinstance(item, dict) and item.get('url')]
    except (OSError, ValueError):
        return []


def save_saved(items, path=None):
    target = Path(path) if path else config_path()
    write_atomic(target, json.dumps({'saved': items}, indent=2, ensure_ascii=False) + '\n')


def add_saved_item(raw_item, path=None):
    item = json.loads(raw_item) if isinstance(raw_item, str) else dict(raw_item)
    url = str(item.get('url') or '').strip()
    if not url:
        raise ValueError('Missing station URL')
    title = str(item.get('title') or url).strip()
    subtitle = str(item.get('subtitle') or '').strip()
    if not subtitle and (item.get('channel') or item.get('duration')):
        subtitle = ' · '.join(p for p in (item.get('channel'), item.get('duration')) if p)
    kind = str(item.get('kind') or ('playlist' if 'playlist?list=' in url else 'youtube')).strip()
    category = str(item.get('category') or 'saved').strip()
    item_id = str(item.get('id') or '').strip()
    if not item_id:
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:24] or 'saved'
        item_id = f'{slug}-{uuid.uuid4().hex[:6]}'
    items = load_saved(path)
    entry = {
        'id': item_id,
        'title': title,
        'subtitle': subtitle,
        'category': category,
        'kind': kind,
        'url': url,
        'saved': True,
    }
    replaced = False
    for index, existing in enumerate(items):
        if existing.get('url') == url or existing.get('id') == item_id:
            entry['id'] = existing.get('id') or item_id
            items[index] = entry
            replaced = True
            break
    if not replaced:
        items.insert(0, entry)
    save_saved(items, path)
    return entry


def youtube_id(url_or_id):
    if not url_or_id:
        return ''
    text = str(url_or_id).strip()
    match = re.search(r'(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})', text)
    if match:
        return match.group(1)
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', text):
        return text
    return ''


def remove_saved_item(identifier, path=None):
    items = load_saved(path)
    target = str(identifier).strip()
    target_strip = target.rstrip('/')
    norm_target = ('https://' + target) if target.startswith(('youtube.com/', 'www.youtube.com/', 'youtu.be/')) else target
    norm_strip = norm_target.rstrip('/')
    target_yt = youtube_id(target)
    filtered = []
    for item in items:
        item_id = str(item.get('id') or '')
        item_url = str(item.get('url') or '')
        item_strip = item_url.rstrip('/')
        if (
            item_id == target
            or item_url in (target, norm_target)
            or (item_strip and item_strip in (target_strip, norm_strip))
            or (target_yt and youtube_id(item_url) == target_yt)
        ):
            continue
        filtered.append(item)
    save_saved(filtered, path)
    return len(filtered) != len(items)


def default_state():
    return {
        'active': False,
        'playing': False,
        'paused': False,
        'pid': 0,
        'socket': '',
        'stationId': '',
        'title': '',
        'stationTitle': '',
        'subtitle': '',
        'url': '',
        'kind': '',
        'category': '',
        'video': False,
    }


def load_state(path=None):
    target = Path(path) if path else state_path()
    state = default_state()
    try:
        raw = json.loads(target.read_text(encoding='utf-8'))
        if isinstance(raw, dict):
            state.update(raw)
    except (OSError, ValueError):
        return state
    pid = state.get('pid', 0)
    sock = state.get('socket', '')
    if state.get('active') and (not pid or not pid_alive(pid)):
        if sock:
            Path(sock).unlink(missing_ok=True)
        state = default_state()
        try:
            write_atomic(target, json.dumps(state) + '\n')
        except OSError:
            pass
    return state


def write_state(state, path=None):
    target = Path(path) if path else state_path()
    merged = default_state()
    merged.update(state)
    write_atomic(target, json.dumps(merged, ensure_ascii=False) + '\n')
    return merged


def match_station(identifier_or_url, saved_items=None):
    if not identifier_or_url:
        return None
    needle = str(identifier_or_url).strip()
    needle_lower = needle.lower()
    needle_strip = needle.rstrip('/')
    needle_yt = youtube_id(needle)
    saved = saved_items if saved_items is not None else load_saved()
    for station in STATIONS + saved:
        st_url = str(station.get('url') or '')
        st_strip = st_url.rstrip('/')
        if (
            station.get('id', '').lower() == needle_lower
            or st_url == needle
            or (st_strip and st_strip == needle_strip)
            or (needle_yt and youtube_id(st_url) == needle_yt)
        ):
            return dict(station)
        for alias in station.get('aliases', []):
            if alias.lower() == needle_lower:
                return dict(station)
    return None


def active_sockets():
    state = load_state()
    candidates = []
    if state.get('socket') and Path(state['socket']).exists():
        candidates.append(Path(state['socket']))
    default_sock = radio_socket_path()
    if default_sock.exists() and default_sock not in candidates:
        candidates.append(default_sock)
    for sock in sorted(runtime_dir().glob('mpv-*.sock'), reverse=True):
        if sock not in candidates:
            candidates.append(sock)
    return candidates


def mpv_ipc(command, socket_path=None, timeout=1.5):
    targets = [Path(socket_path)] if socket_path else active_sockets()
    payload = (json.dumps({'command': command}) + '\n').encode('utf-8')
    for target in targets:
        if not target.exists():
            continue
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(timeout)
                client.connect(str(target))
                client.sendall(payload)
                buffer = b''
                while b'\n' not in buffer:
                    chunk = client.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk
                for line in buffer.decode('utf-8', errors='replace').splitlines():
                    msg = json.loads(line)
                    if 'error' in msg:
                        return msg
        except (OSError, ValueError):
            continue
    return None


def stop_playback():
    state = load_state()
    pid = state.get('pid', 0)
    sock = state.get('socket') or str(radio_socket_path())
    mpv_ipc(['quit'], socket_path=sock, timeout=0.5)
    for extra_sock in active_sockets():
        mpv_ipc(['quit'], socket_path=extra_sock, timeout=0.4)
    if pid and pid_alive(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        for _ in range(15):
            if not pid_alive(pid):
                break
            time.sleep(0.05)
        if pid_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    Path(sock).unlink(missing_ok=True)
    return write_state(default_state())


def resolve_play_item(target):
    if isinstance(target, dict):
        return dict(target)
    text = str(target).strip()
    if text.startswith('{') and text.endswith('}'):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and parsed.get('url'):
                return parsed
        except ValueError:
            pass
    if text.startswith(('youtube.com/', 'www.youtube.com/', 'm.youtube.com/', 'music.youtube.com/', 'youtu.be/')):
        text = 'https://' + text
    matched = match_station(text)
    if matched:
        return matched
    if text.startswith(('http://', 'https://', 'ytdl://', 'file://')) or Path(text).exists():
        kind = 'playlist' if 'playlist?list=' in text else ('youtube' if 'youtube.com/' in text or 'youtu.be/' in text else 'radio')
        return {
            'id': '',
            'title': text,
            'subtitle': 'Direct Stream',
            'category': 'custom',
            'kind': kind,
            'url': text,
        }
    raise ValueError(f'Unknown station or URL: {text}')


def play_target(target, video=False):
    item = resolve_play_item(target)
    url = item['url']
    title = item.get('title') or url
    subtitle = item.get('subtitle') or ''
    kind = item.get('kind') or ('playlist' if 'playlist?list=' in url else 'radio')
    category = item.get('category') or ''
    station_id = item.get('id') or ''

    stop_playback()
    sock = radio_socket_path()
    sock.unlink(missing_ok=True)

    cmd = [
        'mpv',
        f'--input-ipc-server={sock}',
        f'--force-media-title={title}',
        f'--title={title}',
        '--vid=' + ('auto' if video else 'no'),
    ]
    if not video:
        cmd.append('--no-video')
    if kind == 'playlist' or 'playlist?list=' in url:
        cmd.append('--ytdl-raw-options=yes-playlist=')
    cmd.append(url)

    child = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return write_state({
        'active': True,
        'playing': True,
        'paused': False,
        'pid': child.pid,
        'socket': str(sock),
        'stationId': station_id,
        'title': title,
        'stationTitle': title,
        'subtitle': subtitle,
        'url': url,
        'kind': kind,
        'category': category,
        'video': bool(video),
    })


def parse_ytfzf_output(raw_text, limit=20):
    if not raw_text or not str(raw_text).strip():
        return []
    clean_text = ANSI_RE.sub('', str(raw_text))
    decoder = json.JSONDecoder()
    pos = 0
    length = len(clean_text)
    raw_items = []
    while pos < length:
        match = re.search(r'[\[\{]', clean_text[pos:])
        if not match:
            break
        start = pos + match.start()
        try:
            obj, end = decoder.raw_decode(clean_text, start)
            if isinstance(obj, list):
                raw_items.extend(x for x in obj if isinstance(x, dict))
            elif isinstance(obj, dict):
                raw_items.append(obj)
            pos = end
        except ValueError:
            pos = start + 1

    results = []
    seen_urls = set()
    for item in raw_items:
        title = html.unescape(ANSI_RE.sub('', str(item.get('title') or ''))).strip()
        title = re.sub(r'\s+', ' ', title)
        url = html.unescape(ANSI_RE.sub('', str(item.get('url') or ''))).strip()
        item_id = ANSI_RE.sub('', str(item.get('ID') or '')).strip()
        action = str(item.get('action') or '')
        views = str(item.get('views') or '')
        channel = html.unescape(ANSI_RE.sub('', str(item.get('channel') or ''))).strip()
        channel = re.sub(r'\s+', ' ', channel)
        duration = ANSI_RE.sub('', str(item.get('duration') or '')).strip()

        if title == '[BACK]' or url == 'back' or title.startswith('[channel]') or 'invidious-channel' in action:
            continue

        is_playlist = (
            title.startswith('[playlist]')
            or views == 'playlist'
            or 'playlist' in action
            or 'playlist?list=' in url
        )
        if is_playlist:
            if title.startswith('[playlist]'):
                title = title[len('[playlist]'):].strip()
            if ('list=null' in url or not url or 'playlist?list=' not in url) and item_id:
                url = f'https://www.youtube.com/playlist?list={item_id}'
            elif url.startswith('https://youtube.com/'):
                url = 'https://www.youtube.com/' + url[len('https://youtube.com/'):]
            elif url.startswith('http://youtube.com/'):
                url = 'https://www.youtube.com/' + url[len('http://youtube.com/'):]
            elif url.startswith('http://www.youtube.com/'):
                url = 'https://www.youtube.com/' + url[len('http://www.youtube.com/'):]
            elif url.startswith(('/', 'playlist?', 'watch?')):
                url = 'https://www.youtube.com/' + url.lstrip('/')
            kind = 'playlist'
        else:
            if ('watch?v=null' in url or not url) and item_id:
                url = f'https://www.youtube.com/watch?v={item_id}'
            elif url.startswith('https://youtube.com/'):
                url = 'https://www.youtube.com/' + url[len('https://youtube.com/'):]
            elif url.startswith('http://youtube.com/'):
                url = 'https://www.youtube.com/' + url[len('http://youtube.com/'):]
            elif url.startswith('http://www.youtube.com/'):
                url = 'https://www.youtube.com/' + url[len('http://www.youtube.com/'):]
            elif url.startswith(('/', 'watch?', 'playlist?')):
                url = 'https://www.youtube.com/' + url.lstrip('/')
            kind = 'youtube'

        if not url or not title or url in seen_urls:
            continue
        seen_urls.add(url)

        details = [part for part in (channel, duration) if part and part != 'null']
        subtitle = ' · '.join(details) if details else ('YouTube Playlist' if kind == 'playlist' else 'YouTube')
        results.append({
            'id': f'yt-{item_id or uuid.uuid4().hex[:8]}',
            'title': title,
            'subtitle': subtitle,
            'channel': channel,
            'duration': duration,
            'category': 'youtube',
            'kind': kind,
            'url': url,
        })
        if len(results) >= limit:
            break
    return results


def search_ytdlp_fallback(query, search_type='all', limit=15):
    if not shutil.which('yt-dlp'):
        return []
    if search_type == 'playlist':
        from urllib.parse import quote_plus
        target = f'https://www.youtube.com/results?search_query={quote_plus(query)}&sp=EgIQAw%253D%253D'
    else:
        target = f'ytsearch{limit}:{query}'
    cmd = ['yt-dlp', '--flat-playlist', '--dump-json', '--no-warnings', '--playlist-end', str(limit), target]
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError):
        return []
    results = []
    seen = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except ValueError:
            continue
        entry_id = ANSI_RE.sub('', str(data.get('id') or '')).strip()
        title = html.unescape(ANSI_RE.sub('', str(data.get('title') or ''))).strip()
        title = re.sub(r'\s+', ' ', title)
        url = html.unescape(ANSI_RE.sub('', str(data.get('url') or data.get('webpage_url') or ''))).strip()
        ie_key = str(data.get('ie_key') or data.get('_type') or '').lower()
        is_playlist = search_type == 'playlist' or 'playlist' in ie_key or entry_id.startswith(('PL', 'OL', 'UU', 'RD'))
        if is_playlist and entry_id and 'playlist?list=' not in url:
            url = f'https://www.youtube.com/playlist?list={entry_id}'
        elif not url.startswith('http') and entry_id:
            url = f'https://www.youtube.com/watch?v={entry_id}'
        elif url.startswith('http://'):
            url = 'https://' + url[len('http://'):]
        if not title or not url or url in seen:
            continue
        seen.add(url)
        channel = html.unescape(ANSI_RE.sub('', str(data.get('channel') or data.get('uploader') or ''))).strip()
        channel = re.sub(r'\s+', ' ', channel)
        dur_val = data.get('duration')
        if isinstance(dur_val, (int, float)) and dur_val > 0:
            mins, secs = divmod(int(dur_val), 60)
            duration = f'{mins}:{secs:02d}'
        else:
            duration = ''
        details = [p for p in (channel, duration) if p]
        results.append({
            'id': f'yt-{entry_id or uuid.uuid4().hex[:8]}',
            'title': title,
            'subtitle': ' · '.join(details) if details else ('YouTube Playlist' if is_playlist else 'YouTube'),
            'channel': channel,
            'duration': duration,
            'category': 'youtube',
            'kind': 'playlist' if is_playlist else 'youtube',
            'url': url,
        })
        if len(results) >= limit:
            break
    return results


def search_youtube(query, search_type='all', limit=20):
    query = str(query or '').strip()
    if not query:
        return []
    if shutil.which('ytfzf'):
        type_arg = 'playlist' if search_type == 'playlist' else ('video' if search_type == 'video' else 'all')
        cmd = [
            'ytfzf',
            '-c', 'Y',
            '-A',
            '-I', 'VJ',
            '--info-exit',
            '--disable-actions',
            '--disable-submenus',
            f'--type={type_arg}',
            query,
        ]
        try:
            proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=12, check=False)
            parsed = parse_ytfzf_output(proc.stdout, limit=limit)
            if parsed:
                return parsed
        except (OSError, subprocess.SubprocessError):
            pass
    return search_ytdlp_fallback(query, search_type=search_type, limit=limit)


MPRIS_XML = """
<node>
  <interface name="org.mpris.MediaPlayer2">
    <method name="Raise"/>
    <method name="Quit"/>
    <property name="CanQuit" type="b" access="read"/>
    <property name="CanRaise" type="b" access="read"/>
    <property name="HasTrackList" type="b" access="read"/>
    <property name="Identity" type="s" access="read"/>
    <property name="DesktopEntry" type="s" access="read"/>
    <property name="SupportedUriSchemes" type="as" access="read"/>
    <property name="SupportedMimeTypes" type="as" access="read"/>
  </interface>
  <interface name="org.mpris.MediaPlayer2.Player">
    <method name="Next"/>
    <method name="Previous"/>
    <method name="Pause"/>
    <method name="PlayPause"/>
    <method name="Stop"/>
    <method name="Play"/>
    <method name="Seek">
      <arg direction="in" name="Offset" type="x"/>
    </method>
    <method name="SetPosition">
      <arg direction="in" name="TrackId" type="o"/>
      <arg direction="in" name="Position" type="x"/>
    </method>
    <method name="OpenUri">
      <arg direction="in" name="Uri" type="s"/>
    </method>
    <property name="PlaybackStatus" type="s" access="read"/>
    <property name="Rate" type="d" access="read"/>
    <property name="Metadata" type="a{sv}" access="read"/>
    <property name="Volume" type="d" access="readwrite"/>
    <property name="Position" type="x" access="read"/>
    <property name="MinimumRate" type="d" access="read"/>
    <property name="MaximumRate" type="d" access="read"/>
    <property name="CanGoNext" type="b" access="read"/>
    <property name="CanGoPrevious" type="b" access="read"/>
    <property name="CanPlay" type="b" access="read"/>
    <property name="CanPause" type="b" access="read"/>
    <property name="CanSeek" type="b" access="read"/>
    <property name="CanControl" type="b" access="read"/>
  </interface>
</node>
"""


def run_mpris_bridge(socket_file, mpv_pid=0):
    from gi.repository import Gio, GLib

    sock_path = Path(socket_file)
    for _ in range(50):
        if sock_path.exists():
            break
        if mpv_pid and not pid_alive(mpv_pid):
            return 0
        time.sleep(0.1)
    if not sock_path.exists():
        return 1

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(str(sock_path))
    except OSError:
        return 1
    client.setblocking(False)

    loop = GLib.MainLoop()
    node_info = Gio.DBusNodeInfo.new_for_xml(MPRIS_XML)

    state = {
        'pause': False,
        'media-title': '',
        'icy-title': '',
        'path': '',
        'duration': 0.0,
        'time-pos': 0.0,
        'volume': 100.0,
        'vid': 'no',
        'metadata': {},
    }
    station_info = {}
    initial_radio = load_state()
    if initial_radio.get('active') and (
        initial_radio.get('pid') == mpv_pid or initial_radio.get('socket') == str(sock_path)
    ):
        station_info = dict(initial_radio)

    dbus_conn = {'conn': None, 'reg_ids': []}
    last_emitted = {'status': None, 'meta_sig': None}

    def send_mpv(command):
        try:
            payload = (json.dumps({'command': command}) + '\n').encode('utf-8')
            client.sendall(payload)
        except OSError:
            pass

    def compute_display():
        nonlocal station_info
        path = str(state.get('path') or '')
        if path and not station_info.get('stationTitle'):
            matched = match_station(path)
            if matched:
                station_info = {
                    'stationId': matched.get('id', ''),
                    'stationTitle': matched.get('title', ''),
                    'subtitle': matched.get('subtitle', ''),
                    'kind': matched.get('kind', ''),
                    'category': matched.get('category', ''),
                    'url': path,
                }
        meta = state.get('metadata') if isinstance(state.get('metadata'), dict) else {}
        icy_title = html.unescape(str(state.get('icy-title') or meta.get('icy-title') or '')).strip()
        icy_name = html.unescape(str(meta.get('icy-name') or '')).strip()
        media_title = html.unescape(str(state.get('media-title') or '')).strip()
        station_title = str(station_info.get('stationTitle') or '').strip()
        station_sub = str(station_info.get('subtitle') or '').strip()
        uploader = html.unescape(str(meta.get('uploader') or meta.get('artist') or meta.get('ARTIST') or '')).strip()

        if icy_title:
            track_title = icy_title
            artist = station_title or icy_name or station_sub or 'Web Radio'
        elif station_title:
            if media_title and media_title != station_title and not media_title.startswith(('http://', 'https://')):
                track_title = media_title
                artist = station_title
            else:
                track_title = station_title
                artist = uploader or station_sub or icy_name or 'Radio'
        else:
            track_title = media_title or Path(path).name or 'mpv'
            artist = uploader or icy_name or 'mpv'
        return track_title, artist, station_title or track_title, station_sub or artist

    def build_metadata():
        track_title, artist, station_title, _ = compute_display()
        meta = {
            'mpris:trackid': GLib.Variant('o', '/org/mpris/MediaPlayer2/Track/1'),
            'xesam:title': GLib.Variant('s', track_title),
            'xesam:artist': GLib.Variant('as', [artist] if artist else ['mpv']),
            'xesam:album': GLib.Variant('s', station_title),
        }
        if state.get('path'):
            meta['xesam:url'] = GLib.Variant('s', str(state['path']))
        duration = float(state.get('duration') or 0.0)
        if duration > 0:
            meta['mpris:length'] = GLib.Variant('x', int(duration * 1_000_000))
        return meta

    def playback_status():
        return 'Paused' if state.get('pause') else 'Playing'

    def sync_radio_state():
        track_title, artist, station_title, subtitle = compute_display()
        current = load_state()
        is_radio_sock = str(sock_path) == str(radio_socket_path())
        if not is_radio_sock and current.get('active') and current.get('pid') not in (0, mpv_pid):
            return
        vid_val = state.get('vid')
        has_video = vid_val not in ('no', False, None, 'false', 0)
        url = str(state.get('path') or station_info.get('url') or '')
        write_state({
            'active': True,
            'playing': not bool(state.get('pause')),
            'paused': bool(state.get('pause')),
            'pid': mpv_pid or os.getppid(),
            'socket': str(sock_path),
            'stationId': station_info.get('stationId', ''),
            'title': track_title,
            'stationTitle': station_title,
            'subtitle': subtitle or artist,
            'url': url,
            'kind': station_info.get('kind') or ('playlist' if 'playlist?list=' in url else 'radio'),
            'category': station_info.get('category', ''),
            'video': has_video,
        })

    def emit_changes(force=False):
        conn = dbus_conn['conn']
        status = playback_status()
        meta = build_metadata()
        sig = (
            status,
            meta['xesam:title'].unpack(),
            tuple(meta['xesam:artist'].unpack()),
            int(float(state.get('duration') or 0.0)),
            bool(state.get('vid') not in ('no', False, None, 'false', 0)),
        )
        if not force and sig == last_emitted['meta_sig']:
            return
        last_emitted['meta_sig'] = sig
        sync_radio_state()
        if conn is None:
            return
        changed = {
            'PlaybackStatus': GLib.Variant('s', status),
            'Metadata': GLib.Variant('a{sv}', meta),
            'CanSeek': GLib.Variant('b', float(state.get('duration') or 0.0) > 0),
        }
        try:
            conn.emit_signal(
                None,
                '/org/mpris/MediaPlayer2',
                'org.freedesktop.DBus.Properties',
                'PropertiesChanged',
                GLib.Variant('(sa{sv}as)', ('org.mpris.MediaPlayer2.Player', changed, [])),
            )
        except Exception:
            pass

    def handle_method_call(_conn, _sender, _path, interface, method, params, invocation):
        if interface == 'org.mpris.MediaPlayer2':
            if method == 'Quit':
                send_mpv(['quit'])
            invocation.return_value(None)
            return
        if method == 'Play':
            send_mpv(['set_property', 'pause', False])
        elif method == 'Pause':
            send_mpv(['set_property', 'pause', True])
        elif method == 'PlayPause':
            send_mpv(['cycle', 'pause'])
        elif method == 'Stop':
            send_mpv(['quit'])
        elif method == 'Next':
            send_mpv(['playlist-next', 'weak'])
        elif method == 'Previous':
            send_mpv(['playlist-prev', 'weak'])
        elif method == 'Seek':
            offset_us = params.unpack()[0]
            send_mpv(['seek', offset_us / 1_000_000.0, 'relative'])
        elif method == 'SetPosition':
            _track_id, pos_us = params.unpack()
            send_mpv(['seek', pos_us / 1_000_000.0, 'absolute'])
        elif method == 'OpenUri':
            uri = params.unpack()[0]
            send_mpv(['loadfile', uri])
        invocation.return_value(None)

    def handle_get_property(_conn, _sender, _path, interface, prop):
        if interface == 'org.mpris.MediaPlayer2':
            root_props = {
                'CanQuit': GLib.Variant('b', True),
                'CanRaise': GLib.Variant('b', False),
                'HasTrackList': GLib.Variant('b', False),
                'Identity': GLib.Variant('s', 'mpv'),
                'DesktopEntry': GLib.Variant('s', 'desktop-radio'),
                'SupportedUriSchemes': GLib.Variant('as', ['http', 'https', 'file', 'ytdl']),
                'SupportedMimeTypes': GLib.Variant('as', ['audio/mpeg', 'audio/ogg', 'audio/flac', 'video/mp4']),
            }
            return root_props.get(prop)
        player_props = {
            'PlaybackStatus': GLib.Variant('s', playback_status()),
            'Rate': GLib.Variant('d', 1.0),
            'MinimumRate': GLib.Variant('d', 1.0),
            'MaximumRate': GLib.Variant('d', 1.0),
            'Metadata': GLib.Variant('a{sv}', build_metadata()),
            'Volume': GLib.Variant('d', max(0.0, float(state.get('volume') or 100.0) / 100.0)),
            'Position': GLib.Variant('x', int(float(state.get('time-pos') or 0.0) * 1_000_000)),
            'CanGoNext': GLib.Variant('b', True),
            'CanGoPrevious': GLib.Variant('b', True),
            'CanPlay': GLib.Variant('b', True),
            'CanPause': GLib.Variant('b', True),
            'CanSeek': GLib.Variant('b', float(state.get('duration') or 0.0) > 0),
            'CanControl': GLib.Variant('b', True),
        }
        return player_props.get(prop)

    def handle_set_property(_conn, _sender, _path, _interface, prop, value):
        if prop == 'Volume':
            vol = max(0.0, min(150.0, float(value.unpack()) * 100.0))
            send_mpv(['set_property', 'volume', vol])
            return True
        return False

    def on_bus_acquired(conn, _name):
        dbus_conn['conn'] = conn
        for iface in node_info.interfaces:
            reg_id = conn.register_object(
                '/org/mpris/MediaPlayer2',
                iface,
                handle_method_call,
                handle_get_property,
                handle_set_property,
            )
            dbus_conn['reg_ids'].append(reg_id)
        emit_changes(force=True)

    rx_buffer = {'data': b''}

    def on_socket_readable(_fd, condition):
        if condition & (GLib.IO_HUP | GLib.IO_ERR):
            loop.quit()
            return False
        try:
            chunk = client.recv(8192)
        except BlockingIOError:
            return True
        except OSError:
            loop.quit()
            return False
        if not chunk:
            loop.quit()
            return False
        rx_buffer['data'] += chunk
        while b'\n' in rx_buffer['data']:
            line, rx_buffer['data'] = rx_buffer['data'].split(b'\n', 1)
            try:
                msg = json.loads(line.decode('utf-8', errors='replace'))
            except ValueError:
                continue
            event = msg.get('event')
            if event == 'property-change':
                prop_name = msg.get('name')
                if prop_name in state:
                    data = msg.get('data')
                    if data is None:
                        if prop_name in ('media-title', 'icy-title', 'path'):
                            state[prop_name] = ''
                        elif prop_name == 'vid':
                            state[prop_name] = 'no'
                        elif prop_name in ('duration', 'time-pos'):
                            state[prop_name] = 0.0
                        elif prop_name == 'pause':
                            state[prop_name] = False
                        elif prop_name == 'metadata':
                            state[prop_name] = {}
                    else:
                        state[prop_name] = data
                    if prop_name != 'time-pos':
                        emit_changes()
            elif event == 'shutdown':
                loop.quit()
                return False
        return True

    for idx, prop in enumerate(
        ('pause', 'media-title', 'icy-title', 'path', 'duration', 'time-pos', 'volume', 'vid', 'metadata'),
        start=1,
    ):
        send_mpv(['observe_property', idx, prop])

    bus_id = mpv_pid or os.getpid()
    owner_id = Gio.bus_own_name(
        Gio.BusType.SESSION,
        f'org.mpris.MediaPlayer2.mpv.instance{bus_id}',
        Gio.BusNameOwnerFlags.NONE,
        on_bus_acquired,
        None,
        None,
    )

    GLib.unix_fd_add_full(
        GLib.PRIORITY_DEFAULT,
        client.fileno(),
        GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR,
        on_socket_readable,
    )

    def check_parent():
        if mpv_pid and not pid_alive(mpv_pid):
            loop.quit()
            return False
        return True

    GLib.timeout_add(1000, check_parent)

    def quit_cleanly(*_):
        loop.quit()

    signal.signal(signal.SIGTERM, quit_cleanly)
    signal.signal(signal.SIGINT, quit_cleanly)

    try:
        loop.run()
    finally:
        Gio.bus_unown_name(owner_id)
        try:
            client.close()
        except OSError:
            pass
        sock_path.unlink(missing_ok=True)
        current = load_state()
        if current.get('pid') == mpv_pid or current.get('socket') == str(sock_path):
            write_state(default_state())
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else 'list'

    try:
        if cmd == 'list':
            print(json.dumps({
                'stations': STATIONS,
                'saved': load_saved(),
                'state': load_state(),
            }, ensure_ascii=False))
            return 0

        if cmd == 'status':
            print(json.dumps(load_state(), ensure_ascii=False))
            return 0

        if cmd == 'play':
            if len(args) < 2:
                sys.stderr.write('Usage: radio.py play <station-id|url|json> [--video]\n')
                return 2
            video = '--video' in args[2:]
            state = play_target(args[1], video=video)
            print(json.dumps(state, ensure_ascii=False))
            return 0

        if cmd == 'stop':
            state = stop_playback()
            print(json.dumps(state, ensure_ascii=False))
            return 0

        if cmd == 'toggle':
            mpv_ipc(['cycle', 'pause'])
            time.sleep(0.05)
            print(json.dumps(load_state(), ensure_ascii=False))
            return 0

        if cmd == 'next':
            mpv_ipc(['playlist-next', 'weak'])
            return 0

        if cmd == 'previous':
            mpv_ipc(['playlist-prev', 'weak'])
            return 0

        if cmd == 'video':
            mode = args[1] if len(args) > 1 else 'toggle'
            state = load_state()
            if mode == 'toggle':
                enable = not bool(state.get('video'))
            else:
                enable = mode in ('on', 'true', '1', 'auto')
            mpv_ipc(['set_property', 'vid', 'auto' if enable else 'no'])
            if state.get('active'):
                state['video'] = enable
                write_state(state)
            print(json.dumps(state, ensure_ascii=False))
            return 0

        if cmd == 'search':
            query = args[1] if len(args) > 1 else ''
            search_type = args[2] if len(args) > 2 else 'all'
            results = search_youtube(query, search_type=search_type)
            print(json.dumps({'results': results}, ensure_ascii=False))
            return 0

        if cmd == 'save':
            if len(args) < 2:
                return 2
            entry = add_saved_item(args[1])
            print(json.dumps({'saved': load_saved(), 'entry': entry}, ensure_ascii=False))
            return 0

        if cmd == 'remove':
            if len(args) < 2:
                return 2
            remove_saved_item(args[1])
            print(json.dumps({'saved': load_saved()}, ensure_ascii=False))
            return 0

        if cmd == 'mpris':
            if len(args) < 2:
                return 2
            pid = int(args[2]) if len(args) > 2 and args[2].isdigit() else 0
            return run_mpris_bridge(args[1], pid)

        matched = match_station(cmd)
        if matched:
            video = '--video' in args[1:]
            state = play_target(matched, video=video)
            print(json.dumps(state, ensure_ascii=False))
            return 0
    except ValueError as error:
        sys.stderr.write(f'{error}\n')
        return 1

    sys.stderr.write(f'Unknown radio command: {cmd}\n')
    return 2


if __name__ == '__main__':
    sys.exit(main())

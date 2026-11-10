#!/usr/bin/env python3
"""Radio & music for the shell's Radio panel (Super + M) and desktop-radio: web radio stations, DJ sets and YouTube
search (ytfzf, else yt-dlp), played by one mpv of its own. mpv-mpris (the radio profile) puts that mpv on MPRIS, so
the bar, the Control Center, the lock screen and the media keys follow it like any player.

Stations: ~/.local/share/desktop/radio/stations.json (shipped), then "stations" in ~/.config/desktop/radio.json, whose
entries replace a shipped one with the same id or add to them; "saved" there holds what the panel pins.

list: the categories, stations, saved items and state, as JSON.
status: the state, with the title, pause, position and current item read from the running mpv.
play ID|ALIAS|URL|JSON, stop, toggle, next, previous: the radio's own mpv only, sound only.
video: the picture of what mpv plays, for the Radio panel: a video-only stream (yt-dlp, up to 720p) and where mpv is,
as JSON. mpv keeps the sound; the panel follows its position and pause (status).
search QUERY [all|playlist|video]: YouTube results, as JSON.
save JSON, remove ID|URL: the saved items.
"""
from common import read_json, write_atomic
from i18n import tr
import contextlib
import fcntl
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
from urllib.parse import quote_plus
import uuid

ANSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
HOME = Path.home()
SHIPPED = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'desktop/radio/stations.json'
# What mpv may play: streams and yt-dlp's URLs, and files on disk (given as an absolute path).
SCHEMES = ('http://', 'https://', 'ytdl://')
KINDS = ('radio', 'youtube', 'playlist', 'file')


def runtime_dir():
    base = Path(os.environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}')
    directory = base / 'desktop-shell'
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def state_path():
    return runtime_dir() / 'radio.json'


# One change of what plays at a time (the panel, a bind and a terminal can ask together): stop, start and the
# state written after it go as one, or two plays would both start an mpv and only the second be in radio.json.
# The panel ends an action it replaces with SIGTERM: that waits for the end of the change, and the newer action
# waits on the lock, so it finds the state of this one.
@contextlib.contextmanager
def exclusive():
    stopped = []
    previous = signal.signal(signal.SIGTERM, lambda number, frame: stopped.append(number))
    try:
        with (runtime_dir() / '.radio.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield
    finally:
        signal.signal(signal.SIGTERM, previous)
        if stopped:
            os.kill(os.getpid(), signal.SIGTERM)


def radio_socket_path():
    return runtime_dir() / 'radio-mpv.sock'


def config_path():
    base = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config')
    return base / 'desktop' / 'radio.json'


def station(entry):
    """A station as used here, or None when the entry does not describe one."""
    if not isinstance(entry, dict):
        return None
    url = str(entry.get('url') or '').strip()
    station_id = str(entry.get('id') or '').strip()
    if not station_id or not playable(url):
        return None
    aliases = entry.get('aliases') if isinstance(entry.get('aliases'), list) else []
    return {
        'id': station_id,
        'aliases': [str(alias) for alias in aliases if isinstance(alias, str)],
        'title': str(entry.get('title') or url).strip(),
        'subtitle': str(entry.get('subtitle') or '').strip(),
        'category': str(entry.get('category') or '').strip(),
        'kind': entry.get('kind') if entry.get('kind') in KINDS else kind_of(url),
        'url': url,
    }


def catalog(shipped=None, own=None):
    """The categories and stations: shipped first, then the user's, which replace one with the same id."""
    shipped = read_json(shipped or SHIPPED)
    own = read_json(own or config_path())
    stations, categories = {}, []
    for source in (shipped, own):
        for entry in source.get('stations', []) if isinstance(source.get('stations'), list) else []:
            item = station(entry)
            if item:
                stations[item['id']] = item
        for name in source.get('categories', []) if isinstance(source.get('categories'), list) else []:
            if isinstance(name, str) and name not in categories:
                categories.append(name)
    listed = list(stations.values())
    categories += [item['category'] for item in listed if item['category'] and item['category'] not in categories]
    return [name for name in categories if any(item['category'] == name for item in listed)], listed


def pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def runs_mpv_on(pid, sock):
    # The radio's own mpv, started with this socket: the pid in radio.json may belong to another program by now
    # (mpv ends by itself at the end of a video, and the state says so only at the next look).
    try:
        arguments = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    except OSError:
        return False
    return f'--input-ipc-server={sock}'.encode() in arguments


def playable(url):
    return isinstance(url, str) and (url.startswith(SCHEMES) or (url.startswith('/') and Path(url).is_file()))


def kind_of(url):
    if 'playlist?list=' in url:
        return 'playlist'
    if 'youtube.com/' in url or 'youtu.be/' in url:
        return 'youtube'
    return 'file' if url.startswith('/') else 'radio'


def load_saved(path=None):
    items = read_json(path or config_path()).get('saved', [])
    return [item for item in items if isinstance(item, dict) and playable(str(item.get('url') or ''))] if isinstance(items, list) else []


def save_saved(items, path=None):
    target = Path(path or config_path())
    # The rest of the file (the user's own stations) stays as it is.
    data = read_json(target)
    data['saved'] = items
    write_atomic(target, json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def add_saved_item(raw_item, path=None):
    item = json.loads(raw_item) if isinstance(raw_item, str) else dict(raw_item)
    if not isinstance(item, dict):
        raise ValueError(tr('radio.errors.missingUrl'))
    url = str(item.get('url') or '').strip()
    if not playable(url):
        raise ValueError(tr('radio.errors.missingUrl'))
    title = str(item.get('title') or url).strip()
    subtitle = str(item.get('subtitle') or '').strip()
    if not subtitle and (item.get('channel') or item.get('duration')):
        subtitle = ' · '.join(str(part) for part in (item.get('channel'), item.get('duration')) if part)
    kind = item.get('kind') if item.get('kind') in KINDS else kind_of(url)
    category = str(item.get('category') or 'saved').strip()
    item_id = str(item.get('id') or '').strip()
    if not item_id:
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:24] or 'saved'
        item_id = f'{slug}-{uuid.uuid4().hex[:6]}'
    items = load_saved(path)
    entry = {'id': item_id, 'title': title, 'subtitle': subtitle, 'category': category, 'kind': kind, 'url': url, 'saved': True}
    for index, existing in enumerate(items):
        if existing.get('url') == url or existing.get('id') == item_id:
            entry['id'] = existing.get('id') or item_id
            items[index] = entry
            break
    else:
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


def schemed(text):
    # youtube.com/watch?v=… typed without its scheme.
    if text.startswith(('youtube.com/', 'www.youtube.com/', 'm.youtube.com/', 'music.youtube.com/', 'youtu.be/')):
        return 'https://' + text
    return text


def same_url(first, second):
    first, second = str(first or '').rstrip('/'), str(second or '').rstrip('/')
    if first and first == second:
        return True
    first_id, second_id = youtube_id(first), youtube_id(second)
    return bool(first_id) and first_id == second_id


def remove_saved_item(identifier, path=None):
    target = schemed(str(identifier).strip())
    items = load_saved(path)
    kept = [item for item in items if str(item.get('id') or '') != target and not same_url(item.get('url'), target)]
    save_saved(kept, path)
    return len(kept) != len(items)


def default_state():
    return {
        'active': False, 'playing': False, 'paused': False, 'pid': 0, 'socket': '', 'stationId': '', 'title': '',
        'stationTitle': '', 'subtitle': '', 'url': '', 'kind': '', 'category': '',
    }


def load_state(path=None):
    target = Path(path) if path else state_path()
    state = default_state()
    raw = read_json(target)
    state.update({key: raw[key] for key in state if key in raw})
    if state['active'] and not pid_alive(state['pid']):
        if state['socket']:
            Path(state['socket']).unlink(missing_ok=True)
        state = default_state()
        try:
            write_atomic(target, json.dumps(state) + '\n')
        except OSError:
            pass
    return state


def write_state(state, path=None):
    merged = default_state()
    merged.update(state)
    write_atomic(Path(path) if path else state_path(), json.dumps(merged, ensure_ascii=False) + '\n')
    return merged


def match_station(identifier_or_url, stations=None, saved_items=None):
    if not identifier_or_url:
        return None
    needle = schemed(str(identifier_or_url).strip())
    lower = needle.lower()
    stations = catalog()[1] if stations is None else stations
    saved = load_saved() if saved_items is None else saved_items
    for item in stations + saved:
        if str(item.get('id', '')).lower() == lower or same_url(item.get('url'), needle):
            return dict(item)
        if any(str(alias).lower() == lower for alias in item.get('aliases', [])):
            return dict(item)
    return None


def mpv_ipc(command, socket_path=None, timeout=1.5):
    """Send one command to the radio's mpv and return its reply, or None. Only that mpv: never another one."""
    target = Path(socket_path) if socket_path else radio_socket_path()
    if not target.exists():
        return None
    payload = (json.dumps({'command': command, 'request_id': 1}) + '\n').encode('utf-8')
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout)
            client.connect(str(target))
            client.sendall(payload)
            buffer = b''
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    return None
                buffer += chunk
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    try:
                        reply = json.loads(line.decode('utf-8', errors='replace'))
                    except ValueError:
                        continue
                    # Events arrive on the same socket; the reply carries the request's id.
                    if isinstance(reply, dict) and reply.get('request_id') == 1:
                        return reply
    except OSError:
        return None


def mpv_property(name):
    reply = mpv_ipc(['get_property', name], timeout=0.5)
    return reply.get('data') if isinstance(reply, dict) and reply.get('error') == 'success' else None


def live_state():
    """The state file, with what the running mpv says now: its title, pause, position and item."""
    state = load_state()
    if not state['active']:
        return state
    title = mpv_property('media-title')
    if isinstance(title, str) and title.strip() and not title.startswith(SCHEMES):
        state['title'] = html.unescape(title).strip()
    paused = mpv_property('pause')
    if isinstance(paused, bool):
        state['paused'], state['playing'] = paused, not paused
    position = mpv_property('time-pos')
    state['position'] = position if isinstance(position, (int, float)) else 0
    item = mpv_property('path')
    state['item'] = item if isinstance(item, str) else state['url']
    return state


def current_url(state):
    """What mpv plays now: the item of a playlist, as a URL yt-dlp takes, or the file."""
    path = mpv_property('path')
    path = path if isinstance(path, str) and path else state.get('url', '')
    if path.startswith('ytdl://'):
        path = path[len('ytdl://'):]
        path = f'https://www.youtube.com/watch?v={path}' if youtube_id(path) == path else path
    return path


def video_stream(url):
    """The picture alone, which Qt Multimedia plays muted next to mpv's sound: YouTube serves sound and picture as
    separate streams, and this is the best H.264 one up to 720p. A file is played as it is."""
    if url.startswith('/'):
        return 'file://' + url
    if not shutil.which('yt-dlp'):
        raise ValueError(tr('radio.errors.noVideo'))
    formats = ('bestvideo[height<=720][vcodec^=avc1][protocol=https]/bestvideo[height<=720][vcodec^=avc1]/'
               'bestvideo[height<=720]/best[vcodec!=none]')
    command = ['yt-dlp', '--no-playlist', '--no-warnings', '-f', formats, '-g', '--', url]
    try:
        process = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        raise ValueError(tr('radio.errors.noVideo')) from None
    lines = [line for line in process.stdout.splitlines() if line.startswith(SCHEMES)]
    if process.returncode != 0 or len(lines) != 1:
        raise ValueError(tr('radio.errors.noVideo'))
    return lines[0]


def video():
    """The picture of what mpv plays now, and where mpv is: the panel starts it there and follows mpv from then on."""
    state = live_state()
    if not state['active'] or state.get('kind') not in ('youtube', 'playlist', 'file'):
        raise ValueError(tr('radio.errors.noVideo'))
    item = current_url(state)
    stream = video_stream(item)
    position = mpv_property('time-pos')
    return {'stream': stream, 'item': state['item'], 'position': position if isinstance(position, (int, float)) else 0}


def stop_playback():
    state = load_state()
    sock = state.get('socket') or str(radio_socket_path())
    mpv_ipc(['quit'], socket_path=sock, timeout=0.5)
    pid = state.get('pid', 0)
    if pid_alive(pid) and runs_mpv_on(pid, sock):
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
        item = dict(target)
    else:
        text = str(target).strip()
        item = None
        if text.startswith('{') and text.endswith('}'):
            try:
                parsed = json.loads(text)
            except ValueError:
                parsed = None
            item = parsed if isinstance(parsed, dict) else None
        if item is None:
            text = schemed(text)
            item = match_station(text)
        if item is None:
            path = Path(text).expanduser()
            url = str(path.resolve()) if not text.startswith(SCHEMES) and path.is_file() else text
            if not playable(url):
                raise ValueError(tr('radio.errors.unknown', [text]))
            item = {'id': '', 'title': url, 'subtitle': '', 'category': 'custom', 'kind': kind_of(url), 'url': url}
    url = str(item.get('url') or '').strip()
    # Whatever the item came from (a search result, the panel), mpv gets a URL or a file, never an option.
    if not playable(url):
        raise ValueError(tr('radio.errors.unknown', [url]))
    item['url'] = url
    return item


def play_target(target):
    item = resolve_play_item(target)
    url = item['url']
    title = item.get('title') or url
    kind = item.get('kind') if item.get('kind') in KINDS else kind_of(url)
    stop_playback()
    sock = radio_socket_path()
    sock.unlink(missing_ok=True)
    # Sound only: the picture, when asked for, plays in the Radio panel, muted and in step with this mpv (video).
    command = ['mpv', f'--input-ipc-server={sock}', f'--title={title}', '--no-video']
    if kind == 'playlist':
        command.append('--ytdl-raw-options=yes-playlist=')
    command += ['--', url]
    try:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
    except OSError:
        raise ValueError(tr('radio.errors.noMpv')) from None
    return write_state({
        'active': True, 'playing': True, 'paused': False, 'pid': child.pid, 'socket': str(sock),
        'stationId': item.get('id') or '', 'title': title, 'stationTitle': title, 'subtitle': item.get('subtitle') or '',
        'url': url, 'kind': kind, 'category': item.get('category') or '',
    })


def youtube_url(url, item_id, playlist):
    """A YouTube URL from a search result: absolute, https, www, or built from the id."""
    url = url.strip()
    if playlist and ('list=null' in url or 'playlist?list=' not in url) and item_id:
        return f'https://www.youtube.com/playlist?list={item_id}'
    if not playlist and ('watch?v=null' in url or not url) and item_id:
        return f'https://www.youtube.com/watch?v={item_id}'
    for prefix in ('https://youtube.com/', 'http://youtube.com/', 'http://www.youtube.com/'):
        if url.startswith(prefix):
            return 'https://www.youtube.com/' + url[len(prefix):]
    if url.startswith(('/', 'watch?', 'playlist?')):
        return 'https://www.youtube.com/' + url.lstrip('/')
    return url


def clean(text):
    return re.sub(r'\s+', ' ', html.unescape(ANSI_RE.sub('', str(text or '')))).strip()


def parse_ytfzf_output(raw_text, limit=20):
    if not raw_text or not str(raw_text).strip():
        return []
    text = ANSI_RE.sub('', str(raw_text))
    decoder = json.JSONDecoder()
    position, raw_items = 0, []
    while position < len(text):
        match = re.search(r'[\[\{]', text[position:])
        if not match:
            break
        start = position + match.start()
        try:
            value, end = decoder.raw_decode(text, start)
        except ValueError:
            position = start + 1
            continue
        if isinstance(value, list):
            raw_items.extend(entry for entry in value if isinstance(entry, dict))
        elif isinstance(value, dict):
            raw_items.append(value)
        position = end
    results, seen = [], set()
    for entry in raw_items:
        title, url = clean(entry.get('title')), clean(entry.get('url'))
        item_id, action, views = clean(entry.get('ID')), str(entry.get('action') or ''), str(entry.get('views') or '')
        channel, duration = clean(entry.get('channel')), clean(entry.get('duration'))
        if title == '[BACK]' or url == 'back' or title.startswith('[channel]') or 'invidious-channel' in action:
            continue
        playlist = title.startswith('[playlist]') or views == 'playlist' or 'playlist' in action or 'playlist?list=' in url
        if title.startswith('[playlist]'):
            title = title[len('[playlist]'):].strip()
        url = youtube_url(url, item_id, playlist)
        if not title or not url.startswith(SCHEMES) or url in seen:
            continue
        seen.add(url)
        results.append({
            'id': f'yt-{item_id or uuid.uuid4().hex[:8]}', 'title': title,
            'subtitle': ' · '.join(part for part in (channel, duration) if part and part != 'null'),
            'channel': channel, 'duration': duration, 'category': 'youtube', 'kind': 'playlist' if playlist else 'youtube',
            'url': url,
        })
        if len(results) >= limit:
            break
    return results


def search_ytdlp_fallback(query, search_type='all', limit=15):
    if not shutil.which('yt-dlp'):
        return []
    if search_type == 'playlist':
        target = f'https://www.youtube.com/results?search_query={quote_plus(query)}&sp=EgIQAw%253D%253D'
    else:
        target = f'ytsearch{limit}:{query}'
    command = ['yt-dlp', '--flat-playlist', '--dump-json', '--no-warnings', '--playlist-end', str(limit), '--', target]
    try:
        process = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError):
        return []
    results, seen = [], set()
    for line in process.stdout.splitlines():
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        entry_id, title = clean(data.get('id')), clean(data.get('title'))
        url = clean(data.get('url') or data.get('webpage_url'))
        kind = str(data.get('ie_key') or data.get('_type') or '').lower()
        playlist = search_type == 'playlist' or 'playlist' in kind or entry_id.startswith(('PL', 'OL', 'UU', 'RD'))
        if playlist and entry_id and 'playlist?list=' not in url:
            url = f'https://www.youtube.com/playlist?list={entry_id}'
        elif not url.startswith('http') and entry_id:
            url = f'https://www.youtube.com/watch?v={entry_id}'
        elif url.startswith('http://'):
            url = 'https://' + url[len('http://'):]
        if not title or not url.startswith(SCHEMES) or url in seen:
            continue
        seen.add(url)
        channel = clean(data.get('channel') or data.get('uploader'))
        seconds = data.get('duration')
        duration = f'{int(seconds) // 60}:{int(seconds) % 60:02d}' if isinstance(seconds, (int, float)) and seconds > 0 else ''
        results.append({
            'id': f'yt-{entry_id or uuid.uuid4().hex[:8]}', 'title': title,
            'subtitle': ' · '.join(part for part in (channel, duration) if part), 'channel': channel, 'duration': duration,
            'category': 'youtube', 'kind': 'playlist' if playlist else 'youtube', 'url': url,
        })
        if len(results) >= limit:
            break
    return results


def search_youtube(query, search_type='all', limit=20):
    query = str(query or '').strip()
    if not query:
        return []
    search_type = search_type if search_type in ('all', 'playlist', 'video') else 'all'
    if shutil.which('ytfzf'):
        command = ['ytfzf', '-c', 'Y', '-A', '-I', 'VJ', '--info-exit', '--disable-actions', '--disable-submenus',
                   f'--type={search_type}', query]
        try:
            process = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=12, check=False)
            parsed = parse_ytfzf_output(process.stdout, limit=limit)
            if parsed:
                return parsed
        except (OSError, subprocess.SubprocessError):
            pass
    return search_ytdlp_fallback(query, search_type=search_type, limit=limit)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0] if args else 'list'
    try:
        if command == 'list':
            categories, stations = catalog()
            print(json.dumps({'categories': categories, 'stations': stations, 'saved': load_saved(), 'state': live_state()},
                             ensure_ascii=False))
            return 0
        if command == 'status':
            print(json.dumps(live_state(), ensure_ascii=False))
            return 0
        if command == 'play' and len(args) >= 2:
            with exclusive():
                result = play_target(args[1])
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if command == 'stop':
            with exclusive():
                result = stop_playback()
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if command in ('toggle', 'next', 'previous'):
            mpv_ipc({'toggle': ['cycle', 'pause'], 'next': ['playlist-next', 'weak'], 'previous': ['playlist-prev', 'weak']}[command])
            print(json.dumps(live_state(), ensure_ascii=False))
            return 0
        if command == 'video':
            print(json.dumps(video(), ensure_ascii=False))
            return 0
        if command == 'search':
            results = search_youtube(args[1] if len(args) > 1 else '', args[2] if len(args) > 2 else 'all')
            print(json.dumps({'results': results}, ensure_ascii=False))
            return 0
        if command == 'save' and len(args) >= 2:
            with exclusive():
                entry = add_saved_item(args[1])
            print(json.dumps({'saved': load_saved(), 'entry': entry}, ensure_ascii=False))
            return 0
        if command == 'remove' and len(args) >= 2:
            with exclusive():
                remove_saved_item(args[1])
            print(json.dumps({'saved': load_saved()}, ensure_ascii=False))
            return 0
        if command not in ('play', 'save', 'remove'):
            matched = match_station(command)
            if matched:
                with exclusive():
                    result = play_target(matched)
                print(json.dumps(result, ensure_ascii=False))
                return 0
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    print(tr('radio.errors.usage', [command]), file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())

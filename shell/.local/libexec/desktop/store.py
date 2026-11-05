#!/usr/bin/env python3
"""Cursor and icon themes from the KDE Store (store.kde.org, through its public OCS API), as Plasma's "Get New"
dialogs find them.

search KIND [QUERY] [PAGE]: prints {"items": [{id, name, author, summary, downloads, score, preview, files}],
    "total", "page"}; KIND is cursors or icons, most downloaded first.
install KIND ID FILE: downloads that file of the entry (its md5 checked when the store gives one), unpacks it
    with tarfile's data filter or a checked zip, and moves the theme folders it holds (a cursors/ folder for
    cursors, an index.theme with [Icon Theme] directories for icons) into ~/.local/share/icons; prints
    {"installed": [folders]}. Folders installed this way are listed in ~/.local/share/desktop/store.json.
remove FOLDER: deletes a folder the store installed, nothing else.
installed: prints that list.

The content is other people's: archives are size-limited, nothing is run, and only theme folders are kept.
"""
from common import theme_name, write_atomic
from i18n import tr
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile

API = 'https://api.kde-look.org/ocs/v1/content'
CATEGORIES = {'cursors': 107, 'icons': 132}
# A generic client name; nothing personal goes with the requests.
AGENT = 'desktop-theming/1.0'
HOME = Path.home()
ICONS = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'icons'
LEDGER = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'desktop/store.json'
# Themes from packages or put there by hand: the user folder is searched first, so a pack with one of their
# names (Adwaita, Papirus) would replace it for every app. Nor the default alias or the fallback themes.
SYSTEM_ICONS = [HOME / '.icons'] + [Path(d) / 'icons' for d in (os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':') if d]
RESERVED = {'default', 'hicolor', 'locolor'}
MAX_DOWNLOAD = 300 * 2**20
MAX_UNPACKED = 2 * 2**30
MAX_MEMBERS = 300_000


def fetch_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode('utf-8'))


def files_of(item):
    files = []
    index = 1
    while item.get(f'downloadlink{index}'):
        files.append({'index': index, 'name': item.get(f'downloadname{index}') or f'#{index}',
                      'size': int(item.get(f'downloadsize{index}') or 0), 'md5': item.get(f'downloadmd5sum{index}') or ''})
        index += 1
    return files


def search(kind, query='', page=0):
    params = {'categories': CATEGORIES[kind], 'sortmode': 'down', 'pagesize': 24, 'page': page, 'format': 'json'}
    if query:
        params['search'] = query
    data = fetch_json(f'{API}/data?' + urllib.parse.urlencode(params))
    items = [{'id': int(item['id']), 'name': item.get('name', ''), 'author': item.get('personid', ''),
              'summary': (item.get('summary') or '')[:200], 'downloads': int(item.get('downloads') or 0),
              'score': int(item.get('score') or 0), 'preview': item.get('smallpreviewpic1') or item.get('previewpic1') or '',
              'files': files_of(item)} for item in data.get('data') or []]
    return {'items': items, 'total': int(data.get('totalitems') or 0), 'page': page}


def download(url, destination, md5):
    request = urllib.request.Request(url, headers={'User-Agent': AGENT})
    digest, size = hashlib.md5(), 0
    with urllib.request.urlopen(request, timeout=60) as response, destination.open('wb') as file:
        for block in iter(lambda: response.read(1024 * 1024), b''):
            size += len(block)
            if size > MAX_DOWNLOAD:
                raise ValueError(tr('store.errors.tooLarge'))
            digest.update(block)
            file.write(block)
    if md5 and digest.hexdigest() != md5:
        raise ValueError(tr('store.errors.checksum'))


def safe_member(member, path):
    # tarfile's data filter, member by member: what it refuses (an absolute link, a path out of the folder, a
    # device) is left out instead of failing the whole theme, as icon themes often link to absolute paths.
    try:
        return tarfile.data_filter(member, path)
    except tarfile.FilterError:
        return None


def unpack(archive, target):
    # tar through safe_member; zip by hand.
    if tarfile.is_tarfile(archive):
        with tarfile.open(archive) as source:
            members = source.getmembers()
            if len(members) > MAX_MEMBERS or sum(member.size for member in members) > MAX_UNPACKED:
                raise ValueError(tr('store.errors.tooLarge'))
            source.extractall(target, filter=safe_member)
        return
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as source:
            infos = source.infolist()
            if len(infos) > MAX_MEMBERS or sum(info.file_size for info in infos) > MAX_UNPACKED:
                raise ValueError(tr('store.errors.tooLarge'))
            root = target.resolve()
            for info in infos:
                path = (target / info.filename).resolve()
                if not path.is_relative_to(root) or (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError(tr('store.errors.unsafe'))
            source.extractall(target)
        return
    raise ValueError(tr('store.errors.format'))


def is_theme(folder, kind):
    if kind == 'cursors':
        return (folder / 'cursors').is_dir()
    index = folder / 'index.theme'
    if not index.is_file():
        return False
    text = index.read_text(encoding='utf-8', errors='replace')
    return '[Icon Theme]' in text and 'Directories=' in text


def themes_in(root, kind):
    found = []
    for folder in sorted(path for path in root.rglob('*') if path.is_dir() and not path.is_symlink()):
        if is_theme(folder, kind) and not any(folder.is_relative_to(other) for other in found):
            found.append(folder)
    return found


def ledger():
    try:
        value = json.loads(LEDGER.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def allowed(name):
    return theme_name(name) and name not in RESERVED and not any((root / name).exists() for root in SYSTEM_ICONS)


def install(kind, item_id, index):
    item = (fetch_json(f'{API}/data/{int(item_id)}?format=json').get('data') or [None])[0]
    if not item or not item.get(f'downloadlink{index}'):
        raise ValueError(tr('store.errors.missing'))
    installed, refused = [], False
    # Unpacked next to the icon folders, not in /tmp (memory here): installing is then a rename, not a copy.
    # The leading dot keeps it out of the theme lists.
    ICONS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.desktop-store-', dir=ICONS) as folder:
        work = Path(folder)
        archive = work / 'download'
        download(item[f'downloadlink{index}'], archive, item.get(f'downloadmd5sum{index}') or '')
        unpacked = work / 'unpacked'
        unpacked.mkdir()
        unpack(archive, unpacked)
        themes = themes_in(unpacked, kind)
        if not themes:
            raise ValueError(tr('store.errors.noTheme'))
        record = ledger()
        ICONS.mkdir(parents=True, exist_ok=True)
        for theme in themes:
            name = theme.name
            # Names go into config files (theme.py), so only plain ones.
            if not allowed(name):
                refused = True
                continue
            target = ICONS / name
            # Only a folder the store put there may be replaced: never a theme from a package or by hand.
            if target.exists() and name not in record:
                continue
            shutil.rmtree(target, ignore_errors=True)
            shutil.move(str(theme), str(target))
            record[name] = {'id': int(item_id), 'name': item.get('name', ''), 'kind': kind, 'file': item.get(f'downloadname{index}', '')}
            installed.append(name)
        write_atomic(LEDGER, json.dumps(record, ensure_ascii=False, indent=1))
    if not installed:
        raise ValueError(tr('store.errors.name' if refused else 'store.errors.exists'))
    return {'installed': installed}


# Every folder of an entry in one call; all are checked before any is removed.
def remove(*names):
    record = ledger()
    for name in names:
        if name not in record or '/' in name:
            raise ValueError(tr('store.errors.notFromStore', [name]))
    for name in names:
        shutil.rmtree(ICONS / name, ignore_errors=True)
        del record[name]
    write_atomic(LEDGER, json.dumps(record, ensure_ascii=False, indent=1))
    return {'removed': list(names)}


def main():
    arguments = sys.argv[1:]
    try:
        if arguments[:1] == ['search'] and len(arguments) >= 2 and arguments[1] in CATEGORIES:
            result = search(arguments[1], arguments[2] if len(arguments) > 2 else '', int(arguments[3]) if len(arguments) > 3 else 0)
        elif arguments[:1] == ['install'] and len(arguments) == 4 and arguments[1] in CATEGORIES:
            result = install(arguments[1], int(arguments[2]), int(arguments[3]))
        elif arguments[:1] == ['remove'] and len(arguments) >= 2:
            result = remove(*arguments[1:])
        elif arguments == ['installed']:
            result = {'installed': ledger()}
        else:
            print(tr('store.errors.usage'), file=sys.stderr)
            return 2
    except ValueError as error:
        result = {'error': str(error)}
    except (tarfile.TarError, zipfile.BadZipFile, EOFError):
        result = {'error': tr('store.errors.format')}
    except (OSError, KeyError):
        result = {'error': tr('store.errors.unavailable')}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())

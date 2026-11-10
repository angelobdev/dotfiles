#!/usr/bin/env python3
"""The icon and cursor themes theme.py offers: icon packs found through their index.theme and Inherits chain, with
sample icons, and cursor packs (the desktop's own set, fetched and checked by sha256) with previews drawn from
XCursor and hyprcursor files. Nothing here knows about colour themes; theme.py imports from it."""
from common import download as download_file, replacing, theme_name
from i18n import tr
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import struct
import sys
import tarfile
import tempfile
import zipfile
import zlib

HOME = Path.home()


ICON_DIRS = [Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'icons', HOME / '.icons'] + [
    Path(d) / 'icons' for d in (os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':') if d]


# Folder, terminal, browser, settings and document: enough to tell icon packs apart at a glance.
ICON_SAMPLES = ('folder', 'utilities-terminal', 'web-browser', 'preferences-system', 'text-x-generic')


USER_ICONS = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'icons'


def read_index(path):
    sections, section = {}, None
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            section = sections.setdefault(line[1:-1], {})
        elif '=' in line and section is not None:
            key, _, value = line.partition('=')
            section[key.strip()] = value.strip()
    return sections


def icon_theme_dirs(name, roots):
    return [root / name for root in roots if (root / name / 'index.theme').is_file()]


# A Size that is not a plain number ("48px" in a downloaded pack) sorts last instead of failing the listing.
def index_size(section):
    size = section.get('Size', '').strip()
    return int(size) if size.isdigit() else 0


# Sample files resolved through the theme and its Inherits chain, so a preview shows that pack's icons.
def icon_samples(name, roots, names=ICON_SAMPLES):
    found, chain, seen = {}, [name], set()
    while chain:
        theme = chain.pop(0)
        # Every chain ends in hicolor, the fallback all icon themes share.
        if not chain and theme != 'hicolor' and 'hicolor' not in seen:
            chain.append('hicolor')
        if theme in seen:
            continue
        seen.add(theme)
        for base in icon_theme_dirs(theme, roots):
            index = read_index(base / 'index.theme')
            info = index.get('Icon Theme', {})
            directories = [d.strip() for d in info.get('Directories', '').split(',') if d.strip()]
            directories += [d.strip() for d in info.get('ScaledDirectories', '').split(',') if d.strip()]
            # Prefer scalable and large icons for a crisp preview.
            directories.sort(key=lambda d: (index.get(d, {}).get('Type') != 'Scalable', -index_size(index.get(d, {}))))
            for icon in names:
                if icon in found:
                    continue
                for directory in directories:
                    for extension in ('.svg', '.png'):
                        candidate = base / directory / (icon + extension)
                        if candidate.is_file():
                            found[icon] = str(candidate)
                            break
                    if icon in found:
                        break
            chain += [parent.strip() for parent in info.get('Inherits', '').split(',') if parent.strip()]
        if len(found) == len(names):
            break
    return [found.get(icon, '') for icon in names]


def icon_themes(roots=None):
    roots = roots or ICON_DIRS
    listed = {}
    for root in roots:
        if not root.is_dir():
            continue
        for base in sorted(root.iterdir()):
            index_file = base / 'index.theme'
            if base.name in listed or base.name in ('hicolor', 'default', 'locolor') or not theme_name(base.name) or not index_file.is_file():
                continue
            info = read_index(index_file).get('Icon Theme', {})
            # Hidden is not honoured: Fedora's Adwaita sets it, and the sample check below already drops
            # cursor-only and internal themes.
            if 'legacy' in base.name.lower():
                continue
            # One broken pack hides only itself.
            try:
                samples = icon_samples(base.name, roots)
            except (OSError, ValueError):
                continue
            # Cursor-only themes resolve nothing beyond hicolor. Adwaita draws folders and files but leaves
            # application icons to hicolor, so two samples of its own are enough.
            if sum(1 for sample in samples if sample and '/hicolor/' not in sample) < 2:
                continue
            listed[base.name] = {'id': base.name, 'name': info.get('Name', base.name), 'samples': samples}
    return sorted(listed.values(), key=lambda t: t['name'].lower())


# Cursor sizes offered, in logical pixels; Adwaita draws 24, 32, 48, 64 and 96, others scale the nearest.
CURSOR_SIZES = (24, 32, 40, 48)


# Cursor themes Fedora does not package, part of the desktop's set beside Adwaita and Breeze: pinned releases,
# checked by sha256, unpacked into ~/.local/share/icons. `apply` (every login) fetches the missing ones in the
# background; choosing one before that fetches it at once. member is the folder taken from the archive.
CURSOR_PACKS = {
    'macOS': {'name': 'macOS', 'file': 'macOS.tar.xz', 'member': 'macOS',
              'url': 'https://github.com/ful1e5/apple_cursor/releases/download/v2.0.1/macOS.tar.xz',
              'sha256': '9c6e5e13b068ce51a9e90a9abd6ce232ec7d25d4ceb05aa8ac76efbb99c76762'},
    'macOS-White': {'name': 'macOS White', 'file': 'macOS.tar.xz', 'member': 'macOS-White',
                    'url': 'https://github.com/ful1e5/apple_cursor/releases/download/v2.0.1/macOS.tar.xz',
                    'sha256': '9c6e5e13b068ce51a9e90a9abd6ce232ec7d25d4ceb05aa8ac76efbb99c76762'},
    'Bibata-Modern-Classic': {'name': 'Bibata Modern Classic', 'file': 'Bibata-Modern-Classic.tar.xz', 'member': 'Bibata-Modern-Classic',
                              'url': 'https://github.com/ful1e5/Bibata_Cursor/releases/download/v2.0.7/Bibata-Modern-Classic.tar.xz',
                              'sha256': '7d3495864e5bbef02f5e77de760b2905903b63c71495a78ef6306d19a3b556d8'},
    'Bibata-Modern-Ice': {'name': 'Bibata Modern Ice', 'file': 'Bibata-Modern-Ice.tar.xz', 'member': 'Bibata-Modern-Ice',
                          'url': 'https://github.com/ful1e5/Bibata_Cursor/releases/download/v2.0.7/Bibata-Modern-Ice.tar.xz',
                          'sha256': 'a68cae60c4dc706350e194ebc91c5fe48bc7bc9d59e119555834a2a7ee5078ef'},
}


CURSOR_DOWNLOADS = Path(os.environ.get('XDG_CACHE_HOME') or HOME / '.cache') / 'desktop/cursors'


def fetch_cursor(name):
    # One fetch at a time: the one apply starts at login and one from the panel would share the archive.
    CURSOR_DOWNLOADS.mkdir(parents=True, exist_ok=True)
    with open(CURSOR_DOWNLOADS / '.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Installed by the other one while this one waited.
        if (USER_ICONS / name / 'cursors').is_dir():
            return
        unpack_cursor(name)


def unpack_cursor(name):
    # The archive is kept, so the other variant of a pack (macOS, macOS White) needs no download. Only the pack's
    # own folder is unpacked, with tarfile's data filter: no links out of it, no devices, no absolute paths.
    pack = CURSOR_PACKS[name]
    archive = CURSOR_DOWNLOADS / pack['file']
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != pack['sha256']:
        download(pack, archive)
    # A folder of its own, hidden from the theme lists (a name starting with a dot is no theme name).
    USER_ICONS.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(dir=USER_ICONS, prefix=f'.{name}.'))
    try:
        with tarfile.open(archive) as source:
            prefix = pack['member'].strip('/')
            members = [member for member in source.getmembers()
                       if member.name.lstrip('./') == prefix or member.name.lstrip('./').startswith(prefix + '/')]
            if not members:
                raise ValueError(tr('theme.errors.checksum', [pack['file']]))
            source.extractall(staging, members=members, filter='data')
        unpacked = staging / prefix
        target = USER_ICONS / name
        shutil.rmtree(target, ignore_errors=True)
        unpacked.rename(target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def fetch_missing_cursors():
    # The desktop's set, in the background after apply; one that fails is tried again at the next login.
    installed = {theme['id'] for theme in cursor_themes()}
    for name in CURSOR_PACKS:
        if name not in installed:
            try:
                fetch_cursor(name)
            except (OSError, ValueError, tarfile.TarError) as error:
                print(f'{name}: {error}', file=sys.stderr)


def cursor_themes(roots=None):
    # XCursor themes (a cursors folder) and hyprcursor ones (a manifest), by folder name; the "default" alias
    # only points at another theme.
    listed = {}
    for root in roots or ICON_DIRS:
        if not root.is_dir():
            continue
        for base in sorted(root.iterdir()):
            if base.name in listed or base.name == 'default' or not theme_name(base.name) or not ((base / 'cursors').is_dir() or (base / 'manifest.hl').is_file()):
                continue
            info = read_index(base / 'index.theme').get('Icon Theme', {}) if (base / 'index.theme').is_file() else {}
            listed[base.name] = {'id': base.name, 'name': info.get('Name', base.name)}
    return sorted(listed.values(), key=lambda t: t['name'].lower())


# The shapes a cursor preview shows: arrow, hand, text, busy and resize, each by its CSS name first and the
# X11 names older themes use.
CURSOR_SAMPLES = (('default', 'left_ptr', 'arrow'), ('pointer', 'hand2', 'hand1', 'pointing_hand'), ('text', 'xterm', 'ibeam'),
                  ('wait', 'watch'), ('ew-resize', 'sb_h_double_arrow', 'h_double_arrow', 'size_hor'))


CURSOR_PREVIEWS = Path(os.environ.get('XDG_CACHE_HOME') or HOME / '.cache') / 'desktop-theme/cursors'


# The largest image a preview takes: 48 logical pixels on a 2x screen.
CURSOR_PREVIEW_SIZE = 96


XCURSOR_IMAGE = 0xfffd0002


def png_bytes(width, height, rgba):
    # Enough PNG for a preview: 8-bit RGBA, no filtering.
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    stride = width * 4
    rows = b''.join(b'\0' + rgba[y * stride:(y + 1) * stride] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


def xcursor_png(data, largest=CURSOR_PREVIEW_SIZE):
    # The first frame of the largest nominal size up to `largest` (else the smallest), as PNG. Pixels are
    # premultiplied ARGB, little endian, which PNG wants straight.
    if data[:4] != b'Xcur' or len(data) < 16:
        raise ValueError('not an XCursor file')
    header, _version, count = struct.unpack_from('<III', data, 4)
    entries = []
    for index in range(count):
        offset = header + index * 12
        if offset + 12 > len(data):
            break
        kind, size, position = struct.unpack_from('<III', data, offset)
        if kind == XCURSOR_IMAGE:
            entries.append((size, position))
    if not entries:
        raise ValueError('no image in the XCursor file')
    fitting = [entry for entry in entries if entry[0] <= largest]
    size, position = max(fitting) if fitting else min(entries)
    if position + 36 > len(data):
        raise ValueError('truncated XCursor file')
    width, height = struct.unpack_from('<II', data, position + 16)
    if not (0 < width <= 1024 and 0 < height <= 1024) or position + 36 + width * height * 4 > len(data):
        raise ValueError('bad XCursor image')
    pixels = memoryview(data)[position + 36:position + 36 + width * height * 4]
    rgba = bytearray(width * height * 4)
    for index in range(width * height):
        b, g, r, a = pixels[index * 4:index * 4 + 4]
        if a:
            rgba[index * 4:index * 4 + 4] = bytes((min(255, r * 255 // a), min(255, g * 255 // a), min(255, b * 255 // a), a))
    return png_bytes(width, height, bytes(rgba))


def hyprcursor_image(path, largest=CURSOR_PREVIEW_SIZE):
    # A .hlc shape is a zip with meta.hl ("define_size = SIZE, FILE[, DELAY]", 0 for an SVG) and its images:
    # the SVG when there is one, else the largest PNG up to `largest`.
    with zipfile.ZipFile(path) as archive:
        sizes = []
        for line in archive.read('meta.hl').decode('utf-8', 'replace').splitlines():
            key, _, value = line.partition('=')
            if key.strip() == 'define_size':
                parts = [part.strip() for part in value.split(',')]
                if len(parts) >= 2 and parts[0].isdigit():
                    sizes.append((int(parts[0]), parts[1]))
        if not sizes:
            raise ValueError('no image in the hyprcursor shape')
        vector = [entry for entry in sizes if entry[0] == 0 or entry[1].lower().endswith('.svg')]
        fitting = [entry for entry in sizes if 0 < entry[0] <= largest]
        _size, name = vector[0] if vector else max(fitting) if fitting else min(sizes)
        return archive.read(name), Path(name).suffix.lower() or '.png'


def cursor_sample(base, names):
    # The preview of one shape, cached under the cursor file's path, size and time: '' when the theme lacks it.
    base = Path(base)
    candidates = [(base / 'cursors' / name, 'xcursor') for name in names]
    if (base / 'manifest.hl').is_file():
        folder = 'hyprcursors'
        for line in (base / 'manifest.hl').read_text(encoding='utf-8', errors='replace').splitlines():
            key, _, value = line.partition('=')
            if key.strip() == 'cursors_directory' and value.strip():
                folder = value.strip()
        candidates += [(base / folder / (name + '.hlc'), 'hyprcursor') for name in names]
    for path, kind in candidates:
        if not path.is_file():
            continue
        info = path.stat()
        key = hashlib.sha1(f'{path.resolve()}\0{info.st_mtime_ns}\0{info.st_size}'.encode()).hexdigest()
        cached = [CURSOR_PREVIEWS / (key + suffix) for suffix in ('.png', '.svg')]
        for target in cached:
            if target.is_file():
                return str(target)
        try:
            if kind == 'xcursor':
                image, suffix = xcursor_png(path.read_bytes()), '.png'
            else:
                image, suffix = hyprcursor_image(path)
        except (OSError, ValueError, KeyError, struct.error, zipfile.BadZipFile):
            continue
        target = CURSOR_PREVIEWS / (key + ('.svg' if suffix == '.svg' else '.png'))
        with replacing(target, suffix=target.suffix) as temporary:
            temporary.write_bytes(image)
        return str(target)
    return ''


def cursor_theme_dir(name, roots=None):
    # The folder cursor_themes() lists for this name: the first root wins, as there.
    for root in roots or ICON_DIRS:
        base = root / name
        if (base / 'cursors').is_dir() or (base / 'manifest.hl').is_file():
            return base
    return None


def cursor_samples(base):
    # One broken file hides only its own shape.
    return [cursor_sample(base, names) for names in CURSOR_SAMPLES]


def download(entry, destination):
    download_file(entry['url'], destination, entry['sha256'], mismatch=tr('theme.errors.checksum', [entry['file']]))

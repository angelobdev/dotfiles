#!/usr/bin/env python3
"""Microsoft's fonts for this user, from their own Windows ISO, install.wim / install.esd or Fonts folder."""
from i18n import tr
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

FONTS = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share') / 'fonts/microsoft'
# Not /tmp, which is memory on Fedora: the image of a Windows ISO is 5 GiB or more.
CACHE = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'desktop'
SUFFIXES = ('.ttf', '.ttc', '.otf')
# Segoe UI Emoji: fontconfig may pick it over Noto Color Emoji, so it is installed only when asked for.
EMOJI = ('seguiemj.ttf',)
# The Windows image inside an ISO: a WIM from Microsoft's download page, an ESD from the Media Creation Tool.
IMAGES = ('sources/install.wim', 'sources/install.esd')
# Where 7z shows the fonts of an image: under the number of each edition, or at the top when it holds only one.
IMAGE_ROOTS = ('1/', '')
GIB = 1024 ** 3


def is_font(path, emoji=True):
    name = path.name.lower()
    return path.is_file() and name.endswith(SUFFIXES) and (emoji or name not in EMOJI)


def fonts_in(folder, emoji=True):
    return sorted(path for path in folder.iterdir() if is_font(path, emoji)) if folder.is_dir() else []


def child(folder, *names):
    """A path below folder whatever its case: NTFS and the ISO do not agree on Windows/Fonts and sources."""
    for name in names:
        if not folder.is_dir():
            return None
        folder = next((entry for entry in folder.iterdir() if entry.name.lower() == name), None)
        if folder is None:
            return None
    return folder


def resolve(source):
    """What the source is: ('folder', Fonts), ('image', install.wim or .esd) or ('iso', file)."""
    if not source.exists():
        raise ValueError(tr('msfonts.errors.noSource', [source]))
    if source.is_file():
        kind = {'.iso': 'iso', '.wim': 'image', '.esd': 'image'}.get(source.suffix.lower())
        if kind:
            return kind, source
    elif fonts_in(source):
        return 'folder', source
    else:
        # A mounted Windows partition, then a mounted ISO.
        fonts = child(source, 'windows', 'fonts')
        if fonts and fonts_in(fonts):
            return 'folder', fonts
        for image in IMAGES:
            found = child(source, *image.split('/'))
            if found and found.is_file():
                return 'image', found
    raise ValueError(tr('msfonts.errors.unknownSource', [source]))


def seven_zip(*arguments):
    program = shutil.which('7z') or shutil.which('7zz')
    if not program:
        raise ValueError(tr('msfonts.errors.no7z'))
    # -ssc-: names match whatever their case. -bd: no progress bar in the captured output.
    return subprocess.run([program, *arguments, '-ssc-', '-bd'], capture_output=True, text=True, errors='replace')


def extract(archive, patterns, into):
    """The files of the archive that match, flat in a folder. 7z exits 1 on warnings and still extracts."""
    into.mkdir(parents=True, exist_ok=True)
    result = seven_zip('e', '-y', '-aoa', f'-o{into}', str(archive), *patterns)
    if result.returncode > 1:
        lines = (result.stderr.strip() or result.stdout.strip()).splitlines()
        raise ValueError(tr('msfonts.errors.extract', [archive, lines[-1] if lines else result.returncode]))
    return sorted(path for path in into.iterdir() if path.is_file())


def image_in_iso(iso):
    """The Windows image of the ISO and its size, read from the listing."""
    result = seven_zip('l', '-slt', str(iso), *IMAGES)
    # The first Path of the listing is the ISO itself, above the line of dashes.
    listing = result.stdout.split('\n----------\n', 1)[-1] if result.returncode <= 1 else ''
    match = re.search(r'^Path = (.+)\n(?:.+\n)*?Size = (\d+)$', listing, re.M)
    if not match:
        raise ValueError(tr('msfonts.errors.noImage', [iso]))
    return match[1], int(match[2])


def fonts_of_image(image, work):
    for root in IMAGE_ROOTS:
        files = extract(image, [f'{root}Windows/Fonts/*{suffix}' for suffix in SUFFIXES], work / 'fonts')
        if files:
            return work / 'fonts'
    raise ValueError(tr('msfonts.errors.noFonts', [image]))


def fonts_of_iso(iso, work):
    name, size = image_in_iso(iso)
    free = shutil.disk_usage(work).free
    if free < size + GIB:
        raise ValueError(tr('msfonts.errors.noSpace', [f'{(size + GIB) / GIB:.1f}', work.parent, f'{free / GIB:.1f}']))
    print(tr('msfonts.unpackingImage', [f'{size / GIB:.1f}']), flush=True)
    image = next(iter(extract(iso, [name], work / 'image')), None)
    if image is None:
        raise ValueError(tr('msfonts.errors.noImage', [iso]))
    return fonts_of_image(image, work)


def refresh():
    if shutil.which('fc-cache'):
        subprocess.run(['fc-cache', '-f', str(FONTS.parent)], check=False)


def install(source, emoji=False):
    kind, path = resolve(source.expanduser())
    CACHE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=CACHE, prefix='msfonts-') as folder:
        if kind == 'iso':
            path = fonts_of_iso(path, Path(folder))
        elif kind == 'image':
            print(tr('msfonts.extractingFonts'), flush=True)
            path = fonts_of_image(path, Path(folder))
        fonts = fonts_in(path, emoji)
        if not fonts:
            raise ValueError(tr('msfonts.errors.noFonts', [source]))
        FONTS.mkdir(parents=True, exist_ok=True)
        for font in fonts:
            # A copy with the user's own mode, whatever NTFS or the archive gave the file.
            target = FONTS / font.name.lower()
            shutil.copyfile(font, target)
            target.chmod(0o644)
    refresh()
    print(tr('msfonts.installed', [len(fonts), FONTS]))
    if not emoji:
        print(tr('msfonts.emojiSkipped'))


def families():
    if not shutil.which('fc-scan') or not fonts_in(FONTS):
        return []
    result = subprocess.run(['fc-scan', '--format', '%{family[0]}\n', str(FONTS)], capture_output=True, text=True)
    return sorted(set(filter(None, result.stdout.splitlines())), key=str.lower)


def status():
    fonts = fonts_in(FONTS)
    if not fonts:
        print(tr('msfonts.none'))
        return
    print(tr('msfonts.status', [len(fonts), FONTS]))
    names = families()
    if names:
        print(tr('msfonts.families', [', '.join(names)]))


def remove():
    fonts = fonts_in(FONTS)
    for font in fonts:
        font.unlink()
    # Only the fonts are this command's: anything else in the folder stays, and the folder with it.
    if FONTS.is_dir() and not any(FONTS.iterdir()):
        FONTS.rmdir()
    refresh()
    print(tr('msfonts.removed', [len(fonts), FONTS]))


def main(arguments=None):
    parser = argparse.ArgumentParser(prog='desktop-msfonts', description=tr('msfonts.help.description'))
    commands = parser.add_subparsers(dest='command')
    installer = commands.add_parser('install', help=tr('msfonts.help.install'))
    installer.add_argument('source', type=Path, help=tr('msfonts.help.source'))
    installer.add_argument('--emoji', action='store_true', help=tr('msfonts.help.emoji'))
    commands.add_parser('status', help=tr('msfonts.help.status'))
    commands.add_parser('remove', help=tr('msfonts.help.remove'))
    args = parser.parse_args(arguments)
    try:
        if args.command == 'install':
            install(args.source, args.emoji)
        elif args.command == 'remove':
            remove()
        else:
            status()
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == '__main__':
    sys.exit(main())

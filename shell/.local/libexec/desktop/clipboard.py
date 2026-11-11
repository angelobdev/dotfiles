#!/usr/bin/env python3
"""JSON bridge for the Quickshell clipboard panel; clipboard bytes never enter logs."""
from common import MAGICK
from i18n import tr
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

# What cliphist lists for an image: "[[ binary data 745 KiB png 2448x1600 ]]"; the type and size only when it
# could read them.
BINARY = re.compile(r'\[\[ binary data (\d+(?:\.\d+)? [KMGTP]?i?B)(?: (\w+))?(?: (\d+)x(\d+))? \]\]')


def thumbnail_folder():
    # In the runtime folder (memory, private, gone at logout), next to the other state of the shell.
    runtime = os.environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}'
    return Path(runtime)/'desktop-shell'/'clipboard'


def describe(ident, preview):
    entry = {'id': ident, 'preview': preview, 'image': preview.startswith('[[ binary data')}
    match = BINARY.fullmatch(preview)
    if match:
        entry['size'] = match[1]
        if match[2]:
            entry['format'] = match[2]
        if match[3]:
            entry['width'], entry['height'] = int(match[3]), int(match[4])
    return entry


# Thumbnails of entries no longer in the history are removed, all of them when keep is None. One being written
# (a dot file, see thumbnail) is left to the run that writes it.
def prune(keep=None):
    folder = thumbnail_folder()
    try:
        files = list(folder.iterdir())
    except OSError:
        return
    for path in files:
        if keep is None or (path.stem not in keep and not path.name.startswith('.')):
            path.unlink(missing_ok=True)


# A small PNG of an image entry, made once: cliphist decodes it, ImageMagick (with its memory limits) scales it.
def thumbnail(ident):
    folder = thumbnail_folder()
    target = folder/f'{ident}.png'
    if target.exists():
        return target
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    decoded = subprocess.run(['cliphist', 'decode', ident], capture_output=True, check=True, timeout=10)
    handle, name = tempfile.mkstemp(dir=folder, prefix='.', suffix='.png')
    os.close(handle)
    try:
        subprocess.run(MAGICK + ['-[0]', '-auto-orient', '-thumbnail', '96x96>', f'png:{name}'], input=decoded.stdout,
                       capture_output=True, check=True, timeout=20)
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('watch-text', 'watch-image', 'list', 'copy', 'delete', 'clear', 'thumbnails'))
    parser.add_argument('values', nargs='*')
    args = parser.parse_args()
    value = args.values[0] if args.values else None
    os.umask(0o077)
    cache = Path(os.environ.get('XDG_CACHE_HOME') or str(Path.home()/'.cache'))/'cliphist'
    cache.mkdir(mode=0o700, parents=True, exist_ok=True)
    cache.chmod(0o700)
    if args.action.startswith('watch-'):
        # wl-paste leaves sensitive selections to the password manager, when marked.
        limit = max(1, min(2000, int(value or 200)))
        os.execvp('wl-paste', ['wl-paste', '--type', args.action[6:], '--watch', 'cliphist', '-max-items', str(limit), 'store'])
    if args.action == 'list':
        result = subprocess.run(['cliphist', 'list'], capture_output=True, timeout=10)
        if result.returncode and b'please store something first' not in result.stderr:
            raise subprocess.CalledProcessError(result.returncode, result.args)
        data = result.stdout.decode('utf-8', 'replace')
        entries = []
        for line in data.splitlines():
            ident, sep, preview = line.partition('\t')
            if sep and ident.isdecimal():
                entries.append(describe(ident, preview))
        prune({entry['id'] for entry in entries if entry['image']})
        print(json.dumps(entries, ensure_ascii=False))
    elif args.action == 'clear':
        subprocess.run(['cliphist', 'wipe'], check=True, stdout=subprocess.DEVNULL, timeout=10)
        prune()
    elif args.action == 'thumbnails':
        # {id: path} for the entries that have one; an entry that cannot be decoded is left out.
        if not all(re.fullmatch(r'[0-9]+', ident) for ident in args.values):
            parser.error(tr('clipboard.errors.invalidId'))
        made = {}
        for ident in args.values:
            try:
                made[ident] = str(thumbnail(ident))
            except (OSError, subprocess.SubprocessError):
                pass
        print(json.dumps(made))
    else:
        if not value or not re.fullmatch(r'[0-9]+', value) or len(args.values) > 1:
            parser.error(tr('clipboard.errors.invalidId'))
        if args.action == 'copy':
            decoded = subprocess.run(['cliphist', 'decode', value], capture_output=True, check=True, timeout=10)
            subprocess.run(['wl-copy'], input=decoded.stdout, check=True, timeout=10)
        else:
            subprocess.run(['cliphist', 'delete'], input=(value+'\n').encode(), stdout=subprocess.DEVNULL, check=True, timeout=10)
            (thumbnail_folder()/f'{value}.png').unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError):
        print(tr('clipboard.errors.operationFailed'), file=sys.stderr)
        sys.exit(1)

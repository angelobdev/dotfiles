#!/usr/bin/env python3
"""JSON bridge for the Quickshell clipboard panel; clipboard bytes never enter logs."""
from i18n import tr
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('watch-text', 'watch-image', 'list', 'copy', 'delete', 'clear'))
    parser.add_argument('value', nargs='?')
    args = parser.parse_args()
    os.umask(0o077)
    cache = Path(os.environ.get('XDG_CACHE_HOME') or str(Path.home()/'.cache'))/'cliphist'
    cache.mkdir(mode=0o700, parents=True, exist_ok=True)
    cache.chmod(0o700)
    if args.action.startswith('watch-'):
        # wl-paste leaves sensitive selections to the password manager, when marked.
        limit = max(1, min(2000, int(args.value or 200)))
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
                entries.append({'id': ident, 'preview': preview, 'image': preview.startswith('[[ binary data')})
        print(json.dumps(entries, ensure_ascii=False))
    elif args.action == 'clear':
        subprocess.run(['cliphist', 'wipe'], check=True, stdout=subprocess.DEVNULL, timeout=10)
    else:
        if not args.value or not re.fullmatch(r'[0-9]+', args.value):
            parser.error(tr('clipboard.errors.invalidId'))
        if args.action == 'copy':
            decoded = subprocess.run(['cliphist', 'decode', args.value], capture_output=True, check=True, timeout=10)
            subprocess.run(['wl-copy'], input=decoded.stdout, check=True, timeout=10)
        else:
            subprocess.run(['cliphist', 'delete'], input=(args.value+'\n').encode(), stdout=subprocess.DEVNULL, check=True, timeout=10)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError):
        print(tr('clipboard.errors.operationFailed'), file=sys.stderr)
        sys.exit(1)

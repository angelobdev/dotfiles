#!/usr/bin/env python3
"""Translate an explicit Quickshell selection into XDPH 1.4's picker protocol."""
from i18n import tr
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def windows(raw):
    items = []
    # IDs belong to the portal's toplevel protocol, not Hyprland window addresses.
    for match in re.finditer(r'(\d+)\[HC>\](.*?)\[HT>\](.*?)\[HE>\](.*?)\[HA>\]', raw, re.S):
        ident, app, title, _ = match.groups()
        items.append({'id': ident, 'app': app, 'title': title})
    return items


def selection(value, outputs, entries, allow_token=False):
    kind, ident = value.get('kind'), str(value.get('id', ''))
    valid = (kind == 'screen' and ident in outputs) or (kind == 'window' and ident in {w['id'] for w in entries})
    if not valid or any(c in ident for c in '\n\r'):
        raise ValueError(tr('sharing.errors.invalidSelection'))
    return '[SELECTION]'+('r' if allow_token and value.get('remember') else '')+'/'+kind+':'+ident


def main():
    allow_token = '--allow-token' in sys.argv
    entries = windows(os.environ.get('XDPH_WINDOW_SHARING_LIST', ''))
    monitors = json.loads(subprocess.run(['hyprctl', '-j', 'monitors'], capture_output=True, text=True, check=True, timeout=10).stdout)
    outputs = [m['name'] for m in monitors]
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if not runtime:
        raise ValueError(tr('session.errors.waylandRequired'))
    with tempfile.TemporaryDirectory(prefix='desktop-share-', dir=runtime) as directory:
        result = Path(directory)/'selection.json'
        result.write_text('')
        result.chmod(0o600)
        env = dict(os.environ, DESKTOP_SHARE_WINDOWS=json.dumps(entries), DESKTOP_SHARE_RESULT=str(result),
                   DESKTOP_SHARE_ALLOW_TOKEN='1' if allow_token else '0')
        config = Path(os.environ.get('XDG_CONFIG_HOME') or str(Path.home()/'.config'))/'quickshell/desktop/share.qml'
        # Only our validated selection goes to stdout. Quickshell diagnostics use stderr.
        child = subprocess.run(['qs', '-p', str(config)], env=env, stdout=sys.stderr)
        text = result.read_text()
        if child.returncode or not text.strip():
            return 1
        print(selection(json.loads(text), outputs, entries, allow_token), flush=True)
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(tr('sharing.errors.selectionFailed', [error]), file=sys.stderr)
        sys.exit(1)

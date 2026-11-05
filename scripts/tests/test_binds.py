#!/usr/bin/env python3
"""Every bind description Hints shows is translated: a key in i18n/Sources.js or a pattern of I18n.bindDescription."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

REPO = Path(__file__).resolve().parents[2]
SHELL = REPO / 'quickshell/.config/quickshell/desktop'
# The descriptions I18n.bindDescription builds from a pattern instead of a fixed key.
PATTERNS = (r'(Focus|Move) (left|right|up|down)', r'Move to workspace \d+', r'Workspace \d+', r'Dock item \d+')


def lookup(catalog, key):
    value = catalog
    for part in key.split('.'):
        value = value.get(part) if isinstance(value, dict) else None
    return value


class BindTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('lua'), 'lua is not installed')
    def test_every_bind_description_has_a_translation(self):
        listed = subprocess.run(['lua', str(REPO / 'scripts/tests/bind_descriptions.lua'), str(REPO / 'hypr/.config/hypr')],
                                capture_output=True, text=True, check=True, timeout=30).stdout.splitlines()
        self.assertGreater(len(listed), 20)
        keys = dict(re.findall(r'^\s*"([^"]+)": "([^"]+)",?$', (SHELL / 'i18n/Sources.js').read_text(encoding='utf-8'), re.MULTILINE))
        english = json.loads((SHELL / 'i18n/en_US.json').read_text(encoding='utf-8'))
        missing = [text for text in listed if text not in keys and not any(re.fullmatch(pattern, text) for pattern in PATTERNS)]
        self.assertEqual(missing, [], 'bind descriptions without a key in i18n/Sources.js')
        unknown = sorted({keys[text] for text in listed if text in keys and not isinstance(lookup(english, keys[text]), str)})
        self.assertEqual(unknown, [], 'Sources.js keys missing from the catalog')


if __name__ == '__main__':
    unittest.main()

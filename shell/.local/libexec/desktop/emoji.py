#!/usr/bin/env python3
"""The emoji the picker offers, with names and keywords in the interface language.

list: prints {"groups": [group keys], "emoji": [{"e": emoji, "n": name, "k": keywords, "g": group index}]}.
The order and groups come from Unicode's emoji-test.txt (unicode-emoji), the names and keywords from CLDR's
annotations (cldr-emoji-annotation), Italian or English as the shell. Skin-tone variants are left out. The
result is cached per language until either source changes.
"""
from common import install_command, write_atomic
from i18n import language, tr
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ElementTree

TEST = Path('/usr/share/unicode/emoji/emoji-test.txt')
ANNOTATIONS = Path('/usr/share/unicode/cldr/common')
CACHE = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'desktop'
# emoji-test.txt group names, as the keys of their translations (emoji.groups.*).
GROUPS = {'Smileys & Emotion': 'smileys', 'People & Body': 'people', 'Animals & Nature': 'nature', 'Food & Drink': 'food',
          'Travel & Places': 'travel', 'Activities': 'activities', 'Objects': 'objects', 'Symbols': 'symbols', 'Flags': 'flags'}
SKIN_TONES = set(range(0x1F3FB, 0x1F400))
LINE = re.compile(r'^([0-9A-F ]+?)\s*;\s*fully-qualified\s*#\s*(\S+)\s+E[\d.]+\s+(.*)$')


def annotations(code):
    names, keywords = {}, {}
    for folder in ('annotations', 'annotationsDerived'):
        path = ANNOTATIONS / folder / f'{code}.xml'
        if not path.is_file():
            continue
        for node in ElementTree.parse(path).getroot().iter('annotation'):
            text = (node.text or '').strip()
            if node.get('type') == 'tts':
                names.setdefault(node.get('cp'), text)
            else:
                keywords.setdefault(node.get('cp'), ' '.join(part.strip() for part in text.split('|')))
    return names, keywords


def build(code):
    names, keywords = annotations(code)
    groups, emoji, group = [], [], -1
    for line in TEST.read_text(encoding='utf-8').splitlines():
        if line.startswith('# group:'):
            key = GROUPS.get(line.split(':', 1)[1].strip())
            if key and key not in groups:
                groups.append(key)
            group = groups.index(key) if key else -1
            continue
        match = LINE.match(line)
        if not match or group < 0 or any(int(point, 16) in SKIN_TONES for point in match[1].split()):
            continue
        character, english = match[2], match[3]
        bare = character.replace('️', '')
        emoji.append({'e': character, 'n': names.get(character) or names.get(bare) or english,
                      'k': keywords.get(character) or keywords.get(bare) or '', 'g': group})
    return {'groups': groups, 'emoji': emoji}


def listing():
    code = 'it' if language() == 'it_IT' else 'en'
    if not TEST.is_file():
        raise ValueError(tr('emoji.errors.missing', [install_command({'fedora': ['unicode-emoji', 'cldr-emoji-annotation'],
                                                                     'arch': ['unicode-emoji', 'unicode-cldr-annotations', 'unicode-cldr']})]))
    sources = [TEST] + [ANNOTATIONS / folder / f'{code}.xml' for folder in ('annotations', 'annotationsDerived')]
    signature = [int(path.stat().st_mtime) for path in sources if path.is_file()]
    cache = CACHE / f'emoji-{code}.json'
    try:
        cached = json.loads(cache.read_text(encoding='utf-8'))
        if cached.get('signature') == signature:
            return cached['data']
    except (OSError, ValueError, KeyError):
        pass
    data = build(code)
    write_atomic(cache, json.dumps({'signature': signature, 'data': data}, ensure_ascii=False))
    return data


def main():
    if sys.argv[1:] != ['list']:
        print(tr('emoji.errors.usage'), file=sys.stderr)
        return 2
    try:
        print(json.dumps(listing(), ensure_ascii=False))
    except ValueError as error:
        print(json.dumps({'error': str(error), 'groups': [], 'emoji': []}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Check the relative links of the README and the docs: the target is in the repository, with its heading."""
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
FENCED = re.compile(r'^```.*?^```', re.S | re.M)
INLINE = re.compile(r'`[^`\n]*`')
LINK = re.compile(r'\]\(([^)\s]+)(?:\s[^)]*)?\)|(?:src|href)="([^"]+)"')
HEADING = re.compile(r'^#{1,6} (.+)$', re.M)


def prose(path):
    return INLINE.sub('', FENCED.sub('', path.read_text(encoding='utf-8')))


def anchors(path):
    # GitHub's ids: lower case, no punctuation, dashes for spaces, and a counter for repeated headings.
    found, seen = set(), {}
    for heading in HEADING.findall(FENCED.sub('', path.read_text(encoding='utf-8'))):
        text = re.sub(r'[^\w\s-]', '', re.sub(r'\]\([^)]*\)', '', heading.strip().lower().replace('`', '')))
        slug = text.replace(' ', '-')
        found.add(slug + ('-' + str(seen[slug]) if slug in seen else ''))
        seen[slug] = seen.get(slug, 0) + 1
    return found


def broken(path):
    for first, second in LINK.findall(prose(path)):
        link = first or second
        parts = urlsplit(link)
        if parts.scheme or parts.netloc:
            continue
        # As on GitHub, a leading slash starts from the root. Symlinks are not followed: a link that leaves
        # the repository through the stowed $HOME exists on this machine and nowhere else.
        base = ROOT if parts.path.startswith('/') else path.parent
        target = Path(os.path.normpath(base / parts.path.lstrip('/'))) if parts.path else path
        if not target.is_relative_to(ROOT):
            yield link, 'outside the repository'
        elif not target.exists():
            yield link, 'missing file'
        elif parts.fragment and target.suffix == '.md' and parts.fragment not in anchors(target):
            yield link, 'missing heading'


def main():
    pages = [ROOT / 'README.md', ROOT / '.claude/CLAUDE.md', *sorted((ROOT / 'docs').rglob('*.md'))]
    failures = [(page, link, reason) for page in pages for link, reason in broken(page)]
    for page, link, reason in failures:
        print(f'{page.relative_to(ROOT)}: {link}: {reason}', file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Check the relative links of the README and the docs: the target exists, and so does its heading."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
FENCED = re.compile(r'^```.*?^```', re.S | re.M)
INLINE = re.compile(r'`[^`\n]*`')
LINK = re.compile(r'\]\(([^)\s]+)\)|(?:src|href)="([^"]+)"')
HEADING = re.compile(r'^#{1,6} (.+)$', re.M)
EXTERNAL = ('http://', 'https://', 'mailto:')


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
        if link.startswith(EXTERNAL):
            continue
        target, _, fragment = link.partition('#')
        resolved = (path.parent / target).resolve() if target else path
        if not resolved.exists():
            yield link, 'missing file'
        elif fragment and resolved.suffix == '.md' and fragment not in anchors(resolved):
            yield link, 'missing heading'


def main():
    pages = [ROOT / 'README.md', ROOT / '.claude/CLAUDE.md', *sorted((ROOT / 'docs').rglob('*.md'))]
    failures = [(page, link, reason) for page in pages for link, reason in broken(page)]
    for page, link, reason in failures:
        print(f'{page.relative_to(ROOT)}: {link}: {reason}', file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())

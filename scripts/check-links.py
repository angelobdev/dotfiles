#!/usr/bin/env python3
"""Check the README and the docs as GitHub renders them: links, headings and repository paths must exist."""
import functools
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
CATALOGS = 'quickshell/.config/quickshell/desktop/i18n'
# History: these pages may name paths that are gone by now.
HISTORY = ('roadmap.md', 'verification-log.md')
HEADING = re.compile(r'h[1-6]')
REPO_PATH = re.compile(r'[\w.-]+(?:/[\w.-]+)+/?')
DOC_PATH = re.compile(r'docs/[\w./-]+\.md')


class Page(HTMLParser):
    """The links, anchors and inline code of a rendered page."""

    def __init__(self):
        super().__init__()
        self.links, self.code, self.anchors, self.seen = [], [], set(), {}
        self.heading = self.snippet = None

    def handle_starttag(self, tag, attrs):
        found = dict(attrs)
        self.links += [found[name] for name in ('href', 'src') if found.get(name)]
        self.links += [entry.split()[0] for entry in (found.get('srcset') or '').split(',') if entry.strip()]
        self.anchors.update(found[name] for name in ('id', 'name') if found.get(name))
        if HEADING.fullmatch(tag):
            self.heading = []
        elif tag == 'code':
            self.snippet = []

    def handle_data(self, data):
        for text in (self.heading, self.snippet):
            if text is not None:
                text.append(data)

    def handle_endtag(self, tag):
        if HEADING.fullmatch(tag) and self.heading is not None:
            # GitHub's ids: lower case, no punctuation, dashes for spaces, and a counter for repeated headings.
            slug = re.sub(r'[^\w\- ]', '', ''.join(self.heading).strip().lower()).replace(' ', '-')
            self.anchors.add(slug + ('-' + str(self.seen[slug]) if slug in self.seen else ''))
            self.seen[slug] = self.seen.get(slug, 0) + 1
            self.heading = None
        elif tag == 'code' and self.snippet is not None:
            self.code.append(''.join(self.snippet))
            self.snippet = None


@functools.cache
def parse(path):
    # Imported here: check.sh and the tests skip this script on machines without python3-cmarkgfm.
    import cmarkgfm
    from cmarkgfm.cmark import Options
    text = path.read_text(encoding='utf-8')
    page = Page()
    page.feed(cmarkgfm.github_flavored_markdown_to_html(text, options=Options.CMARK_OPT_UNSAFE))
    page.close()
    return page


def broken(path):
    page = parse(path)
    for link in page.links:
        parts = urlsplit(link)
        if parts.scheme or parts.netloc:
            continue
        # As on GitHub, a leading slash starts from the root. Symlinks are not followed: a link that leaves
        # the repository through the stowed $HOME exists on this machine and nowhere else.
        base = ROOT if parts.path.startswith('/') else path.parent
        target = Path(os.path.normpath(base / unquote(parts.path).lstrip('/'))) if parts.path else path
        if not target.is_relative_to(ROOT):
            yield link, 'outside the repository'
        elif not target.exists():
            yield link, 'missing file'
        elif parts.fragment and target.suffix == '.md' and unquote(parts.fragment) not in parse(target).anchors:
            yield link, 'missing heading'
    if path.name not in HISTORY:
        # Code blocks end with a newline, so only inline code can match.
        for code in page.code:
            if REPO_PATH.fullmatch(code) and (ROOT / code.split('/')[0]).is_dir() and not (ROOT / code).exists():
                yield code, 'missing path'


def stale_catalogs():
    for catalog in sorted((ROOT / CATALOGS).glob('*.json')):
        for path in DOC_PATH.findall(catalog.read_text(encoding='utf-8')):
            if not (ROOT / path).exists():
                yield catalog, path, 'missing path'


def main():
    pages = [ROOT / 'README.md', ROOT / '.claude/CLAUDE.md', *sorted((ROOT / 'docs').rglob('*.md'))]
    failures = [(page, link, reason) for page in pages for link, reason in broken(page)]
    failures += stale_catalogs()
    for page, link, reason in failures:
        print(f'{page.relative_to(ROOT)}: {link}: {reason}', file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())

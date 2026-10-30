#!/usr/bin/env python3
"""check-links.py must report the links GitHub would break, and only those."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('check_links', REPO / 'scripts/check-links.py')
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


class LinkTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name).resolve() / 'repo'
        (self.root / '.claude').mkdir(parents=True)
        (self.root / 'docs/guide').mkdir(parents=True)
        (self.root / 'README.md').write_text('# Title\n', encoding='utf-8')
        (self.root / '.claude/CLAUDE.md').write_text('# Rules\n', encoding='utf-8')
        (self.root / 'docs/real.md').write_text('# A `code` title!\n\n## Twice\n\n## Twice\n', encoding='utf-8')
        patcher = mock.patch.object(links, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def report(self, text):
        page = self.root / 'docs/page.md'
        page.write_text(text, encoding='utf-8')
        return list(links.broken(page))

    def test_a_link_to_a_file_needs_the_file(self):
        self.assertEqual(self.report('[a](real.md)'), [])
        self.assertEqual(self.report('[a](nope.md)'), [('nope.md', 'missing file')])

    def test_a_link_to_a_heading_needs_the_heading(self):
        self.assertEqual(self.report('[a](real.md#a-code-title) [b](real.md#twice) [c](real.md#twice-1)'), [])
        self.assertEqual(self.report('[a](real.md#twice-2)'), [('real.md#twice-2', 'missing heading')])

    def test_a_heading_of_the_same_page(self):
        self.assertEqual(self.report('# Here\n\n[a](#here)'), [])
        self.assertEqual(self.report('[a](#nope)'), [('#nope', 'missing heading')])

    def test_a_title_does_not_hide_the_target(self):
        self.assertEqual(self.report('[a](real.md "Title")'), [])
        self.assertEqual(self.report('[a](nope.md "Title")'), [('nope.md', 'missing file')])
        self.assertEqual(self.report("[a](real.md#nope 'Title')"), [('real.md#nope', 'missing heading')])

    def test_html_attributes_are_links(self):
        self.assertEqual(self.report('<img src="nope.png">'), [('nope.png', 'missing file')])
        self.assertEqual(self.report('<a href="nope.md">a</a>'), [('nope.md', 'missing file')])

    def test_code_holds_no_links(self):
        self.assertEqual(self.report('`[a](nope.md)`\n\n```md\n[b](nope.md)\n```\n'), [])

    def test_other_schemes_are_not_files(self):
        self.assertEqual(self.report('[a](https://example.com/nope.md) [b](mailto:a@example.com) '
                                     '[c](//example.com/nope.png) <img src="data:image/png;base64,AAAA">'), [])

    def test_a_leading_slash_starts_from_the_root(self):
        self.assertEqual(self.report('[a](/README.md) [b](/docs/real.md#twice)'), [])
        self.assertEqual(self.report('[a](/real.md)'), [('/real.md', 'missing file')])

    def test_a_link_cannot_leave_the_repository(self):
        (self.root.parent / 'outside.md').write_text('# Outside\n', encoding='utf-8')
        self.assertEqual(self.report('[a](../../outside.md)'), [('../../outside.md', 'outside the repository')])

    def test_a_symlink_does_not_bring_a_link_back(self):
        # The stowed case: the path leaves the repository, and the link in $HOME points back into it.
        (self.root.parent / 'home.md').symlink_to(self.root / 'docs/real.md')
        self.assertEqual(self.report('[a](../../home.md)'), [('../../home.md', 'outside the repository')])

    def test_the_exit_code_follows_the_report(self):
        self.assertEqual(links.main(), 0)
        (self.root / 'docs/page.md').write_text('[a](nope.md)', encoding='utf-8')
        with mock.patch('sys.stderr'):
            self.assertEqual(links.main(), 1)


if __name__ == '__main__':
    unittest.main()

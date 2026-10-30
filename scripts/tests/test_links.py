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


@unittest.skipUnless(importlib.util.find_spec('cmarkgfm'), 'python3-cmarkgfm is not installed')
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

    def report(self, text, name='page.md'):
        links.parse.cache_clear()
        page = self.root / 'docs' / name
        page.write_text(text, encoding='utf-8')
        return list(links.broken(page))

    def missing(self, link):
        return [(link, 'missing file')]

    def test_a_link_to_a_file_needs_the_file(self):
        self.assertEqual(self.report('[a](real.md)'), [])
        self.assertEqual(self.report('[a](nope.md)'), self.missing('nope.md'))

    def test_a_link_to_a_heading_needs_the_heading(self):
        self.assertEqual(self.report('[a](real.md#a-code-title) [b](real.md#twice) [c](real.md#twice-1)'), [])
        self.assertEqual(self.report('[a](real.md#twice-2)'), [('real.md#twice-2', 'missing heading')])

    def test_a_heading_of_the_same_page(self):
        self.assertEqual(self.report('# Here\n\n[a](#here)'), [])
        self.assertEqual(self.report('[a](#nope)'), [('#nope', 'missing heading')])

    def test_every_kind_of_heading_has_its_anchor(self):
        text = ('<h1 align="center">One + Two</h1>\n\n## Closed ##\n\n## <kbd>Super</kbd> key\n\n'
                'Underlined\n==========\n\n <a id="plain"></a>\n\n<a name="named"></a>\n\n'
                '[a](#one--two) [b](#closed) [c](#super-key) [d](#underlined) [e](#plain) [f](#named)')
        self.assertEqual(self.report(text), [])

    def test_a_code_block_holds_no_headings(self):
        self.assertEqual(self.report('~~~sh\n# Install\n~~~\n\n[a](#install)'), [('#install', 'missing heading')])

    def test_a_title_does_not_hide_the_target(self):
        self.assertEqual(self.report('[a](real.md "Title")'), [])
        self.assertEqual(self.report('[a](nope.md "Title")'), self.missing('nope.md'))
        self.assertEqual(self.report("[a](real.md#nope 'Title')"), [('real.md#nope', 'missing heading')])

    def test_reference_links_are_links(self):
        self.assertEqual(self.report('[a][r]\n\n[r]: real.md\n'), [])
        self.assertEqual(self.report('[a][r]\n\n[r]: nope.md\n'), self.missing('nope.md'))

    def test_links_in_tables_are_links(self):
        self.assertEqual(self.report('| a |\n| - |\n| [b](nope.md) |\n'), self.missing('nope.md'))

    def test_a_table_splits_its_cells_before_reading_links(self):
        # GitHub only: plain CommonMark has no tables, and would read this as one link.
        self.assertEqual(self.report('| a | b |\n| - | - |\n| [c](nope.md|x) | d |\n'), [])

    def test_every_way_of_writing_a_target(self):
        (self.root / 'docs/sp ace.md').write_text('# Title\n', encoding='utf-8')
        (self.root / 'docs/par(1).md').write_text('# Title\n', encoding='utf-8')
        text = '[a](sp%20ace.md) [b](<sp ace.md>) [c](par(1).md) [d](real.md?raw=true) <img src="sp%20ace.md">'
        self.assertEqual(self.report(text), [])

    def test_html_attributes_are_links(self):
        self.assertEqual(self.report('<img src="nope.png">'), self.missing('nope.png'))
        self.assertEqual(self.report('<a href="nope.md">a</a>'), self.missing('nope.md'))
        self.assertEqual(self.report("<img src='nope.png'>"), self.missing('nope.png'))
        self.assertEqual(self.report('<img src=nope.png>'), self.missing('nope.png'))
        self.assertEqual(self.report('<img src = "nope.png">'), self.missing('nope.png'))

    def test_every_source_of_a_srcset(self):
        (self.root / 'docs/one.png').write_bytes(b'')
        self.assertEqual(self.report('<source srcset="one.png 1x, nope.png 2x">'), self.missing('nope.png'))

    def test_other_attributes_are_not_links(self):
        (self.root / 'docs/one.png').write_bytes(b'')
        self.assertEqual(self.report('<img data-src="nope.png" src="one.png">'), [])

    def test_code_holds_no_links(self):
        for text in ('`[a](nope.md)`', '```md\n[a](nope.md)\n```\n', '~~~\n[a](nope.md)\n~~~\n',
                     '````\n```\n[a](nope.md)\n````\n', 'text\n\n    [a](nope.md)\n',
                     '<!-- [a](nope.md) -->\n', '<pre>[a](nope.md)</pre>\n'):
            with self.subTest(text=text):
                self.assertEqual(self.report(text), [])

    def test_a_long_fence_does_not_swallow_the_text_after_it(self):
        text = '````\n```\n````\n\n[a](nope.md)\n\n```sh\nls\n```\n'
        self.assertEqual(self.report(text), self.missing('nope.md'))

    def test_other_schemes_are_not_files(self):
        self.assertEqual(self.report('[a](https://example.com/nope.md) [b](mailto:a@example.com) '
                                     '[c](//example.com/nope.png) [d](tel:+123) '
                                     '<img src="data:image/png;base64,AAAA">'), [])

    def test_a_leading_slash_starts_from_the_root(self):
        self.assertEqual(self.report('[a](/README.md) [b](/docs/real.md#twice)'), [])
        self.assertEqual(self.report('[a](/real.md)'), self.missing('/real.md'))

    def test_a_link_cannot_leave_the_repository(self):
        (self.root.parent / 'outside.md').write_text('# Outside\n', encoding='utf-8')
        self.assertEqual(self.report('[a](../../outside.md)'), [('../../outside.md', 'outside the repository')])

    def test_a_symlink_does_not_bring_a_link_back(self):
        # The stowed case: the path leaves the repository, and the link in $HOME points back into it.
        (self.root.parent / 'home.md').symlink_to(self.root / 'docs/real.md')
        self.assertEqual(self.report('[a](../../home.md)'), [('../../home.md', 'outside the repository')])

    def test_repository_paths_in_inline_code_must_exist(self):
        self.assertEqual(self.report('`docs/real.md` `docs/guide/`'), [])
        self.assertEqual(self.report('`docs/nope.md`'), [('docs/nope.md', 'missing path')])

    def test_other_inline_code_is_not_a_path(self):
        self.assertEqual(self.report('`config/nope.lua` `docs/*.md` `docs/<id>.md` `git add docs` `~/docs/nope`'), [])

    def test_code_blocks_are_not_checked_for_paths(self):
        self.assertEqual(self.report('```\ndocs/nope.md\n```\n'), [])

    def test_history_may_name_paths_that_are_gone(self):
        self.assertEqual(self.report('`docs/nope.md`', 'roadmap.md'), [])
        self.assertEqual(self.report('[a](nope.md)', 'roadmap.md'), self.missing('nope.md'))

    def test_catalogs_must_name_docs_that_exist(self):
        catalogs = self.root / links.CATALOGS
        catalogs.mkdir(parents=True)
        (catalogs / 'en_US.json').write_text('{"a": "See docs/real.md"}', encoding='utf-8')
        self.assertEqual(list(links.stale_catalogs()), [])
        (catalogs / 'it_IT.json').write_text('{"a": "Vedi docs/nope.md"}', encoding='utf-8')
        self.assertEqual(list(links.stale_catalogs()), [(catalogs / 'it_IT.json', 'docs/nope.md', 'missing path')])

    def test_the_exit_code_follows_the_report(self):
        self.assertEqual(links.main(), 0)
        links.parse.cache_clear()
        (self.root / 'docs/page.md').write_text('[a](nope.md)', encoding='utf-8')
        with mock.patch('sys.stderr'):
            self.assertEqual(links.main(), 1)

    def test_a_stale_catalog_fails_the_check(self):
        catalogs = self.root / links.CATALOGS
        catalogs.mkdir(parents=True)
        (catalogs / 'en_US.json').write_text('{"a": "See docs/nope.md"}', encoding='utf-8')
        links.parse.cache_clear()
        with mock.patch('sys.stderr'):
            self.assertEqual(links.main(), 1)


if __name__ == '__main__':
    unittest.main()

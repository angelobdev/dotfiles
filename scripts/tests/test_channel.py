#!/usr/bin/env python3
"""channel.py and release.py: versions, the branch a clone follows, the changelog sections between two releases,
What's new once per release, and the draft of a release section."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
sys.path.insert(0, str(REPO / 'scripts'))
import channel  # noqa: E402
import release  # noqa: E402

CHANGELOG = '''# Changelog

Intro.

## v1.2.0 - 2026-12-10

- Two.

## v1.1.0 - 2026-12-01

- One.

## v1.0.0 - 2026-11-26

First.
'''


def done(stdout='', code=0):
    return subprocess.CompletedProcess([], code, stdout, '')


def answering(maintainer=False, stable=True, tag='v1.1.0'):
    def git(*arguments):
        if arguments[0] == 'config':
            return done('true\n' if maintainer else '')
        if arguments[0] == 'rev-parse':
            return done('', 0 if stable else 1)
        if arguments[0] == 'describe':
            return done(tag + '\n', 0 if tag else 128)
        raise AssertionError(arguments)
    return git


class ChannelTests(unittest.TestCase):
    def test_sections_and_versions_between(self):
        self.assertEqual([section['version'] for section in channel.sections(CHANGELOG)], ['v1.2.0', 'v1.1.0', 'v1.0.0'])
        self.assertEqual(channel.sections(CHANGELOG)[2], {'version': 'v1.0.0', 'date': '2026-11-26', 'notes': 'First.'})
        self.assertEqual([section['version'] for section in channel.between(CHANGELOG, 'v1.0.0', 'v1.2.0')], ['v1.2.0', 'v1.1.0'])
        # With nothing seen, the installed version alone; an unknown or empty target, nothing.
        self.assertEqual([section['version'] for section in channel.between(CHANGELOG, '', 'v1.1.0')], ['v1.1.0'])
        self.assertEqual(channel.between(CHANGELOG, 'v1.0.0', ''), [])

    def test_versions_compare_as_numbers(self):
        self.assertGreater(channel.version_key('v1.10.0'), channel.version_key('v1.9.3'))
        self.assertEqual(channel.version_key('1.0.0'), ())

    def test_a_clone_follows_stable_and_a_maintainer_their_branch(self):
        self.assertEqual(channel.target(answering(), 'origin/main'), 'origin/stable')
        self.assertEqual(channel.target(answering(maintainer=True), 'origin/main'), 'origin/main')
        # Before the first release the remote has no stable branch.
        self.assertEqual(channel.target(answering(stable=False), 'origin/main'), 'origin/main')
        self.assertEqual(channel.target(answering(), 'origin/stable'), 'origin/stable')

    def test_moving_to_stable_takes_the_branch(self):
        self.assertEqual(channel.update_command('origin/stable', 'origin/main'), ('switch', '-C', 'stable', '--track', 'origin/stable'))
        self.assertEqual(channel.update_command('origin/stable', 'origin/stable'), ('merge', '--ff-only', 'origin/stable'))

    def test_only_release_tags_are_versions(self):
        self.assertEqual(channel.version(answering(tag='v1.1.0')), 'v1.1.0')
        self.assertEqual(channel.version(answering(tag='')), '')
        self.assertEqual(channel.version(answering(tag='nightly')), '')


class WhatsNewTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        (self.root / 'CHANGELOG.md').write_text(CHANGELOG, encoding='utf-8')
        self.state = self.root / 'state/whats-new.json'
        self.checked = self.root / 'state/updates.json'
        patcher = mock.patch.object(channel, 'REPO', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def new(self, tag='v1.2.0', current=False):
        return channel.whats_new(answering(tag=tag), current_only=current, path=self.state, checked=self.checked)

    def test_a_new_install_starts_from_its_version(self):
        self.assertEqual(self.new()['sections'], [])
        self.assertEqual(channel.seen_version(self.state), 'v1.2.0')

    def test_a_shell_from_before_releases_sees_its_version_once(self):
        self.checked.parent.mkdir(parents=True)
        self.checked.write_text('{}', encoding='utf-8')
        self.assertEqual([section['version'] for section in self.new()['sections']], ['v1.2.0'])
        channel.record_seen('v1.2.0', self.state)
        self.assertEqual(self.new()['sections'], [])

    def test_an_update_shows_every_release_since_the_one_seen(self):
        channel.record_seen('v1.0.0', self.state)
        self.assertEqual([section['version'] for section in self.new()['sections']], ['v1.2.0', 'v1.1.0'])

    def test_a_downgrade_or_no_release_shows_nothing(self):
        channel.record_seen('v1.2.0', self.state)
        self.assertEqual(self.new(tag='v1.1.0')['sections'], [])
        self.assertEqual(self.new(tag='')['sections'], [])

    def test_about_shows_the_installed_version_seen_or_not(self):
        channel.record_seen('v1.2.0', self.state)
        self.assertEqual([section['version'] for section in self.new(current=True)['sections']], ['v1.2.0'])


class ReleaseTests(unittest.TestCase):
    def test_a_draft_groups_the_subjects(self):
        subjects = ['feat: a search field (#213)', 'fix(bar): even gaps', 'docs: a guide', 'chore: pins', 'refactor: one cache']
        self.assertEqual(release.draft(subjects, 'v1.1.0', '2026-12-01'), '\n'.join([
            '## v1.1.0 - 2026-12-01', '', '### Added', '', '- A search field (#213)', '', '### Fixed', '', '- Even gaps', '',
            '### Changed', '', '- One cache', '']))
        self.assertIn('### Other\n\n- A guide\n- Pins', release.draft(subjects, 'v1.1.0', '2026-12-01', everything=True))

    def test_a_draft_is_read_back_as_its_section(self):
        text = '# Changelog\n\n' + release.draft(['feat: x'], 'v1.1.0', '2026-12-01')
        self.assertEqual(release.section(text, 'v1.1.0')['notes'], '### Added\n\n- X')

    def test_a_release_is_a_newer_version(self):
        for version, last in (('1.1.0', ''), ('v1.0.0', 'v1.0.0'), ('v0.9.0', 'v1.0.0')):
            with self.assertRaises(SystemExit):
                release.valid(version, last)
        release.valid('v1.0.1', 'v1.0.0')


if __name__ == '__main__':
    unittest.main()

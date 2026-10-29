#!/usr/bin/env python3
"""electron.py: flags right after the program, older spellings replaced, desktop-entry quoting."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import electron  # noqa: E402

FLAGS = ['--ozone-platform-hint=auto', '--enable-wayland-ime', '--wayland-text-input-version=3']


class ElectronTests(unittest.TestCase):
    def test_flags_follow_the_program_and_keep_field_codes(self):
        self.assertEqual(electron.with_flags('/usr/share/code/code --new-window %F', FLAGS),
                         '/usr/share/code/code --ozone-platform-hint=auto --enable-wayland-ime --wayland-text-input-version=3 --new-window %F')

    def test_older_spellings_are_replaced_not_doubled(self):
        line = 'chatgpt --ozone-platform=wayland --enable-features=UseOzonePlatform --enable-wayland-ime %U'
        once = electron.with_flags(line, FLAGS)
        self.assertEqual(once, 'chatgpt ' + ' '.join(FLAGS) + ' %U')
        self.assertEqual(electron.with_flags(once, FLAGS), once)

    def test_env_prefix_and_quoting(self):
        self.assertEqual(electron.with_flags('env GDK_SCALE=2 "/opt/My App/app" %U', FLAGS),
                         'env GDK_SCALE=2 "/opt/My App/app" ' + ' '.join(FLAGS) + ' %U')

    def test_rewrite_marks_the_source_and_touches_only_exec(self):
        text = '[Desktop Entry]\nName=Code\nExec=/usr/bin/code %F\n[Desktop Action new]\nExec=/usr/bin/code -n\n'
        out = electron.rewrite(text, FLAGS, Path('/usr/share/applications/code.desktop'))
        self.assertTrue(out.startswith(electron.MARKER + '/usr/share/applications/code.desktop\n'))
        self.assertIn('Name=Code\n', out)
        self.assertEqual(out.count('--enable-wayland-ime'), 2)
        self.assertEqual(electron.rewrite(out, FLAGS, Path('/usr/share/applications/code.desktop')), out)

    def test_linked_entries_are_left_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            system, target = root / 'system', root / 'user'
            (system / 'applications').mkdir(parents=True)
            target.mkdir()
            (system / 'applications/app.desktop').write_text('[Desktop Entry]\nExec=app %U\n')
            (root / 'stowed.desktop').write_text('[Desktop Entry]\nExec=app --own-flags %U\n')
            (target / 'app.desktop').symlink_to(root / 'stowed.desktop')
            (root / 'apps.conf').write_text('app\n')
            (root / 'flags.conf').write_text(' '.join(FLAGS) + '\n')
            with mock.patch.object(electron, 'APPS', root / 'apps.conf'), \
                    mock.patch.object(electron, 'FLAGS', root / 'flags.conf'), \
                    mock.patch.object(electron, 'TARGET', target), \
                    mock.patch.object(electron, 'data_dirs', return_value=[system]), \
                    mock.patch.object(sys, 'argv', ['electron.py', 'apply']):
                self.assertEqual(electron.main(), 0)
                self.assertTrue(electron.plan()[0]['linked'])
            self.assertTrue((target / 'app.desktop').is_symlink())
            self.assertIn('--own-flags', (root / 'stowed.desktop').read_text())
            self.assertNotIn('--enable-wayland-ime', (root / 'stowed.desktop').read_text())

    def test_system_entries_are_copied_with_the_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            system, target = root / 'system', root / 'user'
            (system / 'applications').mkdir(parents=True)
            (system / 'applications/app.desktop').write_text('[Desktop Entry]\nExec=app %U\n')
            (root / 'apps.conf').write_text('app\n')
            (root / 'flags.conf').write_text(' '.join(FLAGS) + '\n')
            with mock.patch.object(electron, 'APPS', root / 'apps.conf'), \
                    mock.patch.object(electron, 'FLAGS', root / 'flags.conf'), \
                    mock.patch.object(electron, 'TARGET', target), \
                    mock.patch.object(electron, 'data_dirs', return_value=[system]), \
                    mock.patch.object(sys, 'argv', ['electron.py', 'apply']):
                self.assertEqual(electron.main(), 0)
                self.assertTrue(electron.plan()[0]['current'])
            written = target / 'app.desktop'
            self.assertIn('Exec=app ' + ' '.join(FLAGS) + ' %U', written.read_text())
            self.assertEqual(written.stat().st_mode & 0o777, 0o644)


if __name__ == '__main__':
    unittest.main()

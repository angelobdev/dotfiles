#!/usr/bin/env python3
"""electron.py: flags right after the program, older spellings replaced, desktop-entry quoting."""
from pathlib import Path
import sys
import unittest

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


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""privacy.py names the processes holding a camera open, from a /proc tree."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import privacy  # noqa: E402


class CameraTests(unittest.TestCase):
    def proc(self, root, pid, name, targets):
        folder = root / str(pid)
        (folder / 'fd').mkdir(parents=True)
        (folder / 'comm').write_text(name + '\n')
        for number, target in enumerate(targets):
            os.symlink(target, folder / 'fd' / str(number))

    def test_only_video_devices_count_once_per_process(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.proc(root, 10, 'zen', ['/dev/null', '/dev/video0', '/dev/video2'])
            self.proc(root, 11, 'wireplumber', ['/dev/media0'])
            self.proc(root, 12, 'pipewire', ['/dev/video1'])
            (root / 'self').mkdir()
            self.assertEqual(privacy.cameras(str(root)), ['pipewire', 'zen'])

    def test_nothing_open(self):
        with tempfile.TemporaryDirectory() as folder:
            self.proc(Path(folder), 10, 'kitty', ['/dev/pts/1'])
            self.assertEqual(privacy.cameras(folder), [])


if __name__ == '__main__':
    unittest.main()

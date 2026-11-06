#!/usr/bin/env python3
"""about.py: what Settings → System → About reads from os-release, DMI, cpuinfo and meminfo."""
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import about  # noqa: E402


class AboutTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return str(path)

    def test_the_vendor_is_named_once(self):
        self.write('dmi/sys_vendor', 'HP\n')
        self.write('dmi/product_name', 'HP OmniBook Ultra Flip Laptop 14-fh0xxx\n')
        self.assertEqual(about.model(str(self.root / 'dmi')), 'HP OmniBook Ultra Flip Laptop 14-fh0xxx')
        self.write('dmi/product_name', 'ThinkPad X1 Yoga\n')
        self.write('dmi/sys_vendor', 'LENOVO\n')
        self.assertEqual(about.model(str(self.root / 'dmi')), 'LENOVO ThinkPad X1 Yoga')

    def test_firmware_placeholders_are_left_out(self):
        self.write('dmi/sys_vendor', 'System manufacturer\n')
        self.write('dmi/product_name', 'To Be Filled By O.E.M.\n')
        self.assertEqual(about.model(str(self.root / 'dmi')), '')
        self.assertEqual(about.model(str(self.root / 'missing')), '')

    def test_processor_memory_and_distribution(self):
        cpuinfo = self.write('cpuinfo', 'processor\t: 0\nmodel name\t: Intel(R) Core(TM) Ultra 7 258V\n\n'
                             'processor\t: 1\nmodel name\t: Intel(R) Core(TM) Ultra 7 258V\n')
        self.assertEqual(about.processor(cpuinfo), {'name': 'Intel(R) Core(TM) Ultra 7 258V', 'threads': 2})
        self.assertEqual(about.processor(str(self.root / 'none')), {'name': '', 'threads': 0})
        self.assertEqual(about.memory(self.write('meminfo', 'MemTotal:       32317956 kB\n')), '30.8 GiB')
        self.assertEqual(about.memory(str(self.root / 'none')), '')
        release = self.write('os-release', 'NAME="Fedora Linux"\nPRETTY_NAME="Fedora Linux 45 (Forty Five)"\n')
        self.assertEqual(about.os_release(release), 'Fedora Linux 45 (Forty Five)')
        self.assertEqual(about.os_release(self.write('arch', 'NAME="Arch Linux"\n')), 'Arch Linux')

    def test_a_folder_without_git_has_no_commit(self):
        self.assertEqual(about.repository(self.root), {'commit': '', 'date': '', 'changed': False, 'path': str(self.root)})


if __name__ == '__main__':
    unittest.main()

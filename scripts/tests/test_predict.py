#!/usr/bin/env python3
"""predict.py: next letters from word lists."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import predict  # noqa: E402


class WordsTests(unittest.TestCase):
    def words(self, *lists):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, text in enumerate(lists):
                path = Path(directory) / f'{index}.txt'
                path.write_text(text, encoding='utf-8')
                paths.append(path)
            return predict.Words(paths)

    def test_next_letters_follow_frequency(self):
        letters = self.words('casa 30\ncane 10\n').letters('ca')
        self.assertEqual(letters, {'s': 0.75, 'n': 0.25})

    def test_accents_count_for_their_key(self):
        self.assertEqual(self.words('caffè 10\ncaffe 10\n').letters('caff'), {'e': 1.0})

    def test_a_finished_word_adds_nothing(self):
        self.assertEqual(self.words('casa 30\ncasata 10\n').letters('casa'), {'t': 1.0})

    def test_unknown_start_gives_nothing(self):
        self.assertEqual(self.words('casa 30\n').letters('xy'), {})

    def test_each_language_counts_by_its_share(self):
        # The second list is a hundred times larger, yet both weigh the same.
        letters = self.words('alba 10\n', 'zoo 1000\n').letters('')
        self.assertEqual(letters, {'a': 0.5, 'z': 0.5})

    def test_entries_that_are_not_words_are_skipped(self):
        self.assertEqual(self.words("l'amico 50\n123 50\nora 10\n").letters(''), {'o': 1.0})

    def test_capitals_are_folded(self):
        self.assertEqual(self.words('Roma 10\nroma 10\n').letters('r'), {'o': 1.0})


class FetchTests(unittest.TestCase):
    def test_a_wrong_hash_leaves_nothing_behind(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(predict, 'DIRECTORY', Path(directory)), \
                mock.patch('urllib.request.urlopen') as urlopen:
            urlopen.return_value.__enter__.return_value.read.side_effect = [b'nope', b'']
            with self.assertRaises(ValueError):
                predict.fetch()
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_lists_already_there_are_not_downloaded(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(predict, 'DIRECTORY', Path(directory)), \
                mock.patch('urllib.request.urlopen') as urlopen:
            for path in predict.paths():
                path.write_text('casa 1\n')
            predict.fetch()
            urlopen.assert_not_called()


if __name__ == '__main__':
    unittest.main()

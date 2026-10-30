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


class SuggestionTests(WordsTests):
    def test_likeliest_first_and_at_most_three(self):
        words = self.words('casa 40\ncane 30\ncarta 20\ncaldo 10\n')
        self.assertEqual(words.suggestions('ca'), ['casa', 'cane', 'carta'])

    def test_the_word_itself_is_left_out(self):
        self.assertEqual(self.words('casa 40\ncasale 10\n').suggestions('casa'), ['casale'])

    def test_a_missing_accent_still_finds_the_word(self):
        self.assertEqual(self.words('perché 40\n').suggestions('perche'), ['perché'])
        self.assertEqual(self.words('più 40\n').suggestions('piu'), ['più'])

    def test_a_typed_accent_finds_it_too(self):
        self.assertEqual(self.words('caffè 40\n').suggestions('caffè'), [])
        self.assertEqual(self.words('città 40\n').suggestions('citt'), ['città'])

    def test_nothing_before_the_first_letter(self):
        self.assertEqual(self.words('casa 40\n').suggestions(''), [])

    def test_only_what_the_layout_can_type(self):
        self.assertEqual(self.words('señor 40\nserio 10\n').suggestions('se'), ['serio'])

    def test_both_languages_answer(self):
        words = self.words('casa 10\n', 'cat 10\n')
        self.assertEqual(sorted(words.suggestions('ca')), ['casa', 'cat'])

    def test_a_dropped_accent_gives_way_to_the_right_word(self):
        words = self.words('perche 20\nperché 17\nperchè 3\n')
        self.assertEqual(words.suggestions('perch'), ['perché'])
        self.assertEqual(self.words('citta 10\ncittà 10\n').suggestions('cit'), ['città'])

    def test_two_real_words_both_stay(self):
        words = self.words('lavoro 90\nlà 2\nla 100\n')
        self.assertEqual(words.suggestions('l'), ['la', 'lavoro', 'là'])

    def test_a_rare_accent_does_not_replace_the_common_word(self):
        self.assertEqual(self.words('chele 900\nché 1\nche 1000\n').suggestions('ch'), ['che', 'chele', 'ché'])

    def test_letters_ignore_a_missing_accent(self):
        self.assertEqual(self.words('perché 10\n').letters('perch'), {'e': 1.0})


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

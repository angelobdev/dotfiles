#!/usr/bin/env python3
"""How likely each next letter is, for the on-screen keyboard, from Italian and English word frequencies.

fetch: downloads the word lists that are missing (FrequencyWords, CC-BY-SA-4.0, pinned by commit and hash)
into ~/.local/share/desktop/keyboard/. Only the lists come from outside; nothing typed leaves the machine.
"""
from common import replacing
import bisect
import functools
import hashlib
import os
from pathlib import Path
import sys

COMMIT = '525f9b560de45753a5ea01069454e72e9aa541c6'
URL = 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/' + COMMIT + '/content/2018/{0}/{0}_50k.txt'
LISTS = {'it': 'bb96cdcb56d28342c1e909db6b2525448b7767136b7e86a2ccc649a1be66fc19',
         'en': '5351ff405b1126ef555791dd4d9798a48e3e9a501a9fc481a9da957752cfb458'}
DIRECTORY = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share') / 'desktop/keyboard'
# Accents hang off their base letter on the keyboard: a likely è makes the e key likely.
BASE = str.maketrans('àèéìòù', 'aeeiou')


def paths():
    return [DIRECTORY / (language + '.txt') for language in LISTS]


def fetch():
    # Here and not at the top: osk.py imports this module, and urllib would add 8 MB to it for nothing.
    import urllib.request
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    for language, expected in LISTS.items():
        path = DIRECTORY / (language + '.txt')
        if path.exists():
            continue
        digest = hashlib.sha256()
        with replacing(path) as temporary, urllib.request.urlopen(URL.format(language), timeout=30) as response:
            with open(temporary, 'wb') as file:
                while block := response.read(65536):
                    digest.update(block)
                    file.write(block)
            if digest.hexdigest() != expected:
                raise ValueError(language + ': unexpected word list')


class Words:
    # Each word counts by its share of its language, so neither list drowns the other.
    def __init__(self, sources):
        shares = {}
        for source in sources:
            counts = {}
            for line in Path(source).read_text(encoding='utf-8').splitlines():
                word, _, count = line.rpartition(' ')
                if word.isalpha():
                    counts[word.lower()] = counts.get(word.lower(), 0) + int(count)
            total = sum(counts.values()) or 1
            for word, count in counts.items():
                shares[word] = shares.get(word, 0) + count / total
        self.words = sorted(shares)
        self.shares = [shares[word] for word in self.words]
        self.letters = functools.lru_cache(maxsize=256)(self.letters)

    def letters(self, prefix):
        low = bisect.bisect_left(self.words, prefix)
        high = bisect.bisect_left(self.words, prefix + '\U0010ffff')
        found = {}
        for index in range(low, high):
            word = self.words[index]
            if len(word) > len(prefix):
                letter = word[len(prefix)].translate(BASE)
                found[letter] = found.get(letter, 0) + self.shares[index]
        total = sum(found.values())
        return {letter: round(share / total, 4) for letter, share in found.items()} if total else {}


def main():
    if sys.argv[1:] != ['fetch']:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    fetch()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""Next letters and word completions for the on-screen keyboard, from Italian and English word frequencies.

fetch: downloads the word lists that are missing (FrequencyWords, CC-BY-SA-4.0, pinned by commit and hash)
into ~/.local/share/desktop/keyboard/. Only the lists come from outside; nothing typed leaves the machine.
"""
from common import replacing
import bisect
import functools
import hashlib
import heapq
import os
from pathlib import Path
import re
import sys

COMMIT = '525f9b560de45753a5ea01069454e72e9aa541c6'
URL = 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/' + COMMIT + '/content/2018/{0}/{0}_50k.txt'
LISTS = {'it': 'bb96cdcb56d28342c1e909db6b2525448b7767136b7e86a2ccc649a1be66fc19',
         'en': '5351ff405b1126ef555791dd4d9798a48e3e9a501a9fc481a9da957752cfb458'}
DIRECTORY = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share') / 'desktop/keyboard'
# Accents hang off their base letter on the keyboard: a likely è makes the e key likely, and "perche"
# finds "perché".
BASE = str.maketrans('àèéìòù', 'aeeiou')
# Only what the layout can type is worth suggesting.
TYPABLE = re.compile('[a-zàèéìòù]+')


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


# Subtitles often drop accents or pick the wrong one. Where a word needs its accent the accented form is
# common next to the plain one (perché, già); where both are words it is rare (là, sì).
def misspelled(shares):
    variants = {}
    for word in shares:
        if word.translate(BASE) != word:
            variants.setdefault(word.translate(BASE), []).append(word)
    hidden = set()
    for base, accented in variants.items():
        best = max(accented, key=shares.get)
        hidden.update(word for word in accented if word != best)
        if shares[best] * 2 >= shares.get(base, 0):
            hidden.add(base)
    return hidden


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
        self.words = sorted(shares, key=lambda word: word.translate(BASE))
        self.bases = [word.translate(BASE) for word in self.words]
        self.shares = [shares[word] for word in self.words]
        self.hidden = misspelled(shares)
        self.letters = functools.lru_cache(maxsize=256)(self.letters)
        self.suggestions = functools.lru_cache(maxsize=256)(self.suggestions)

    def span(self, prefix):
        base = prefix.translate(BASE)
        return bisect.bisect_left(self.bases, base), bisect.bisect_left(self.bases, base + '\U0010ffff')

    def letters(self, prefix):
        found = {}
        low, high = self.span(prefix)
        for index in range(low, high):
            if len(self.bases[index]) > len(prefix):
                letter = self.bases[index][len(prefix)]
                found[letter] = found.get(letter, 0) + self.shares[index]
        total = sum(found.values())
        return {letter: round(share / total, 4) for letter, share in found.items()} if total else {}

    # The likeliest words starting like this one, itself left out. With no letters yet there is nothing to
    # go on: predicting a whole next word would need pairs of words.
    def suggestions(self, prefix, count=3):
        if not prefix:
            return []
        low, high = self.span(prefix)
        found = [index for index in range(low, high) if self.words[index] != prefix and self.words[index] not in self.hidden
                 and TYPABLE.fullmatch(self.words[index])]
        return [self.words[index] for index in heapq.nlargest(count, found, key=self.shares.__getitem__)]


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

"""Row 2010, Complexity Science: Lempel-Ziv 1976 complexity of a binary word.

lz_complexity(word): word is a string of 1 to 60 characters, each '0' or '1'.
The word is parsed left to right into phrases: a phrase starting at index i
is the shortest slice word[i:j] that does not occur anywhere inside
word[:j - 1] (the earlier text plus the phrase without its last character,
so a phrase may overlap itself); when no such slice exists the rest of the
word is the last phrase. Reported: length, phrases (in order), complexity
(the phrase count), longest (the longest phrase length) and ratio (complexity
divided by length as an exact Fraction). Checks, in this order: word type,
word length, each character in order.
NOT_CLAIMED: randomness tests, entropy estimates, data compression claims,
production readiness.
"""
from fractions import Fraction

SCOPE = 'PARTIAL: Lempel-Ziv 1976 phrase parsing of one supplied binary word, no randomness or entropy claim'
NOT_CLAIMED = ('randomness tests', 'entropy estimates', 'data compression claims',
               'production readiness')

MIN_WORD = 1
MAX_WORD = 60


def lz_complexity(word):
    if type(word) is not str:
        raise TypeError('word must be a string')
    if not MIN_WORD <= len(word) <= MAX_WORD:
        raise ValueError('word must hold 1 to 60 characters')
    for i, ch in enumerate(word, 1):
        if ch != '0' and ch != '1':
            raise ValueError(f"character {i}: expected '0' or '1'")
    phrases = []
    i = 0
    while i < len(word):
        j = i + 1
        while j <= len(word) and word[i:j] in word[:j - 1]:
            j += 1
        phrases.append(word[i:j])
        i = j
    return {'length': len(word),
            'phrases': phrases,
            'complexity': len(phrases),
            'longest': max(len(p) for p in phrases),
            'ratio': Fraction(len(phrases), len(word))}

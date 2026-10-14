"""Row 554, Natural Language Processing: a word and sentence profile of supplied text.

Understands text only as counts. text is a str of 0 to 2000 characters.
Words are runs of ASCII letters and digits with ASCII letters lowered;
every other character separates words. Sentences: split the text at each
of the characters . ! ? and count the pieces that hold at least one
word, so '3.5' counts as two pieces and a trailing piece without a
terminator counts. Reported: words (count with repeats), distinct,
sentences, longest (the longest word, first seen on a length tie, or
None) and top (up to 3 (word, count) rows, highest count first, ties in
alphabetical order). Cap (checked before any work): 0 to 2000 characters.
NOT_CLAIMED: part-of-speech tagging, parsing, meaning, sentiment,
abbreviation handling, multilingual text, accuracy, production readiness.
"""
SCOPE = 'PARTIAL: word and sentence counting over supplied text, no language understanding'
NOT_CLAIMED = ('part-of-speech tagging', 'parsing', 'meaning', 'sentiment',
               'abbreviation handling', 'multilingual text', 'accuracy',
               'production readiness')

MAX_TEXT = 2000
TOP_N = 3
_LOWER = 'abcdefghijklmnopqrstuvwxyz'
_UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
_DIGITS = '0123456789'
_STOPS = '.!?'


def profile(text):
    if type(text) is not str:
        raise TypeError('text must be a str')
    if len(text) > MAX_TEXT:
        raise ValueError('text must be at most 2000 characters')
    words = []
    sentences = 0
    current = ''
    piece_has_word = False
    for ch in text + '.':
        if ch in _UPPER:
            ch = _LOWER[_UPPER.index(ch)]
        if ch in _LOWER or ch in _DIGITS:
            current += ch
            continue
        if current:
            words.append(current)
            piece_has_word = True
            current = ''
        if ch in _STOPS:
            if piece_has_word:
                sentences += 1
            piece_has_word = False
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    longest = None
    for word in words:
        if longest is None or len(word) > len(longest):
            longest = word
    top = sorted(counts.items(), key=lambda row: (-row[1], row[0]))[:TOP_N]
    return {'words': len(words), 'distinct': len(counts), 'sentences': sentences,
            'longest': longest, 'top': top}

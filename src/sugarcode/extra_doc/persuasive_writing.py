"""Row 711, Persuasive Writing (Bounded: one exact copy-audit rule): measurable checks on a supplied piece of copy.

check_copy(sentences) takes sentences as a list of 0 to 40 exact strings, each 1 to 200 characters. A word is a
whitespace-separated token; a keyword is a word lowercased and stripped of leading and trailing .,!?;:'"()
characters. The rules, applied to each sentence i (0-based), are:
  more than 24 words, else (i, 'too_long');
  any keyword in ABSOLUTES, else nothing - if one appears, (i, 'absolute_claim') is reported once for the sentence.
It returns {'problems': sorted (index, code), 'you': the number of sentences holding the keyword "you" or "your",
'questions': the number of sentences ending in '?', 'words': the total word count}.
Order of checks: sentences (list type, count, then each in order: string type, length bounds), and only then the rules.

NOT_CLAIMED: this counts surface features of supplied sentences. It does not say that the copy persuaded anyone,
that the absolutes are false, or that second-person address helps. No clinical or wet-lab claim.
"""

ABSOLUTES = frozenset({'always', 'never', 'guaranteed', 'best', 'perfect', 'unbeatable'})
_STRIP = '.,!?;:\'"()'
_ADDRESS = frozenset({'you', 'your'})


def _keywords(sentence):
    return [w.strip(_STRIP).lower() for w in sentence.split()]


def check_copy(sentences):
    if type(sentences) is not list:
        raise TypeError('sentences must be an exact list')
    if len(sentences) > 40:
        raise ValueError('sentence count must be at most 40')
    for s in sentences:
        if type(s) is not str:
            raise TypeError('each sentence must be an exact string')
        if not 1 <= len(s) <= 200:
            raise ValueError('sentence length must be 1 to 200 characters')
    problems = []
    you = 0
    questions = 0
    words = 0
    for i, s in enumerate(sentences):
        keys = _keywords(s)
        words += len(keys)
        if len(keys) > 24:
            problems.append((i, 'too_long'))
        if any(k in ABSOLUTES for k in keys):
            problems.append((i, 'absolute_claim'))
        if any(k in _ADDRESS for k in keys):
            you += 1
        if s.endswith('?'):
            questions += 1
    return {'problems': sorted(problems), 'you': you, 'questions': questions, 'words': words}

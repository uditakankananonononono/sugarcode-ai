"""Row 735, Explaining Complex Ideas (Bounded: one exact jargon rule): first-use explanation check on supplied text.

check_explainer(sentences, terms) takes sentences as a list of 0 to 60 exact strings of 1 to 300 characters and terms as
a list of 0 to 20 exact strings of 1 to 24 lowercase identifier characters: the jargon a reader may not know. A word is
a whitespace-separated token; a keyword is a word lowercased and stripped of leading and trailing .,!?;:'"() characters.
The rules, applied to each sentence i (0-based), are:
  more than 30 words, else (i, 'too_long');
  3 or more distinct terms among its keywords, else (i, 'packed').
A term's first use is the lowest-indexed sentence holding it as a keyword. The first use counts as explained when that
sentence holds a '(' character or the keyword "means" or "called"; otherwise the term is unexplained.
It returns {'problems': sorted (index, code), 'unexplained': the sorted terms whose first use is not explained,
'first_use': {term: first-use index} for every term that occurs, keyed in sorted order}.
Order of checks: sentences (list type, count, then each in order: string type, length bounds), terms (list type, count,
then each in order: string type, shape), and only then the rules.

NOT_CLAIMED: this checks where supplied terms first appear and whether a fixed marker sits in that sentence. It does
not say the explanation is correct, that the reader understood, or that the idea was made accessible. No clinical or
wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
_STRIP = '.,!?;:\'"()'
_MARKERS = frozenset({'means', 'called'})


def _keywords(sentence):
    return [w.strip(_STRIP).lower() for w in sentence.split()]


def check_explainer(sentences, terms):
    if type(sentences) is not list:
        raise TypeError('sentences must be an exact list')
    if len(sentences) > 60:
        raise ValueError('sentence count must be at most 60')
    for s in sentences:
        if type(s) is not str:
            raise TypeError('each sentence must be an exact string')
        if not 1 <= len(s) <= 300:
            raise ValueError('sentence length must be 1 to 300 characters')
    if type(terms) is not list:
        raise TypeError('terms must be an exact list')
    if len(terms) > 20:
        raise ValueError('term count must be at most 20')
    for t in terms:
        if type(t) is not str:
            raise TypeError('each term must be an exact string')
        if LABEL.fullmatch(t) is None:
            raise ValueError('term must be 1 to 24 lowercase identifier characters')
    problems = []
    first_use = {}
    for i, s in enumerate(sentences):
        keys = _keywords(s)
        if len(keys) > 30:
            problems.append((i, 'too_long'))
        present = {t for t in terms if t in keys}
        if len(present) >= 3:
            problems.append((i, 'packed'))
        for t in present:
            if t not in first_use:
                first_use[t] = i
    unexplained = []
    for t, i in first_use.items():
        s = sentences[i]
        if '(' not in s and not (_MARKERS & set(_keywords(s))):
            unexplained.append(t)
    return {'problems': sorted(problems), 'unexplained': sorted(unexplained),
            'first_use': {t: first_use[t] for t in sorted(first_use)}}

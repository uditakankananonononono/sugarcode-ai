"""Row 404, Brand Voice Development (Bounded: one exact word-list rule): check supplied lines against a supplied voice.

check_voice(avoid, lines) takes avoid as a list of 0 to 10 exact lowercase words of 1 to 16 ASCII letters and lines as a
list of 0 to 20 exact strings of 1 to 200 characters. A line is split on spaces; a word is compared after ASCII lowercase
folding with trailing '.,!?' removed. The rules, applied to each line i (0-based):
  a word in avoid, else (i, 'avoided_word');
  fewer than 3 words, else (i, 'too_short');
  a line equal to an earlier line after folding, else (i, 'repeat').
It returns {'problems': sorted (index, code), 'hits': sorted (word, count) pairs of avoid words found, 'words': total word count}.
Order of checks: avoid (list type, count, then each: type, shape), lines (list type, count, then each: type, length), and
only then the rules.

NOT_CLAIMED: this checks supplied text against a supplied list. It does not say the voice is consistent, on brand or
well written. No clinical or wet-lab claim.
"""
import re

WORD = re.compile(r'[a-z]{1,16}\Z')


def check_voice(avoid, lines):
    if type(avoid) is not list:
        raise TypeError('avoid must be an exact list')
    if len(avoid) > 10:
        raise ValueError('avoid count must be at most 10')
    for w in avoid:
        if type(w) is not str:
            raise TypeError('avoid word must be an exact string')
        if WORD.fullmatch(w) is None:
            raise ValueError('avoid word must be 1 to 16 lowercase ASCII letters')
    if type(lines) is not list:
        raise TypeError('lines must be an exact list')
    if len(lines) > 20:
        raise ValueError('line count must be at most 20')
    for s in lines:
        if type(s) is not str:
            raise TypeError('line must be an exact string')
        if not 1 <= len(s) <= 200:
            raise ValueError('line length must be 1 to 200 characters')
    bad = set(avoid)
    problems, hits, total, seen = [], {}, 0, set()
    for i, s in enumerate(lines):
        toks = [_fold(t) for t in s.split(' ') if t != '']
        total += len(toks)
        found = [t for t in toks if t in bad]
        for t in found:
            hits[t] = hits.get(t, 0) + 1
        if found:
            problems.append((i, 'avoided_word'))
        if len(toks) < 3:
            problems.append((i, 'too_short'))
        key = ' '.join(toks)
        if key in seen:
            problems.append((i, 'repeat'))
        seen.add(key)
    return {'problems': sorted(problems), 'hits': sorted(hits.items()), 'words': total}


def _fold(t):
    t = ''.join(c.lower() if 'A' <= c <= 'Z' else c for c in t)
    while t and t[-1] in '.,!?':
        t = t[:-1]
    return t

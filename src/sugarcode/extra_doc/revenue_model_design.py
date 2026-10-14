"""Row 436, Revenue Model Design (PARTIAL: one exact stream-share rule): check a supplied revenue-stream list.

check_streams(streams) takes streams as a list of 0 to 40 tuples (stream, share, margin): stream 1 to 24
lowercase identifier characters, share an exact integer 1 to 100 (percent of revenue), margin an exact integer
-100 to 100 (percent). The rules, applied to each stream i (0-based), are:
  share over 50, else (i, 'dominant');
  share at least 20 with a negative margin, else (i, 'bleeding').
It returns {'problems': sorted (index, code), 'streams': sorted distinct streams present, 'total': the stream
count}.
Order of checks: streams (list type, count, then each in order: tuple type, 3 items, stream type and shape,
share type and range, margin type and range), and only then the rules.

NOT_CLAIMED: this checks supplied stream shares against two mix bars. It does not say the revenue model is
structured well, that 50 or 20 percent are the right bars, or that any revenue arrived. No clinical or wet-lab
claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_streams(streams):
    if type(streams) is not list:
        raise TypeError('streams must be an exact list')
    if len(streams) > 40:
        raise ValueError('stream count must be at most 40')
    for s in streams:
        if type(s) is not tuple:
            raise TypeError('each stream must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each stream must have 3 items')
        if type(s[0]) is not str:
            raise TypeError('stream must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('stream must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not int:
            raise TypeError('share must be an exact integer')
        if not 1 <= s[1] <= 100:
            raise ValueError('share must be 1 to 100')
        if type(s[2]) is not int:
            raise TypeError('margin must be an exact integer')
        if not -100 <= s[2] <= 100:
            raise ValueError('margin must be -100 to 100')
    problems = []
    names = set()
    for i, (stream, share, margin) in enumerate(streams):
        if share > 50:
            problems.append((i, 'dominant'))
        if share >= 20 and margin < 0:
            problems.append((i, 'bleeding'))
        names.add(stream)
    return {'problems': sorted(problems), 'streams': sorted(names), 'total': len(streams)}

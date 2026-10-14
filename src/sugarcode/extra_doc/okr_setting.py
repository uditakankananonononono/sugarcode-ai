"""Row 491, OKR Setting (PARTIAL: one exact okr check): each okr is an exact tuple
(okr, objectives, key_results) - okr an exact string of 1 to 24 lowercase identifier
characters, objectives an exact integer 0 to 10 of named objectives, key_results an
exact integer 0 to 30 of measurable results. An okr is checked against two definition
bars, and each bar it fails adds (index, code) to problems:
  objectives over 5, else (i, 'top_heavy');
  key_results below 1, else (i, 'unmeasured').
Checks run in this order: okrs must be an exact list; okr count must be at most 40;
each okr must be an exact tuple; each okr must have 3 items; okr must be an exact
string; okr must be 1 to 24 lowercase identifier characters; objectives must be an
exact integer; objectives must be 0 to 10; key_results must be an exact integer;
key_results must be 0 to 30. Returns {'problems': sorted, 'okrs': sorted distinct,
'total': number of okrs}.

NOT_CLAIMED: this checks supplied okr numbers against two definition bars. It does not
say objectives or key results are defined, that 5 objectives or 1 result are the right
bars, or that anything is achieved. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_okrs(okrs):
    """Flag okrs outside the definition bars."""
    if type(okrs) is not list:
        raise TypeError('okrs must be an exact list')
    if len(okrs) > 40:
        fail('okr count must be at most 40')
    problems = []
    names = set()
    for i, okr in enumerate(okrs):
        if type(okr) is not tuple:
            raise TypeError('each okr must be an exact tuple')
        if len(okr) != 3:
            fail('each okr must have 3 items')
        name, objectives, key_results = okr
        if type(name) is not str:
            raise TypeError('okr must be an exact string')
        if not LABEL.match(name):
            fail('okr must be 1 to 24 lowercase identifier characters')
        if type(objectives) is not int:
            raise TypeError('objectives must be an exact integer')
        if not 0 <= objectives <= 10:
            fail('objectives must be 0 to 10')
        if type(key_results) is not int:
            raise TypeError('key_results must be an exact integer')
        if not 0 <= key_results <= 30:
            fail('key_results must be 0 to 30')
        if objectives > 5:
            problems.append((i, 'top_heavy'))
        if key_results < 1:
            problems.append((i, 'unmeasured'))
        names.add(name)
    return {'problems': sorted(problems), 'okrs': sorted(names), 'total': len(okrs)}

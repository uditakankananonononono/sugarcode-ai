"""Row 498, Fundraising Strategy (PARTIAL: one exact round check): each round is an
exact tuple (round, target_k, months) - round an exact string of 1 to 24 lowercase
identifier characters, target_k an exact integer 0 to 100000 of thousands sought,
months an exact integer 0 to 36 planned to close. A round is checked against two
capital bars, and each bar it fails adds (index, code) to problems:
  target_k below 100, else (i, 'too_small');
  months over 18, else (i, 'slow_raise').
Checks run in this order: rounds must be an exact list; round count must be at most
40; each round must be an exact tuple; each round must have 3 items; round must be an
exact string; round must be 1 to 24 lowercase identifier characters; target_k must be
an exact integer; target_k must be 0 to 100000; months must be an exact integer;
months must be 0 to 36. Returns {'problems': sorted, 'rounds': sorted distinct,
'total': number of rounds}.

NOT_CLAIMED: this checks supplied round numbers against two capital bars. It does not
say capital is raised, that 100 thousand or 18 months are the right bars, or that any
investor commits. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_rounds(rounds):
    """Flag rounds outside the capital bars."""
    if type(rounds) is not list:
        raise TypeError('rounds must be an exact list')
    if len(rounds) > 40:
        fail('round count must be at most 40')
    problems = []
    names = set()
    for i, round_ in enumerate(rounds):
        if type(round_) is not tuple:
            raise TypeError('each round must be an exact tuple')
        if len(round_) != 3:
            fail('each round must have 3 items')
        name, target_k, months = round_
        if type(name) is not str:
            raise TypeError('round must be an exact string')
        if not LABEL.match(name):
            fail('round must be 1 to 24 lowercase identifier characters')
        if type(target_k) is not int:
            raise TypeError('target_k must be an exact integer')
        if not 0 <= target_k <= 100000:
            fail('target_k must be 0 to 100000')
        if type(months) is not int:
            raise TypeError('months must be an exact integer')
        if not 0 <= months <= 36:
            fail('months must be 0 to 36')
        if target_k < 100:
            problems.append((i, 'too_small'))
        if months > 18:
            problems.append((i, 'slow_raise'))
        names.add(name)
    return {'problems': sorted(problems), 'rounds': sorted(names), 'total': len(rounds)}

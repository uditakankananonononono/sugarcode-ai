"""Row 790, Humility (PARTIAL: one exact credit rule).

Each supplied win is checked with two credit bars:
- 'self_promoting' when solo_claims > 2
- 'unlearning' when corrections < 1

NOT_CLAIMED: this checks supplied win numbers against two credit bars. It does not say anyone is humble, that 2 solo claims or 1 correction are the right bars, or that any credit is shared. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_wins(wins):
    if type(wins) is not list:
        raise TypeError('wins must be an exact list')
    if len(wins) > 40:
        raise ValueError('win count must be at most 40')
    problems = []
    for i, item in enumerate(wins):
        if type(item) is not tuple:
            raise TypeError('each win must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each win must have 3 items')
        name, solo_claims, corrections = item
        if type(name) is not str:
            raise TypeError('win must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('win must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('solo_claims', solo_claims, 50), ('corrections', corrections, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if solo_claims > 2:
            problems.append((i, 'self_promoting'))
        if corrections < 1:
            problems.append((i, 'unlearning'))
    return {'problems': sorted(problems),
            'wins': sorted({x[0] for x in wins}),
            'total': len(wins)}

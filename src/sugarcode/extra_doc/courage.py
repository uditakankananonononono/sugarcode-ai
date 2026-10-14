"""Row 797, Courage (PARTIAL: one exact bravery rule).

Each supplied challenge is checked with two bravery bars:
- 'avoidant' when evasions > 3
- 'unsupported' when allies < 1

NOT_CLAIMED: this checks supplied challenge numbers against two bravery bars. It does not say anyone is brave, that 3 evasions or 1 ally are the right bars, or that any fear is faced. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_challenges(challenges):
    if type(challenges) is not list:
        raise TypeError('challenges must be an exact list')
    if len(challenges) > 40:
        raise ValueError('challenge count must be at most 40')
    problems = []
    for i, item in enumerate(challenges):
        if type(item) is not tuple:
            raise TypeError('each challenge must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each challenge must have 3 items')
        name, evasions, allies = item
        if type(name) is not str:
            raise TypeError('challenge must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('challenge must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('evasions', evasions, 50), ('allies', allies, 20)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if evasions > 3:
            problems.append((i, 'avoidant'))
        if allies < 1:
            problems.append((i, 'unsupported'))
    return {'problems': sorted(problems),
            'challenges': sorted({x[0] for x in challenges}),
            'total': len(challenges)}

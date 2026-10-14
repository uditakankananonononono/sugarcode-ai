"""Row 787, Tolerance (PARTIAL: one exact acceptance rule).

Each supplied disagreement is checked with two acceptance bars:
- 'dismissive' when interruptions > 3
- 'unheard_side' when viewpoints < 2

NOT_CLAIMED: this checks supplied disagreement numbers against two acceptance bars. It does not say anyone is tolerant, that 3 interruptions or 2 viewpoints are the right bars, or that any difference is respected. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_disagreements(disagreements):
    if type(disagreements) is not list:
        raise TypeError('disagreements must be an exact list')
    if len(disagreements) > 40:
        raise ValueError('disagreement count must be at most 40')
    problems = []
    for i, item in enumerate(disagreements):
        if type(item) is not tuple:
            raise TypeError('each disagreement must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each disagreement must have 3 items')
        name, interruptions, viewpoints = item
        if type(name) is not str:
            raise TypeError('disagreement must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('disagreement must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('interruptions', interruptions, 50), ('viewpoints', viewpoints, 20)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if interruptions > 3:
            problems.append((i, 'dismissive'))
        if viewpoints < 2:
            problems.append((i, 'unheard_side'))
    return {'problems': sorted(problems),
            'disagreements': sorted({x[0] for x in disagreements}),
            'total': len(disagreements)}

"""Row 794, Wisdom (PARTIAL: one exact judgment rule).

Each supplied decision is checked with two judgment bars:
- 'short_sighted' when horizons < 2
- 'uninformed' when lessons < 1

NOT_CLAIMED: this checks supplied decision numbers against two judgment bars. It does not say anyone is wise, that 2 horizons or 1 lesson are the right bars, or that any decision works out. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_decisions(decisions):
    if type(decisions) is not list:
        raise TypeError('decisions must be an exact list')
    if len(decisions) > 40:
        raise ValueError('decision count must be at most 40')
    problems = []
    for i, item in enumerate(decisions):
        if type(item) is not tuple:
            raise TypeError('each decision must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each decision must have 3 items')
        name, horizons, lessons = item
        if type(name) is not str:
            raise TypeError('decision must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('decision must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('horizons', horizons, 10), ('lessons', lessons, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if horizons < 2:
            problems.append((i, 'short_sighted'))
        if lessons < 1:
            problems.append((i, 'uninformed'))
    return {'problems': sorted(problems),
            'decisions': sorted({x[0] for x in decisions}),
            'total': len(decisions)}

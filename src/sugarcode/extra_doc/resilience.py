"""Row 798, Resilience (PARTIAL: one exact recovery rule).

Each supplied setback is checked with two recovery bars:
- 'staying_down' when recoveries < 1
- 'brittle' when consecutive_quits > 2

NOT_CLAIMED: this checks supplied setback numbers against two recovery bars. It does not say anyone bounces back, that 1 recovery or 2 quits are the right bars, or that any setback is overcome. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_setbacks(setbacks):
    if type(setbacks) is not list:
        raise TypeError('setbacks must be an exact list')
    if len(setbacks) > 40:
        raise ValueError('setback count must be at most 40')
    problems = []
    for i, item in enumerate(setbacks):
        if type(item) is not tuple:
            raise TypeError('each setback must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each setback must have 3 items')
        name, recoveries, consecutive_quits = item
        if type(name) is not str:
            raise TypeError('setback must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('setback must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('recoveries', recoveries, 50), ('consecutive_quits', consecutive_quits, 20)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if recoveries < 1:
            problems.append((i, 'staying_down'))
        if consecutive_quits > 2:
            problems.append((i, 'brittle'))
    return {'problems': sorted(problems),
            'setbacks': sorted({x[0] for x in setbacks}),
            'total': len(setbacks)}

"""Row 789, Gratitude (PARTIAL: one exact acknowledgment rule).

Each supplied week is checked with two acknowledgment bars:
- 'unnoticing' when thanks < 2
- 'one_sided' when received_only > 5

NOT_CLAIMED: this checks supplied week numbers against two acknowledgment bars. It does not say anyone feels grateful, that 2 thanks or 5 received-only are the right bars, or that any thanks is sincere. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_weeks(weeks):
    if type(weeks) is not list:
        raise TypeError('weeks must be an exact list')
    if len(weeks) > 40:
        raise ValueError('week count must be at most 40')
    problems = []
    for i, item in enumerate(weeks):
        if type(item) is not tuple:
            raise TypeError('each week must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each week must have 3 items')
        name, thanks, received_only = item
        if type(name) is not str:
            raise TypeError('week must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('week must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('thanks', thanks, 100), ('received_only', received_only, 100)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if thanks < 2:
            problems.append((i, 'unnoticing'))
        if received_only > 5:
            problems.append((i, 'one_sided'))
    return {'problems': sorted(problems),
            'weeks': sorted({x[0] for x in weeks}),
            'total': len(weeks)}

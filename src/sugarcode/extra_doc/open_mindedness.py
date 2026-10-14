"""Row 792, Open-mindedness (PARTIAL: one exact consideration rule).

Each supplied debate is checked with two consideration bars:
- 'closed' when alternatives < 2
- 'dismissive_fast' when snap_rejections > 3

NOT_CLAIMED: this checks supplied debate numbers against two consideration bars. It does not say anyone is open-minded, that 2 alternatives or 3 snap rejections are the right bars, or that any mind changes. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_debates(debates):
    if type(debates) is not list:
        raise TypeError('debates must be an exact list')
    if len(debates) > 40:
        raise ValueError('debate count must be at most 40')
    problems = []
    for i, item in enumerate(debates):
        if type(item) is not tuple:
            raise TypeError('each debate must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each debate must have 3 items')
        name, alternatives, snap_rejections = item
        if type(name) is not str:
            raise TypeError('debate must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('debate must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('alternatives', alternatives, 20), ('snap_rejections', snap_rejections, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if alternatives < 2:
            problems.append((i, 'closed'))
        if snap_rejections > 3:
            problems.append((i, 'dismissive_fast'))
    return {'problems': sorted(problems),
            'debates': sorted({x[0] for x in debates}),
            'total': len(debates)}

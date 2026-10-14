"""Row 788, Forgiveness (PARTIAL: one exact repair rule).

Each supplied rift is checked with two repair bars:
- 'festering' when grudges > 2
- 'unrepaired' when amends < 1

NOT_CLAIMED: this checks supplied rift numbers against two repair bars. It does not say anyone forgives, that 2 grudges or 1 amend are the right bars, or that any rift heals. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_rifts(rifts):
    if type(rifts) is not list:
        raise TypeError('rifts must be an exact list')
    if len(rifts) > 40:
        raise ValueError('rift count must be at most 40')
    problems = []
    for i, item in enumerate(rifts):
        if type(item) is not tuple:
            raise TypeError('each rift must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each rift must have 3 items')
        name, grudges, amends = item
        if type(name) is not str:
            raise TypeError('rift must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('rift must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('grudges', grudges, 50), ('amends', amends, 20)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if grudges > 2:
            problems.append((i, 'festering'))
        if amends < 1:
            problems.append((i, 'unrepaired'))
    return {'problems': sorted(problems),
            'rifts': sorted({x[0] for x in rifts}),
            'total': len(rifts)}

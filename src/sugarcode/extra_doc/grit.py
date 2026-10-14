"""Row 799, Grit (PARTIAL: one exact persistence rule).

Each supplied pursuit is checked with two persistence bars:
- 'dabbling' when weeks < 4
- 'drifting' when goal_changes > 3

NOT_CLAIMED: this checks supplied pursuit numbers against two persistence bars. It does not say anyone has grit, that 4 weeks or 3 goal changes are the right bars, or that any pursuit is finished. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_pursuits(pursuits):
    if type(pursuits) is not list:
        raise TypeError('pursuits must be an exact list')
    if len(pursuits) > 40:
        raise ValueError('pursuit count must be at most 40')
    problems = []
    for i, item in enumerate(pursuits):
        if type(item) is not tuple:
            raise TypeError('each pursuit must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each pursuit must have 3 items')
        name, weeks, goal_changes = item
        if type(name) is not str:
            raise TypeError('pursuit must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('pursuit must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('weeks', weeks, 520), ('goal_changes', goal_changes, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if weeks < 4:
            problems.append((i, 'dabbling'))
        if goal_changes > 3:
            problems.append((i, 'drifting'))
    return {'problems': sorted(problems),
            'pursuits': sorted({x[0] for x in pursuits}),
            'total': len(pursuits)}

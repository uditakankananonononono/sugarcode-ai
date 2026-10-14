"""Row 796, Temperance (PARTIAL: one exact moderation rule).

Each supplied habit is checked with two moderation bars:
- 'excessive' when indulgences > 5
- 'unbounded' when limits < 1

NOT_CLAIMED: this checks supplied habit numbers against two moderation bars. It does not say anyone is temperate, that 5 indulgences or 1 limit are the right bars, or that any habit is healthy. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_habits(habits):
    if type(habits) is not list:
        raise TypeError('habits must be an exact list')
    if len(habits) > 40:
        raise ValueError('habit count must be at most 40')
    problems = []
    for i, item in enumerate(habits):
        if type(item) is not tuple:
            raise TypeError('each habit must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each habit must have 3 items')
        name, indulgences, limits = item
        if type(name) is not str:
            raise TypeError('habit must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('habit must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('indulgences', indulgences, 100), ('limits', limits, 20)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if indulgences > 5:
            problems.append((i, 'excessive'))
        if limits < 1:
            problems.append((i, 'unbounded'))
    return {'problems': sorted(problems),
            'habits': sorted({x[0] for x in habits}),
            'total': len(habits)}

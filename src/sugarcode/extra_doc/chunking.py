"""Row 822, Chunking (PARTIAL: one exact grouping rule).

Each supplied list is checked with two grouping bars:
- 'overloaded' when items > 7
- 'ungrouped' when groups < 2

NOT_CLAIMED: this checks supplied list numbers against two grouping bars. It does not say anyone remembers more, that 7 items or 2 groups are the right bars, or that any chunk is meaningful. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_lists(lists):
    if type(lists) is not list:
        raise TypeError('lists must be an exact list')
    if len(lists) > 40:
        raise ValueError('list count must be at most 40')
    problems = []
    for i, item in enumerate(lists):
        if type(item) is not tuple:
            raise TypeError('each list must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each list must have 3 items')
        name, items, groups = item
        if type(name) is not str:
            raise TypeError('list must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('list must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('items', items, 100), ('groups', groups, 20)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if items > 7:
            problems.append((i, 'overloaded'))
        if groups < 2:
            problems.append((i, 'ungrouped'))
    return {'problems': sorted(problems),
            'lists': sorted({x[0] for x in lists}),
            'total': len(lists)}

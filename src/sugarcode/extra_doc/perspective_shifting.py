"""Row 870, Perspective Shifting (PARTIAL: one exact viewpoint rule).

Each supplied analysis is checked with two viewpoint bars:
- 'fixed_view' when viewpoints < 2
- 'surface' when reframes < 1

NOT_CLAIMED: this checks supplied analysis numbers against two viewpoint bars. It does not say anyone actually shifts perspective, that 2 viewpoints or 1 reframe are the right bars, or that any insight follows. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_analyses(analyses):
    if type(analyses) is not list:
        raise TypeError('analyses must be an exact list')
    if len(analyses) > 40:
        raise ValueError('analysis count must be at most 40')
    problems = []
    for i, item in enumerate(analyses):
        if type(item) is not tuple:
            raise TypeError('each analysis must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each analysis must have 3 items')
        name, viewpoints, reframes = item
        if type(name) is not str:
            raise TypeError('analysis must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('analysis must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('viewpoints', viewpoints, 20), ('reframes', reframes, 20)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if viewpoints < 2:
            problems.append((i, 'fixed_view'))
        if reframes < 1:
            problems.append((i, 'surface'))
    return {'problems': sorted(problems),
            'analyses': sorted({x[0] for x in analyses}),
            'total': len(analyses)}

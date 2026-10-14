"""Row 1007, Cognitive Enhancement (PARTIAL: one exact training rule).

Each supplied program is checked with two training bars:
- 'unmeasured' when baselines < 1
- 'untrained' when sessions < 5

NOT_CLAIMED: this checks supplied program numbers against two training bars. It does not say cognition improves, that 1 baseline or 5 sessions are the right bars, or that any program works. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_programs(programs):
    if type(programs) is not list:
        raise TypeError('programs must be an exact list')
    if len(programs) > 40:
        raise ValueError('program count must be at most 40')
    problems = []
    for i, item in enumerate(programs):
        if type(item) is not tuple:
            raise TypeError('each program must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each program must have 3 items')
        name, baselines, sessions = item
        if type(name) is not str:
            raise TypeError('program must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('program must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('baselines', baselines, 20), ('sessions', sessions, 1000)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if baselines < 1:
            problems.append((i, 'unmeasured'))
        if sessions < 5:
            problems.append((i, 'untrained'))
    return {'problems': sorted(problems),
            'programs': sorted({x[0] for x in programs}),
            'total': len(programs)}

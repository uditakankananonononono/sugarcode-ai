"""Row 821, Deliberate Practice (PARTIAL: one exact practice rule).

Each supplied session is checked with two practice bars:
- 'mindless' when targets < 1
- 'unreviewed' when feedback < 1

NOT_CLAIMED: this checks supplied session numbers against two practice bars. It does not say anyone improves, that 1 target or 1 feedback are the right bars, or that any practice is deliberate. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_sessions(sessions):
    if type(sessions) is not list:
        raise TypeError('sessions must be an exact list')
    if len(sessions) > 40:
        raise ValueError('session count must be at most 40')
    problems = []
    for i, item in enumerate(sessions):
        if type(item) is not tuple:
            raise TypeError('each session must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each session must have 3 items')
        name, targets, feedback = item
        if type(name) is not str:
            raise TypeError('session must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('session must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('targets', targets, 20), ('feedback', feedback, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if targets < 1:
            problems.append((i, 'mindless'))
        if feedback < 1:
            problems.append((i, 'unreviewed'))
    return {'problems': sorted(problems),
            'sessions': sorted({x[0] for x in sessions}),
            'total': len(sessions)}

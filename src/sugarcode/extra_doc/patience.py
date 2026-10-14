"""Row 786, Patience (PARTIAL: one exact pacing rule).

Each supplied wait is checked with two pacing bars:
- 'rushed' when pauses < 2
- 'irritable' when complaints > 3

NOT_CLAIMED: this checks supplied wait numbers against two pacing bars. It does not say anyone is patient, that 2 pauses or 3 complaints are the right bars, or that any wait ends well. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_waits(waits):
    if type(waits) is not list:
        raise TypeError('waits must be an exact list')
    if len(waits) > 40:
        raise ValueError('wait count must be at most 40')
    problems = []
    for i, item in enumerate(waits):
        if type(item) is not tuple:
            raise TypeError('each wait must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each wait must have 3 items')
        name, pauses, complaints = item
        if type(name) is not str:
            raise TypeError('wait must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('wait must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('pauses', pauses, 50), ('complaints', complaints, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if pauses < 2:
            problems.append((i, 'rushed'))
        if complaints > 3:
            problems.append((i, 'irritable'))
    return {'problems': sorted(problems),
            'waits': sorted({x[0] for x in waits}),
            'total': len(waits)}

"""Row 1008, Nootropics (PARTIAL: one exact regimen rule).

Each supplied regimen is checked with two tracking bars:
- 'untracked' when logs < 7
- 'unstacked_check' when interactions_unchecked > 0

NOT_CLAIMED: this checks supplied regimen numbers against two tracking bars. It does not say any substance is safe or effective, that 7 logs or 0 unchecked interactions are the right bars, or that anyone should take anything. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_regimens(regimens):
    if type(regimens) is not list:
        raise TypeError('regimens must be an exact list')
    if len(regimens) > 40:
        raise ValueError('regimen count must be at most 40')
    problems = []
    for i, item in enumerate(regimens):
        if type(item) is not tuple:
            raise TypeError('each regimen must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each regimen must have 3 items')
        name, logs, interactions_unchecked = item
        if type(name) is not str:
            raise TypeError('regimen must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('regimen must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('logs', logs, 365), ('interactions_unchecked', interactions_unchecked, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if logs < 7:
            problems.append((i, 'untracked'))
        if interactions_unchecked > 0:
            problems.append((i, 'unstacked_check'))
    return {'problems': sorted(problems),
            'regimens': sorted({x[0] for x in regimens}),
            'total': len(regimens)}

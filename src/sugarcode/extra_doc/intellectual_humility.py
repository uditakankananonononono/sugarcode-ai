"""Row 793, Intellectual Humility (PARTIAL: one exact calibration rule).

Each supplied claim is checked with two calibration bars:
- 'overconfident' when certainties > 3
- 'unhedged' when caveats < 1

NOT_CLAIMED: this checks supplied claim numbers against two calibration bars. It does not say anyone knows their limits, that 3 certainties or 1 caveat are the right bars, or that any claim is right. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_claims(claims):
    if type(claims) is not list:
        raise TypeError('claims must be an exact list')
    if len(claims) > 40:
        raise ValueError('claim count must be at most 40')
    problems = []
    for i, item in enumerate(claims):
        if type(item) is not tuple:
            raise TypeError('each claim must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each claim must have 3 items')
        name, certainties, caveats = item
        if type(name) is not str:
            raise TypeError('claim must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('claim must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('certainties', certainties, 50), ('caveats', caveats, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if certainties > 3:
            problems.append((i, 'overconfident'))
        if caveats < 1:
            problems.append((i, 'unhedged'))
    return {'problems': sorted(problems),
            'claims': sorted({x[0] for x in claims}),
            'total': len(claims)}

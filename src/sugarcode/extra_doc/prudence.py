"""Row 795, Prudence (PARTIAL: one exact caution rule).

Each supplied venture is checked with two caution bars:
- 'reckless' when safeguards < 1
- 'overleveraged' when exposures > 4

NOT_CLAIMED: this checks supplied venture numbers against two caution bars. It does not say anyone is prudent, that 1 safeguard or 4 exposures are the right bars, or that any downside is avoided. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_ventures(ventures):
    if type(ventures) is not list:
        raise TypeError('ventures must be an exact list')
    if len(ventures) > 40:
        raise ValueError('venture count must be at most 40')
    problems = []
    for i, item in enumerate(ventures):
        if type(item) is not tuple:
            raise TypeError('each venture must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each venture must have 3 items')
        name, safeguards, exposures = item
        if type(name) is not str:
            raise TypeError('venture must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('venture must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('safeguards', safeguards, 20), ('exposures', exposures, 20)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if safeguards < 1:
            problems.append((i, 'reckless'))
        if exposures > 4:
            problems.append((i, 'overleveraged'))
    return {'problems': sorted(problems),
            'ventures': sorted({x[0] for x in ventures}),
            'total': len(ventures)}

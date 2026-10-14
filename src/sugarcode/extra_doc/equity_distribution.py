"""Row 496, Equity Distribution (PARTIAL: one exact holder check): each holder is an
exact tuple (holder, percent, cliff_months) - holder an exact string of 1 to 24
lowercase identifier characters, percent an exact integer 0 to 100 of ownership,
cliff_months an exact integer 0 to 24 before vesting starts. A holder is checked
against two allocation bars, and each bar it fails adds (index, code) to problems:
  percent over 50, else (i, 'outsized');
  cliff_months below 6, else (i, 'short_cliff').
Checks run in this order: holders must be an exact list; holder count must be at most
40; each holder must be an exact tuple; each holder must have 3 items; holder must be
an exact string; holder must be 1 to 24 lowercase identifier characters; percent must
be an exact integer; percent must be 0 to 100; cliff_months must be an exact integer;
cliff_months must be 0 to 24. Returns {'problems': sorted, 'holders': sorted distinct,
'total': number of holders}.

NOT_CLAIMED: this checks supplied allocation numbers against two ownership bars. It
does not say ownership is allocated well, that 50 percent or 6 months are the right
bars, or that any vesting happens. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_holders(holders):
    """Flag holders outside the allocation bars."""
    if type(holders) is not list:
        raise TypeError('holders must be an exact list')
    if len(holders) > 40:
        fail('holder count must be at most 40')
    problems = []
    names = set()
    for i, holder in enumerate(holders):
        if type(holder) is not tuple:
            raise TypeError('each holder must be an exact tuple')
        if len(holder) != 3:
            fail('each holder must have 3 items')
        name, percent, cliff_months = holder
        if type(name) is not str:
            raise TypeError('holder must be an exact string')
        if not LABEL.match(name):
            fail('holder must be 1 to 24 lowercase identifier characters')
        if type(percent) is not int:
            raise TypeError('percent must be an exact integer')
        if not 0 <= percent <= 100:
            fail('percent must be 0 to 100')
        if type(cliff_months) is not int:
            raise TypeError('cliff_months must be an exact integer')
        if not 0 <= cliff_months <= 24:
            fail('cliff_months must be 0 to 24')
        if percent > 50:
            problems.append((i, 'outsized'))
        if cliff_months < 6:
            problems.append((i, 'short_cliff'))
        names.add(name)
    return {'problems': sorted(problems), 'holders': sorted(names), 'total': len(holders)}

"""Row 497, Cap Table Management (PARTIAL: one exact holder check): each holder is an
exact tuple (holder, shares, grants) - holder an exact string of 1 to 24 lowercase
identifier characters, shares an exact integer 0 to 1000000 held, grants an exact
integer 0 to 100 of option grants tracked. A holder is checked against two tracking
bars, and each bar it fails adds (index, code) to problems:
  shares over 500000, else (i, 'concentrated');
  grants below 1, else (i, 'untracked').
Checks run in this order: holders must be an exact list; holder count must be at most
40; each holder must be an exact tuple; each holder must have 3 items; holder must be
an exact string; holder must be 1 to 24 lowercase identifier characters; shares must
be an exact integer; shares must be 0 to 1000000; grants must be an exact integer;
grants must be 0 to 100. Returns {'problems': sorted, 'holders': sorted distinct,
'total': number of holders}.

NOT_CLAIMED: this checks supplied holding numbers against two tracking bars. It does
not say ownership is tracked correctly, that 500000 shares or 1 grant are the right
bars, or that the cap table balances. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_holders(holders):
    """Flag holders outside the tracking bars."""
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
        name, shares, grants = holder
        if type(name) is not str:
            raise TypeError('holder must be an exact string')
        if not LABEL.match(name):
            fail('holder must be 1 to 24 lowercase identifier characters')
        if type(shares) is not int:
            raise TypeError('shares must be an exact integer')
        if not 0 <= shares <= 1000000:
            fail('shares must be 0 to 1000000')
        if type(grants) is not int:
            raise TypeError('grants must be an exact integer')
        if not 0 <= grants <= 100:
            fail('grants must be 0 to 100')
        if shares > 500000:
            problems.append((i, 'concentrated'))
        if grants < 1:
            problems.append((i, 'untracked'))
        names.add(name)
    return {'problems': sorted(problems), 'holders': sorted(names), 'total': len(holders)}

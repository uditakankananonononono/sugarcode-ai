"""Row 488, PESTLE Analysis (PARTIAL: one exact scan check): each scan is an exact
tuple (scan, factors, sources) - scan an exact string of 1 to 24 lowercase identifier
characters, factors an exact integer 0 to 12 of environment factors listed, sources an
exact integer 0 to 20 consulted. A scan is checked against two coverage bars, and each
bar it fails adds (index, code) to problems:
  factors below 6, else (i, 'thin_scan');
  sources below 2, else (i, 'unsupported').
Checks run in this order: scans must be an exact list; scan count must be at most 40;
each scan must be an exact tuple; each scan must have 3 items; scan must be an exact
string; scan must be 1 to 24 lowercase identifier characters; factors must be an exact
integer; factors must be 0 to 12; sources must be an exact integer; sources must be 0
to 20. Returns {'problems': sorted, 'scans': sorted distinct, 'total': number of
scans}.

NOT_CLAIMED: this checks supplied scan numbers against two coverage bars. It does not
say the environment is scanned, that 6 factors or 2 sources are the right bars, or
that any factor is real. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_scans(scans):
    """Flag scans outside the coverage bars."""
    if type(scans) is not list:
        raise TypeError('scans must be an exact list')
    if len(scans) > 40:
        fail('scan count must be at most 40')
    problems = []
    names = set()
    for i, scan in enumerate(scans):
        if type(scan) is not tuple:
            raise TypeError('each scan must be an exact tuple')
        if len(scan) != 3:
            fail('each scan must have 3 items')
        name, factors, sources = scan
        if type(name) is not str:
            raise TypeError('scan must be an exact string')
        if not LABEL.match(name):
            fail('scan must be 1 to 24 lowercase identifier characters')
        if type(factors) is not int:
            raise TypeError('factors must be an exact integer')
        if not 0 <= factors <= 12:
            fail('factors must be 0 to 12')
        if type(sources) is not int:
            raise TypeError('sources must be an exact integer')
        if not 0 <= sources <= 20:
            fail('sources must be 0 to 20')
        if factors < 6:
            problems.append((i, 'thin_scan'))
        if sources < 2:
            problems.append((i, 'unsupported'))
        names.add(name)
    return {'problems': sorted(problems), 'scans': sorted(names), 'total': len(scans)}

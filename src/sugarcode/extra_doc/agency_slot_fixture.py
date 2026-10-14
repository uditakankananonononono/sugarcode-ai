"""Row 1276, Agency Proceedings.

agency_slot_fixture expands positive abstract start x and step y through
inclusive horizon. Returns slots (index,label) sorted by index then label,
count and empty labels. No official hearing, agency schedule, rights, filing
or attendance is verified or arranged.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
horizon defaults to 6, an exact int from 0 to 20.
Validation order: rows type, rows size, horizon, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: agency proceedings, official schedule, legal rights, filing or attendance, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied proceeding slots, no agency proceedings'
NOT_CLAIMED = ('agency proceedings', 'official schedule', 'legal rights', 'filing or attendance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def agency_slot_fixture(rows, horizon=6):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(horizon) is not int or not 0 <= horizon <= 20:
        raise ValueError('horizon must be a nonbool integer between 0 and 20')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    slots=[(t,n) for n,start,step in clean for t in range(start,horizon+1,step)]
    slots.sort(key=lambda r:(r[0],r[1]))
    return {'slots':slots,'count':len(slots),'empty':sorted(n for n,start,step in clean if start>horizon)}

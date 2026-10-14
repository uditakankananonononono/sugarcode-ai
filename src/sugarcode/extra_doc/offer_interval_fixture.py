"""Row 1219, Contract Negotiation.

offer_interval_fixture normalizes supplied endpoints, intersects all closed
intervals with an inclusive lower floor and returns intersection or None,
feasible and below_floor labels whose upper endpoint is below floor.
No actual offer, legal agreement, negotiation or binding effect is created.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
floor defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, floor, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: contract negotiation, binding offer, legal advice, agreement execution, production readiness.
"""

SCOPE = 'PARTIAL: intersects abstract supplied offer intervals, no contract negotiation'
NOT_CLAIMED = ('contract negotiation', 'binding offer', 'legal advice', 'agreement execution', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def offer_interval_fixture(rows, floor=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(floor) is not int or not 0 <= floor <= 10:
        raise ValueError('floor must be a nonbool integer between 0 and 10')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    spans=[(n,min(x,y),max(x,y)) for n,x,y in clean]
    lower=max([floor]+[a for n,a,b in spans]); upper=min(b for n,a,b in spans)
    feasible=lower<=upper
    return {'intersection':(lower,upper) if feasible else None,'feasible':feasible,
            'below_floor':sorted(n for n,a,b in spans if b<floor)}

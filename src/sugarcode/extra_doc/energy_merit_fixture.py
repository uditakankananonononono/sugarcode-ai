"""Row 1380, Energy Markets.

energy_merit_fixture dispatches abstract capacity x in ascending supplied
unit cost y, ties label ascending, until demand is met. Returns dispatch
(label,used,total_cost), unmet, total_cost and served; includes unused rows.
No energy market clearing price, network power flow, actual market model,
physical scheduling, trade execution or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
demand defaults to 7, an exact int from 0 to 20.
Validation order: rows type, rows size, demand, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: energy market model, power flow, market clearing price, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: dispatches supplied unit capacity counts by supplied merit cost, no energy market model'
NOT_CLAIMED = ('energy market model', 'power flow', 'market clearing price', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def energy_merit_fixture(rows, demand=7):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(demand) is not int or not 0 <= demand <= 20:
        raise ValueError('demand must be a nonbool integer between 0 and 20')
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
    remaining=demand; dispatch=[]
    for n,capacity,cost in sorted(clean,key=lambda r:(r[2],r[0])):
        used=min(capacity,remaining); remaining-=used
        dispatch.append((n,used,used*cost))
    return {'dispatch':dispatch,'unmet':remaining,'total_cost':sum(c for n,u,c in dispatch),
            'served':demand-remaining}

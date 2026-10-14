"""Row 1238, Labor Relations.

labor_balance_fixture subtracts supplied abstract fulfilled y from request
x and adds credit. Returns sorted signed balances, unresolved negative labels,
zero labels and total. No labor rights, dispute resolution, bargaining advice
or negotiation is performed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
credit defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, credit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: labor relations, bargaining advice, legal rights, external negotiation, production readiness.
"""

SCOPE = 'PARTIAL: balances supplied abstract request tallies, no labor relations analysis'
NOT_CLAIMED = ('labor relations', 'bargaining advice', 'legal rights', 'external negotiation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def labor_balance_fixture(rows, credit=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(credit) is not int or not 0 <= credit <= 10:
        raise ValueError('credit must be a nonbool integer between 0 and 10')
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
    balances=[(n,x-y+credit) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'balances':balances,'unresolved':[n for n,v in balances if v<0],
            'zero':[n for n,v in balances if v==0],'total':sum(v for n,v in balances)}

"""Row 1320, Cash Flow Analysis.

cash_prefix_fixture adds supplied integer inflow x minus outflow y in
label order to opening. Returns running balances, closing, negative-balance
labels and minimum over opening plus all running balances. These are count
fixtures, not money or verified cash flows; no accounting compliance or
financial/investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
opening defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, opening, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: actual cash flow, currency or source verification, accounting compliance, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied integer count running balances, no financial advice'
NOT_CLAIMED = ('actual cash flow', 'currency or source verification', 'accounting compliance', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def cash_prefix_fixture(rows, opening=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(opening) is not int or not 0 <= opening <= 10:
        raise ValueError('opening must be a nonbool integer between 0 and 10')
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
    balances=[]
    value=opening
    for n,inflow,outflow in sorted(clean,key=lambda r:r[0]):
        value+=inflow-outflow
        balances.append((n,value))
    return {'balances':balances,'closing':value,'negative':[n for n,v in balances if v<0],
            'minimum':min([opening]+[v for n,v in balances])}

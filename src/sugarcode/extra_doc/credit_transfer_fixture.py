"""Row 1363, Credit Derivatives.

credit_transfer_fixture transfers supplied loss x above retention up to
supplied cap y. Returns sorted transferred, residual loss after transfer
and total_transfer. No derivative valuation, binding contract, counterparty
analysis, credit risk model, real instrument payoff or advice is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
retention defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, retention, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: derivative valuation, legal contract, credit risk model, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: transfers abstract loss counts above retention, no derivative valuation'
NOT_CLAIMED = ('derivative valuation', 'legal contract', 'credit risk model', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def credit_transfer_fixture(rows, retention=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(retention) is not int or not 0 <= retention <= 10:
        raise ValueError('retention must be a nonbool integer between 0 and 10')
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
    values=sorted((n,min(max(x-retention,0),y)) for n,x,y in clean)
    return {'transferred':values,'residual':sorted((n,x-v) for n,x,y in clean for label,v in values if label==n),
            'total_transfer':sum(v for n,v in values)}

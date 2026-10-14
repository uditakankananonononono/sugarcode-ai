"""Row 1364, CDS Pricing.

cds_balance_fixture subtracts supplied abstract loss-count y from spread
multiplied by premium-period count x. Returns sorted net_premium, payer_surplus
positive labels, balanced zero labels and total. No actual CDS pricing,
default probability, discounting, market instrument or advice is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
spread defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, spread, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: CDS pricing, default probability, discounting, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: balances supplied premium-count and loss-count legs, no CDS pricing'
NOT_CLAIMED = ('CDS pricing', 'default probability', 'discounting', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def cds_balance_fixture(rows, spread=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(spread) is not int or not 0 <= spread <= 5:
        raise ValueError('spread must be a nonbool integer between 0 and 5')
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
    values=sorted((n,spread*x-y) for n,x,y in clean)
    return {'net_premium':values,'payer_surplus':[n for n,v in values if v>0],
            'balanced':[n for n,v in values if v==0],'total':sum(v for n,v in values)}

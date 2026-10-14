"""Row 1385, Carry Trade.

carry_difference_fixture scales supplied yield-count x minus funding-count
y by ten and subtracts fixed cost per row, including zero-count rows.
Returns sorted basis_counts, positive and negative labels excluding zero,
and total. No carry trade execution, actual yield or FX forecast, financing
terms, market pricing or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cost defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, cost, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: carry trade execution, currency forecast, market pricing, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied integer yield-count carry less fixed cost, no carry trade'
NOT_CLAIMED = ('carry trade execution', 'currency forecast', 'market pricing', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def carry_difference_fixture(rows, cost=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cost) is not int or not 0 <= cost <= 5:
        raise ValueError('cost must be a nonbool integer between 0 and 5')
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
    values=sorted((n,(x-y)*10-cost) for n,x,y in clean)
    return {'basis_counts':values,'positive':[n for n,v in values if v>0],
            'negative':[n for n,v in values if v<0],'total':sum(v for n,v in values)}

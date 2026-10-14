"""Row 1313, Alternative Fee Arrangements.

fee_compare_fixture contrasts abstract multiplier times x with supplied y.
Returns sorted options (label,first,second), first_lower, second_lower and
equal labels. No actual fee, money, valuation, legal entitlement, recommendation
or binding arrangement is determined or executed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
multiplier defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, multiplier, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: fee arrangement, real money or valuation, legal entitlement, agreement execution, production readiness.
"""

SCOPE = 'PARTIAL: contrasts abstract paired fee count tokens, no fee advice'
NOT_CLAIMED = ('fee arrangement', 'real money or valuation', 'legal entitlement', 'agreement execution', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def fee_compare_fixture(rows, multiplier=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(multiplier) is not int or not 1 <= multiplier <= 5:
        raise ValueError('multiplier must be a nonbool integer between 1 and 5')
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
    options=[(n,multiplier*x,y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'options':options,'first_lower':[n for n,a,b in options if a<b],
            'second_lower':[n for n,a,b in options if b<a],'equal':[n for n,a,b in options if a==b]}

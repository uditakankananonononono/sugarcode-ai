"""Row 1386, Purchasing Power Parity.

ppp_ratio_fixture divides supplied local basket count x by foreign basket
count y and compares strictly to supplied tenths ratio. Returns sorted
ratios as Fraction strings or None for zero denominator, above labels and
undefined labels. No actual purchasing-power estimate, comparable basket
selection, economic measurement, exchange rate forecast or advice is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tenths defaults to 10, an exact int from 1 to 20.
Validation order: rows type, rows size, tenths, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: purchasing power estimate, exchange rate forecast, economic measurement, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied basket-count ratio comparison, no purchasing-power estimate'
NOT_CLAIMED = ('purchasing power estimate', 'exchange rate forecast', 'economic measurement', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ppp_ratio_fixture(rows, tenths=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tenths) is not int or not 1 <= tenths <= 20:
        raise ValueError('tenths must be a nonbool integer between 1 and 20')
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
    from fractions import Fraction as F
    values=sorted((n,F(x,y) if y else None) for n,x,y in clean)
    return {'ratios':[(n,str(v) if v is not None else None) for n,v in values],
            'above':[n for n,v in values if v is not None and v>F(tenths,10)],
            'undefined':[n for n,v in values if v is None]}

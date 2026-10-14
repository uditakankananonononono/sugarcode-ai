"""Row 1359, Convexity.

convexity_moment_fixture computes the abstract cash x weighted mean of
period y plus shift times its successor. Returns convexity Fraction string
or None for zero cash, moment numerator, cash and defined flag. This is a
count moment, not discounted financial convexity, a derivative of bond
price, market interest sensitivity or investment advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
shift defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, shift, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: financial convexity, bond pricing, interest sensitivity, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: computes cash-weighted period-product moment, no financial convexity'
NOT_CLAIMED = ('financial convexity', 'bond pricing', 'interest sensitivity', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def convexity_moment_fixture(rows, shift=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(shift) is not int or not 0 <= shift <= 5:
        raise ValueError('shift must be a nonbool integer between 0 and 5')
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
    total=sum(x for n,x,y in clean)
    moment=sum(x*(y+shift)*(y+shift+1) for n,x,y in clean)
    return {'convexity':str(F(moment,total)) if total else None,
            'moment':moment,'cash':total,'defined':bool(total)}

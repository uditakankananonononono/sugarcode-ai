"""Row 1328, WACC Calculation.

wacc_weight_fixture weights supplied positive abstract rate x by positive
y and reduces every rate uniformly by discount percent. Returns sorted
weighted contributions as Fraction strings, mean sum and total weight.
Uniform discount is a fixture convention, not a debt-only tax shield. No debt,
equity, tax, actual financing cost, market data or financial advice is inferred.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
discount defaults to 20, an exact int from 0 to 100.
Validation order: rows type, rows size, discount, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real WACC estimate, debt or equity sourcing, tax shield inference, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: computes supplied positive weighted rate-count average, no real WACC estimate'
NOT_CLAIMED = ('real WACC estimate', 'debt or equity sourcing', 'tax shield inference', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def wacc_weight_fixture(rows, discount=20):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(discount) is not int or not 0 <= discount <= 100:
        raise ValueError('discount must be a nonbool integer between 0 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    weight=sum(y for n,x,y in clean)
    contributions=[(n,F(x*y*(100-discount),100*weight)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'contributions':[(n,str(v)) for n,v in contributions],
            'mean':str(sum((v for n,v in contributions),F(0))),'weight':weight}

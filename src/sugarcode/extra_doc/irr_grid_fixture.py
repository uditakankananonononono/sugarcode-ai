"""Row 1324, IRR Analysis.

irr_grid_fixture treats each nonnegative x as a return count at period y
and subtracts supplied outlay from its discounted sum. Checks every integer
percent rate from 0 through 100 exactly. Returns roots as those integer
rates with zero sum, unique if exactly one and outlay unchanged. This is
finite-grid equality testing, not general IRR: off-grid/negative rates and
signed cashflow multiple-root analysis are not solved. No valuation/advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
outlay defaults to 5, an exact int from 0 to 80.
Validation order: rows type, rows size, outlay, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: general IRR solving, off-grid or multiple-root completeness, real valuation, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: finds exact roots on a finite integer-percent grid, no general IRR solver'
NOT_CLAIMED = ('general IRR solving', 'off-grid or multiple-root completeness', 'real valuation', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def irr_grid_fixture(rows, outlay=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(outlay) is not int or not 0 <= outlay <= 80:
        raise ValueError('outlay must be a nonbool integer between 0 and 80')
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
    roots=[]
    for rate in range(101):
        value=sum((F(x)*F(100,100+rate)**y for n,x,y in clean),F(0))-outlay
        if value==0: roots.append(rate)
    return {'roots':roots,'unique':len(roots)==1,'outlay':outlay}

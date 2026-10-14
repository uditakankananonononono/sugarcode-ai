"""Row 1353, GARCH Models.

garch_step_fixture evaluates abstract omega plus x/10 times y squared plus
one half times y, using y as both supplied squared-shock input source and
lagged variance count by convention. Returns sorted value Fraction strings,
total and above_omega labels. No time series is fitted, coefficients estimated,
stationarity ensured or actual GARCH variance forecast/advice supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
omega defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, omega, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: fitted GARCH model, parameter estimation, stationarity guarantee, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: evaluates supplied scalar variance recursion coefficients, no fitted GARCH model'
NOT_CLAIMED = ('fitted GARCH model', 'parameter estimation', 'stationarity guarantee', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def garch_step_fixture(rows, omega=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(omega) is not int or not 0 <= omega <= 10:
        raise ValueError('omega must be a nonbool integer between 0 and 10')
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
    values=[(n,F(omega)+F(x,10)*y*y+F(1,2)*y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'values':[(n,str(v)) for n,v in values],
            'total':str(sum((v for n,v in values),F(0))),'above_omega':[n for n,v in values if v>omega]}

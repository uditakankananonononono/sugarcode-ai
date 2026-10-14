"""Row 1596, Supercapacitors.

capacitor_square_fixture divides supplied capacitance x count times
voltage y count squared by divisor. Returns sorted budgets Fraction
strings, total string, maximum string and divisor. No supercapacitor model,
physical energy estimate, charging instructions, real circuit dynamics,
physical units or engineering safety judgement is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
divisor defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, divisor, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: supercapacitor model, physical energy estimate, charging instructions, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied capacitance/voltage count squared budget, no supercapacitor model'
NOT_CLAIMED = ('supercapacitor model', 'physical energy estimate', 'charging instructions', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def capacitor_square_fixture(rows, divisor=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(divisor) is not int or not 1 <= divisor <= 5:
        raise ValueError('divisor must be a nonbool integer between 1 and 5')
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
    values=sorted((n,F(x*y*y,divisor)) for n,x,y in clean)
    return {'budgets':[(n,str(v)) for n,v in values],'total':str(sum(v for n,v in values)),
            'maximum':str(max(v for n,v in values)),'divisor':divisor}

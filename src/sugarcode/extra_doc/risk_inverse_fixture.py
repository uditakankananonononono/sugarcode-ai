"""Row 1337, Risk Parity.

risk_inverse_fixture treats x as positive supplied risk-count and computes
weights proportional to its reciprocal to integer power. y is an opaque
auxiliary tally returned only as ignored_total. Returns sorted weights as
Fraction strings, ignored_total and power. No covariance, equal risk
contributions, estimated market risk or true risk-parity portfolio is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
power defaults to 1, an exact int from 1 to 3.
Validation order: rows type, rows size, power, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: covariance risk parity, risk contribution equality, actual market risk, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: normalizes supplied positive inverse-risk counts, no covariance risk parity'
NOT_CLAIMED = ('covariance risk parity', 'risk contribution equality', 'actual market risk', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def risk_inverse_fixture(rows, power=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(power) is not int or not 1 <= power <= 3:
        raise ValueError('power must be a nonbool integer between 1 and 3')
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
    inverse=[(n,F(1,x**power)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    total=sum((v for n,v in inverse),F(0))
    return {'weights':[(n,str(v/total)) for n,v in inverse],
            'ignored_total':sum(y for n,x,y in clean),'power':power}

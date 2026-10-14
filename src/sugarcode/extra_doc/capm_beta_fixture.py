"""Row 1329, CAPM.

capm_beta_fixture evaluates supplied abstract risk_free plus integer beta
count x times supplied premium count y. Returns sorted returns, above_free
labels, mean_numerator sum and mean_denominator row count. This is formula
bookkeeping only; no beta, market premium, risk-free rate validity, expected
return, market data or investment recommendation is estimated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
risk_free defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, risk_free, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: expected return prediction, market data, risk-free rate validity, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: evaluates supplied beta-count and premium fixture formula, no expected-return prediction'
NOT_CLAIMED = ('expected return prediction', 'market data', 'risk-free rate validity', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def capm_beta_fixture(rows, risk_free=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(risk_free) is not int or not 0 <= risk_free <= 10:
        raise ValueError('risk_free must be a nonbool integer between 0 and 10')
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
    returns=[(n,risk_free+x*y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'returns':returns,'above_free':[n for n,v in returns if v>risk_free],
            'mean_numerator':sum(v for n,v in returns),'mean_denominator':len(returns)}

"""Row 1090, Storey's Method - Adaptive FDR.

storey_null_fraction encodes supplied p-values x/(100+y) and lambda as
lambda_tenths/10. Estimate raw_pi0=count(p>lambda)/(m*(1-lambda)), cap at
one for pi0. Returns above as sorted labels strictly above lambda, raw_pi0
and pi0 as exact Fraction strings. Equality does not count. This estimates
a null fraction only; it does not run an adaptive rejection procedure or
verify the estimator's statistical assumptions.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
lambda_tenths defaults to 5, an exact int from 1 to 9.
Validation order: rows type, rows size, lambda_tenths, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: p-value validity, consistent pi0, adaptive FDR guarantee, data provenance, production readiness.
"""

SCOPE = 'PARTIAL: estimates Storey pi0 from supplied rational p-values and a fixed lambda grid'
NOT_CLAIMED = ('p-value validity', 'consistent pi0', 'adaptive FDR guarantee', 'data provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def storey_null_fraction(rows, lambda_tenths=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(lambda_tenths) is not int or not 1 <= lambda_tenths <= 9:
        raise ValueError('lambda_tenths must be a nonbool integer between 1 and 9')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    lam = F(lambda_tenths, 10)
    above = sorted(n for n, x, y in clean if F(x, 100+y) > lam)
    raw = F(len(above), len(clean)) / (1 - lam)
    return {'above': above, 'raw_pi0': str(raw), 'pi0': str(min(F(1), raw))}

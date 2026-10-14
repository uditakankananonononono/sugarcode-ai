"""Row 1086, Family-Wise Error Rate - Control any false positive.

family_error_product treats x and y as marginal error percentages before
and after a supplied adjustment, assumes independent family members. Any-error
risk is one minus the product of non-error probabilities. Returns old_risk
and new_risk Fraction strings, within_limit as new risk at most limit percent,
reduction as old minus new risk Fraction string. Inputs are supplied risks,
not p-values; the independence assumption and risk accuracy are not checked.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
limit defaults to 10, an exact int from 0 to 100.
Validation order: rows type, rows size, limit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: risk calibration, independence validity, actual false positives, statistical guarantee, production readiness.
"""

SCOPE = 'PARTIAL: computes independent-family any-error probabilities from supplied marginal risks'
NOT_CLAIMED = ('risk calibration', 'independence validity', 'actual false positives', 'statistical guarantee', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def family_error_product(rows, limit=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(limit) is not int or not 0 <= limit <= 100:
        raise ValueError('limit must be a nonbool integer between 0 and 100')
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
    old_survival = new_survival = F(1)
    for n, old, new in clean:
        old_survival *= F(100 - old, 100)
        new_survival *= F(100 - new, 100)
    old_risk = 1 - old_survival
    new_risk = 1 - new_survival
    return {'old_risk': str(old_risk), 'new_risk': str(new_risk),
            'within_limit': new_risk <= F(limit, 100), 'reduction': str(old_risk - new_risk)}

"""Row 1108, Bayesian Model Averaging - Average over models.

bayesian_average uses supplied prior mass x and likelihood mass y for each
model, normalizes their products, and assigns each sorted-label model the
fixed output value zero_based_index*scale. Returns weights as sorted
(label,Fraction string), mean and variance as exact posterior-weighted value
moments Fraction strings. These are supplied finite model masses and fixed
index outputs, not fitted models or calibrated predictive probabilities.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
scale defaults to 1, an exact int from 1 to 5.
Validation order: rows type, rows size, scale, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: prior validity, likelihood validity, predictive calibration, model truth, production readiness.
"""

SCOPE = 'PARTIAL: forms posterior model weights from supplied prior and likelihood masses and averages fixed index values'
NOT_CLAIMED = ('prior validity', 'likelihood validity', 'predictive calibration', 'model truth', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def bayesian_average(rows, scale=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(scale) is not int or not 1 <= scale <= 5:
        raise ValueError('scale must be a nonbool integer between 1 and 5')
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
    nodes = sorted(clean, key=lambda r: r[0])
    raw = [prior * likelihood for n, prior, likelihood in nodes]
    total = sum(raw)
    weights = [F(value, total) for value in raw]
    mean = sum((w * i * scale for i, w in enumerate(weights)), F(0))
    variance = sum((w * (i * scale - mean) ** 2 for i, w in enumerate(weights)), F(0))
    return {'weights': [(nodes[i][0], str(w)) for i, w in enumerate(weights)],
            'mean': str(mean), 'variance': str(variance)}

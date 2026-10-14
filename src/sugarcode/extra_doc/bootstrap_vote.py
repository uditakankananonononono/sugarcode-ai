"""Row 1095, Bootstrap Aggregation - Ensemble for stability.

bootstrap_vote treats each row as a model's supplied binary predictions x,y
for two cases. Bootstrap draws model indices independently with replacement.
For each case return the exact probability of a strictly positive majority;
even-draw ties count as zero. Returns majority_probability as two Fraction
strings in case order, changed as whether probabilities differ, draws as the
number of model draws. No model is trained and no random draws are generated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 1; bool and all subclasses are refused.
draws defaults to 3, an exact int from 1 to 5.
Validation order: rows type, rows size, draws, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: trained bootstrap models, generalization, independent voters, real stability, production readiness.
"""

SCOPE = 'PARTIAL: enumerates majority outcomes of bootstrap-resampled supplied binary predictions'
NOT_CLAIMED = ('trained bootstrap models', 'generalization', 'independent voters', 'real stability', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def bootstrap_vote(rows, draws=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(draws) is not int or not 1 <= draws <= 5:
        raise ValueError('draws must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 1:
            raise ValueError('x must be a nonbool integer between 0 and 1')
        if type(y) is not int or not 0 <= y <= 1:
            raise ValueError('y must be a nonbool integer between 0 and 1')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from math import comb
    from fractions import Fraction as F
    count = len(clean)
    positives_x = sum(x for n, x, y in clean)
    positives_y = sum(y for n, x, y in clean)
    probabilities = []
    for positives in (positives_x, positives_y):
        weight = sum(comb(draws, k) * positives ** k * (count - positives) ** (draws - k)
                     for k in range(draws // 2 + 1, draws + 1))
        probabilities.append(F(weight, count ** draws))
    return {'majority_probability': [str(p) for p in probabilities],
            'changed': probabilities[0] != probabilities[1], 'draws': draws}

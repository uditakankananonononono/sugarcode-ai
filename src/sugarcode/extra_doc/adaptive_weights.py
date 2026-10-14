"""Row 1101, AdaBoost - Adaptive boosting.

adaptive_weights interprets x=0 as correct and positive x as a supplied
misclassification marker, y+1 as positive starting weight. Multiply incorrect
weights by multiplier, keep correct weights unchanged, then normalize.
Returns weights as sorted (label,Fraction string), mistakes as sorted labels
with positive markers, total as unnormalized updated sum. This is one supplied
weight update, not AdaBoost's error-based alpha selection or training.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
multiplier defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, multiplier, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: AdaBoost training, optimal alpha, generalization, error provenance, production readiness.
"""

SCOPE = 'PARTIAL: multiplies supplied misclassification weights and normalizes once, no AdaBoost is trained'
NOT_CLAIMED = ('AdaBoost training', 'optimal alpha', 'generalization', 'error provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def adaptive_weights(rows, multiplier=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(multiplier) is not int or not 1 <= multiplier <= 5:
        raise ValueError('multiplier must be a nonbool integer between 1 and 5')
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
    raw = [(n, (weight + 1) * (multiplier if error > 0 else 1)) for n, error, weight in sorted(clean, key=lambda r: r[0])]
    total = sum(w for n, w in raw)
    return {'weights': [(n, str(F(w, total))) for n, w in raw],
            'mistakes': sorted(n for n, error, weight in clean if error > 0), 'total': total}

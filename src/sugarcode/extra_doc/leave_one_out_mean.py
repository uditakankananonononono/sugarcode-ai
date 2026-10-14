"""Row 1112, Leave-One-Out - Extreme cross-validation.

leave_one_out_mean excludes each row's training x and averages the remaining
x values with pseudocount zero-valued prior observations. Evaluate against
that row's supplied y. Returns predictions and errors as sorted (label,
Fraction string) pairs, mse as average squared error Fraction string.
The positive pseudo-count supports a singleton training-empty fold.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
-10 to 10; bool and all subclasses are refused.
pseudocount defaults to 1, an exact int from 1 to 5.
Validation order: rows type, rows size, pseudocount, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: generalization guarantee, model adequacy, data provenance, optimal prior, production readiness.
"""

SCOPE = 'PARTIAL: computes leave-one-out constant-mean predictions with a supplied prior pseudo-count'
NOT_CLAIMED = ('generalization guarantee', 'model adequacy', 'data provenance', 'optimal prior', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def leave_one_out_mean(rows, pseudocount=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(pseudocount) is not int or not 1 <= pseudocount <= 5:
        raise ValueError('pseudocount must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not -10 <= x <= 10:
            raise ValueError('x must be a nonbool integer between -10 and 10')
        if type(y) is not int or not -10 <= y <= 10:
            raise ValueError('y must be a nonbool integer between -10 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    nodes = sorted(clean, key=lambda r: r[0])
    total = sum(x for n, x, y in nodes)
    predictions = [(n, F(total - target, len(nodes)-1+pseudocount)) for n, target, observed in nodes]
    errors = [(n, (prediction - observed) ** 2) for (n, prediction), (m, target, observed) in zip(predictions, nodes)]
    return {'predictions': [(n, str(v)) for n, v in predictions],
            'errors': [(n, str(v)) for n, v in errors], 'mse': str(sum(v for n, v in errors) / len(nodes))}

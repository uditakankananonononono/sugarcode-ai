"""Row 1111, Cross-Validation - Estimate generalization.

cross_validate_split sorts labels, holds out positions divisible by stride
and fits a constant mean to training x values. Evaluate squared errors on
held-out y only. Returns train_mean as Fraction string or None if training
empty, errors as (held_label,Fraction squared-error string) in label order
or empty without training, mse as average held errors Fraction string or None.
This is one deterministic validation split, not a generalization guarantee.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
-10 to 10; bool and all subclasses are refused.
stride defaults to 2, an exact int from 2 to 5.
Validation order: rows type, rows size, stride, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: generalization guarantee, random split, model adequacy, data provenance, production readiness.
"""

SCOPE = 'PARTIAL: evaluates constant-mean predictions on a deterministic holdout split'
NOT_CLAIMED = ('generalization guarantee', 'random split', 'model adequacy', 'data provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def cross_validate_split(rows, stride=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(stride) is not int or not 2 <= stride <= 5:
        raise ValueError('stride must be a nonbool integer between 2 and 5')
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
    train = [target for i, (n, target, observed) in enumerate(nodes) if i % stride != 0]
    held = [(n, observed) for i, (n, target, observed) in enumerate(nodes) if i % stride == 0]
    mean = F(sum(train), len(train)) if train else None
    errors = [(n, str((F(value) - mean) ** 2)) for n, value in held] if mean is not None else []
    loss = str(sum((F(v) for n, v in errors), F(0)) / len(errors)) if errors else None
    return {'train_mean': str(mean) if mean is not None else None, 'errors': errors, 'mse': loss}

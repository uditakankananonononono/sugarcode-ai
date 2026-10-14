"""Row 1113, K-Fold Cross-Validation - Standard cross-validation.

kfold_mean assigns sorted-label rank modulo folds as each holdout fold.
Fit constant mean from training x and evaluate held-out y squared error.
Returns folds as (fold_index,held_labels,train_mean_or_None,mse_or_None) for
all folds in index order, means/MSE as Fraction strings. Empty training or
holdout gives None MSE. macro_mse averages only valid fold MSEs equally,
not by fold size, or None with none. No randomization or population guarantee.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
-10 to 10; bool and all subclasses are refused.
folds defaults to 3, an exact int from 2 to 5.
Validation order: rows type, rows size, folds, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: generalization guarantee, random folds, model adequacy, data provenance, production readiness.
"""

SCOPE = 'PARTIAL: cross-validates constant-mean predictions using deterministic label-rank folds'
NOT_CLAIMED = ('generalization guarantee', 'random folds', 'model adequacy', 'data provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def kfold_mean(rows, folds=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(folds) is not int or not 2 <= folds <= 5:
        raise ValueError('folds must be a nonbool integer between 2 and 5')
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
    results = []
    for fold in range(folds):
        train = [x for i, (n, x, y) in enumerate(nodes) if i % folds != fold]
        held = [(n, y) for i, (n, x, y) in enumerate(nodes) if i % folds == fold]
        mean = F(sum(train), len(train)) if train else None
        loss = sum(((F(y)-mean)**2 for n, y in held), F(0)) / len(held) if held and mean is not None else None
        results.append((fold, [n for n, y in held], str(mean) if mean is not None else None, str(loss) if loss is not None else None))
    valid = [F(r[3]) for r in results if r[3] is not None]
    return {'folds': results, 'macro_mse': str(sum(valid) / len(valid)) if valid else None}

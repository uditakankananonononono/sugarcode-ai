"""Row 1100, CatBoost - Categorical boosting.

ordered_target treats x as an integer category code and y as target. Process
caller order, encoding each category using only earlier rows of the same
category: (sum_previous_targets+prior)/(previous_count+1). Then update its
category statistics. Returns encoded as (label,Fraction string) in caller
order, category_counts as ascending category-code keys and total counts.
Own/future target values never affect a row's encoding. No CatBoost is trained.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
prior defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, prior, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: CatBoost training, generalization, permutation randomization, target validity, production readiness.
"""

SCOPE = 'PARTIAL: computes ordered smoothed target encodings for supplied category codes, no CatBoost model is trained'
NOT_CLAIMED = ('CatBoost training', 'generalization', 'permutation randomization', 'target validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ordered_target(rows, prior=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(prior) is not int or not 0 <= prior <= 10:
        raise ValueError('prior must be a nonbool integer between 0 and 10')
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
    from fractions import Fraction as F
    totals = {}
    counts = {}
    encoded = []
    for n, category, target in clean:
        value = F(totals.get(category, 0) + prior, counts.get(category, 0) + 1)
        encoded.append((n, str(value)))
        totals[category] = totals.get(category, 0) + target
        counts[category] = counts.get(category, 0) + 1
    return {'encoded': encoded, 'category_counts': dict(sorted(counts.items()))}

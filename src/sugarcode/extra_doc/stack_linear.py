"""Row 1102, Stacking - Meta-ensemble.

stack_linear applies a fixed supplied meta-rule weight*x+y to each pair
of base-model predictions. Returns values as (label,meta_score) sorted by
label, positive as sorted labels with meta_score strictly above zero,
disagreement as sorted labels where the two base predictions differ in
strict-positive classification. No meta-model training or cross-fitting occurs.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
-100 to 100; bool and all subclasses are refused.
weight defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, weight, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: meta-model fitting, cross-fit validity, generalization, prediction validity, production readiness.
"""

SCOPE = 'PARTIAL: applies a supplied two-model linear meta-rule to prediction pairs, no meta-learner is fitted'
NOT_CLAIMED = ('meta-model fitting', 'cross-fit validity', 'generalization', 'prediction validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def stack_linear(rows, weight=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(weight) is not int or not 0 <= weight <= 5:
        raise ValueError('weight must be a nonbool integer between 0 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not -100 <= x <= 100:
            raise ValueError('x must be a nonbool integer between -100 and 100')
        if type(y) is not int or not -100 <= y <= 100:
            raise ValueError('y must be a nonbool integer between -100 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    values = [(n, weight * x + y) for n, x, y in sorted(clean, key=lambda r: r[0])]
    return {'values': values, 'positive': [n for n, v in values if v > 0],
            'disagreement': sorted(n for n, x, y in clean if (x > 0) != (y > 0))}

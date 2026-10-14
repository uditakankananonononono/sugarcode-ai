"""Row 1098, XGBoost - Optimized gradient boosting.

xgb_leaf takes supplied nonnegative gradient sum x and Hessian sum y for
each leaf. With L2 regularizer compute optimal leaf weight -x/(y+regularizer)
and quadratic objective improvement x*x/(2*(y+regularizer)). Returns leaves
as (label,weight Fraction string), scores as (label,improvement Fraction
string), both sorted by label, gain as summed improvement Fraction string.
This is the leaf objective formula only, not XGBoost or tree training.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
regularizer defaults to 1, an exact int from 1 to 5.
Validation order: rows type, rows size, regularizer, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: XGBoost training, tree construction, generalization, gradient validity, production readiness.
"""

SCOPE = 'PARTIAL: computes independent regularized leaf weights from supplied gradient/Hessian sums'
NOT_CLAIMED = ('XGBoost training', 'tree construction', 'generalization', 'gradient validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def xgb_leaf(rows, regularizer=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(regularizer) is not int or not 1 <= regularizer <= 5:
        raise ValueError('regularizer must be a nonbool integer between 1 and 5')
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
    leaves = [(n, str(F(-gradient, hessian + regularizer)))
              for n, gradient, hessian in sorted(clean, key=lambda r: r[0])]
    scores = [(n, str(F(gradient * gradient, 2 * (hessian + regularizer))))
              for n, gradient, hessian in sorted(clean, key=lambda r: r[0])]
    return {'leaves': leaves, 'scores': scores, 'gain': str(sum((F(v) for n, v in scores), F(0)))}

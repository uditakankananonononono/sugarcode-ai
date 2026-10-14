"""Row 1097, Gradient Boosting - Sequential ensemble.

boost_residuals treats x as target and y as current prediction. Use the exact
residual x-y as a supplied learner output and learning rate 1/rate for one
squared-error update y+(x-y)/rate. Returns updates as (label,Fraction string)
sorted by label, loss_before and loss_after as summed squared-error Fraction
strings, improved as strict loss reduction. No learner is fitted or reused.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
-10 to 10; bool and all subclasses are refused.
rate defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, rate, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: learner fitting, full boosting ensemble, generalization, data provenance, production readiness.
"""

SCOPE = 'PARTIAL: applies a supplied residual learner once under squared-error loss'
NOT_CLAIMED = ('learner fitting', 'full boosting ensemble', 'generalization', 'data provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def boost_residuals(rows, rate=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(rate) is not int or not 1 <= rate <= 5:
        raise ValueError('rate must be a nonbool integer between 1 and 5')
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
    updates = [(n, F(prediction) + F(target - prediction, rate)) for n, target, prediction in sorted(clean, key=lambda r: r[0])]
    before = sum((target - prediction) ** 2 for n, target, prediction in clean)
    after = sum((F(target) - value) ** 2 for (n, target, prediction), (m, value) in zip(sorted(clean, key=lambda r: r[0]), updates))
    return {'updates': [(n, str(v)) for n, v in updates], 'loss_before': str(F(before)),
            'loss_after': str(after), 'improved': after < before}

"""Row 1109, Bayesian Model Selection - Select best model.

posterior_select treats x as prior mass and y as likelihood mass, repeated
power times. Unnormalized posterior is x*y**power. Returns scores as
(label,integer_mass) descending by mass then label, winner as first label,
posterior as normalized Fraction strings in the same rank order. This finite
supplied-mass model selector verifies neither the model nor its evidence.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
power defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, power, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: model truth, prior validity, likelihood validity, generalization, production readiness.
"""

SCOPE = 'PARTIAL: selects posterior mode from supplied prior and likelihood masses with integer likelihood power'
NOT_CLAIMED = ('model truth', 'prior validity', 'likelihood validity', 'generalization', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def posterior_select(rows, power=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(power) is not int or not 1 <= power <= 5:
        raise ValueError('power must be a nonbool integer between 1 and 5')
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
    scores = [(n, prior * likelihood ** power) for n, prior, likelihood in clean]
    scores.sort(key=lambda r: (-r[1], r[0]))
    total = sum(w for n, w in scores)
    return {'scores': scores, 'winner': scores[0][0],
            'posterior': [(n, str(F(w, total))) for n, w in scores]}

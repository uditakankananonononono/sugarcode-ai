"""Row 1103, Blending - Holdout ensemble.

holdout_blend treats x,y as two base models' supplied residuals on each
holdout row. For first-model weight i/grid, i=0..grid, blended residual is
(i*x+(grid-i)*y)/grid. Minimize sum squared blended residuals, lowest i on
ties. Returns losses as (i,Fraction string) in grid order, weight as winning
first-model Fraction string, loss as best loss Fraction string. It selects
a blend only from supplied holdout residuals, not a verified generalization model.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
-10 to 10; bool and all subclasses are refused.
grid defaults to 4, an exact int from 1 to 5.
Validation order: rows type, rows size, grid, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: unseen generalization, model training, holdout independence, residual validity, production readiness.
"""

SCOPE = 'PARTIAL: selects a two-model blend from supplied holdout residuals on a finite weight grid'
NOT_CLAIMED = ('unseen generalization', 'model training', 'holdout independence', 'residual validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def holdout_blend(rows, grid=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(grid) is not int or not 1 <= grid <= 5:
        raise ValueError('grid must be a nonbool integer between 1 and 5')
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
    losses = []
    for i in range(grid + 1):
        loss = sum((F(i * x + (grid - i) * y, grid) ** 2 for n, x, y in clean), F(0))
        losses.append((i, loss))
    winner = min(losses, key=lambda r: (r[1], r[0]))[0]
    return {'losses': [(i, str(v)) for i, v in losses],
            'weight': str(F(winner, grid)), 'loss': str(losses[winner][1])}

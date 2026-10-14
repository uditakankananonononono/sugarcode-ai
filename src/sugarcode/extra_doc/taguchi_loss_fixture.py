"""Row 1550, Taguchi Methods.

taguchi_loss_fixture multiplies squared supplied x,y count differences
by coefficient. Returns sorted losses, total, zero labels and coefficient.
No Taguchi optimization, orthogonal experiment design, physical loss
estimate, monetary estimate, statistical validation or engineering
certification is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
coefficient defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, coefficient, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: Taguchi optimization, experimental design, physical loss estimate, statistical validation, production readiness.
"""

SCOPE = 'PARTIAL: supplied paired count quadratic difference loss, no Taguchi optimization'
NOT_CLAIMED = ('Taguchi optimization', 'experimental design', 'physical loss estimate', 'statistical validation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def taguchi_loss_fixture(rows, coefficient=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(coefficient) is not int or not 1 <= coefficient <= 5:
        raise ValueError('coefficient must be a nonbool integer between 1 and 5')
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
    losses=sorted((n,coefficient*(x-y)**2) for n,x,y in clean)
    return {'losses':losses,'total':sum(v for n,v in losses),'zero':[n for n,v in losses if v==0],
            'coefficient':coefficient}

"""Row 1470, Dropout Prediction.

dropout_rule_fixture flags supplied missed count x exceeding completed
y by at least margin and strictly exceeding y even when margin zero.
Returns sorted flags, flagged labels, signed gaps and true count. No
actual dropout prediction, fitted probability model, learner diagnosis,
causal claim, student intervention or educational recommendation is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
margin defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, margin, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: dropout prediction, probability model, learner diagnosis, production readiness.
"""

SCOPE = 'PARTIAL: supplied missed/completed count rule flag, no dropout prediction'
NOT_CLAIMED = ('dropout prediction', 'probability model', 'learner diagnosis', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def dropout_rule_fixture(rows, margin=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(margin) is not int or not 0 <= margin <= 10:
        raise ValueError('margin must be a nonbool integer between 0 and 10')
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
    values=sorted((n,x-y>=margin and x>y) for n,x,y in clean)
    return {'flags':values,'flagged':[n for n,v in values if v],
            'gaps':sorted((n,x-y) for n,x,y in clean),'count':sum(v for n,v in values)}

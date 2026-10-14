"""Row 1403, Prospect Theory.

prospect_linear_fixture compares supplied outcome x with reference y.
Nonnegative count difference is unchanged; negative difference is multiplied
by loss_weight. Returns sorted scores, losses, total and nonnegative labels.
No full prospect-theory model, nonlinear utility, probability weighting,
behavioral prediction, fitted preferences or financial advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
loss_weight defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, loss_weight, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: prospect theory model, probability weighting, behavioral prediction, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied piecewise gain/loss count score, no prospect-theory model'
NOT_CLAIMED = ('prospect theory model', 'probability weighting', 'behavioral prediction', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def prospect_linear_fixture(rows, loss_weight=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(loss_weight) is not int or not 1 <= loss_weight <= 5:
        raise ValueError('loss_weight must be a nonbool integer between 1 and 5')
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
    values=sorted((n,x-y if x>=y else loss_weight*(x-y)) for n,x,y in clean)
    return {'scores':values,'losses':[n for n,v in values if v<0],'total':sum(v for n,v in values),
            'nonnegative':[n for n,v in values if v>=0]}

"""Row 1540, Design for Six Sigma.

six_sigma_deviation_fixture sums squared distances of supplied x,y counts
from target. Returns sorted squared_deviations, total, on_target zero
labels and target. This is an abstract deviation fixture, not Six Sigma
design assessment, process capability, statistical inference, actual
quality validation or engineering certification.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
target defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: Six Sigma design assessment, process capability, statistical inference, engineering certification, production readiness.
"""

SCOPE = 'PARTIAL: supplied target coordinate squared deviation, no Six Sigma design assessment'
NOT_CLAIMED = ('Six Sigma design assessment', 'process capability', 'statistical inference', 'engineering certification', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def six_sigma_deviation_fixture(rows, target=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(target) is not int or not 0 <= target <= 10:
        raise ValueError('target must be a nonbool integer between 0 and 10')
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
    values=sorted((n,(x-target)**2+(y-target)**2) for n,x,y in clean)
    return {'squared_deviations':values,'total':sum(v for n,v in values),
            'on_target':[n for n,v in values if v==0],'target':target}

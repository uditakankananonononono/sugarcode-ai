"""Row 1482, Performance Assessment.

performance_cap_fixture assigns three points per supplied accuracy
count x and subtracts penalty times time count y, floors at zero. Returns
sorted scores, positive, total and penalty. Counts are abstract and do not
measure actual accuracy or speed. No performance assessment, skill
validation, grading validity or learner evaluation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
penalty defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, penalty, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: performance assessment, skill validation, grading validity, production readiness.
"""

SCOPE = 'PARTIAL: supplied accuracy/time count penalty score, no performance assessment'
NOT_CLAIMED = ('performance assessment', 'skill validation', 'grading validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def performance_cap_fixture(rows, penalty=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(penalty) is not int or not 0 <= penalty <= 5:
        raise ValueError('penalty must be a nonbool integer between 0 and 5')
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
    values=sorted((n,max(3*x-penalty*y,0)) for n,x,y in clean)
    return {'scores':values,'positive':[n for n,v in values if v>0],
            'total':sum(v for n,v in values),'penalty':penalty}

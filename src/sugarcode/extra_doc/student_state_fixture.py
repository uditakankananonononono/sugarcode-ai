"""Row 1466, Student Modeling.

student_state_fixture partitions supplied attempt x and correct y counts
as unobserved at zero attempts, threshold if capped correct share meets
percent, below otherwise. Returns sorted states, threshold and unobserved
labels, observed row count. States are abstract count flags, not real
student models, learner diagnosis, mastery estimation or recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 80, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: student model, learner diagnosis, mastery estimation, production readiness.
"""

SCOPE = 'PARTIAL: supplied attempt/correct count state partition, no student model'
NOT_CLAIMED = ('student model', 'learner diagnosis', 'mastery estimation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def student_state_fixture(rows, percent=80):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 0 and 100')
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
    values=sorted((n,'unobserved' if x==0 else 'threshold' if 100*min(x,y)>=percent*x else 'below') for n,x,y in clean)
    return {'states':values,'threshold':[n for n,s in values if s=='threshold'],
            'unobserved':[n for n,s in values if s=='unobserved'],'observed':sum(x>0 for n,x,y in clean)}

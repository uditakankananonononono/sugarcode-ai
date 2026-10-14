"""Row 1499, Intelligent Tutoring Systems.

its_hintlevel_fixture assigns zero hint level at zero supplied error y,
level two if positive errors meet error_threshold and supplied attempt x
count is at least two, level one otherwise. Returns sorted hint_levels,
high level-two labels, none zero labels and total level counts. No intelligent
tutoring system, learner modeling, hint generation or pedagogical validation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
error_threshold defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, error_threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: intelligent tutoring system, learner modeling, hint generation, production readiness.
"""

SCOPE = 'PARTIAL: supplied attempt/error count hint-level policy, no intelligent tutoring system'
NOT_CLAIMED = ('intelligent tutoring system', 'learner modeling', 'hint generation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def its_hintlevel_fixture(rows, error_threshold=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(error_threshold) is not int or not 0 <= error_threshold <= 10:
        raise ValueError('error_threshold must be a nonbool integer between 0 and 10')
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
    values=sorted((n,0 if y==0 else 2 if y>=error_threshold and x>=2 else 1) for n,x,y in clean)
    return {'hint_levels':values,'high':[n for n,l in values if l==2],
            'none':[n for n,l in values if l==0],'total':sum(l for n,l in values)}

"""Row 1512, Inclusive Education.

inclusive_access_fixture compares supplied requested count x plus buffer
against available count y, recording gaps and spare counts. Returns sorted
access (label,gap,spare), covered zero-gap labels, gap and spare totals.
No inclusion certification, learner needs inference, accommodation choice,
accessibility judgment or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
buffer defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, buffer, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: inclusion certification, learner needs inference, accessibility judgment, production readiness.
"""

SCOPE = 'PARTIAL: supplied access/request count buffer gaps, no inclusion certification'
NOT_CLAIMED = ('inclusion certification', 'learner needs inference', 'accessibility judgment', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def inclusive_access_fixture(rows, buffer=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(buffer) is not int or not 0 <= buffer <= 5:
        raise ValueError('buffer must be a nonbool integer between 0 and 5')
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
    values=sorted((n,max(x+buffer-y,0),max(y-x-buffer,0)) for n,x,y in clean)
    return {'access':values,'covered':[n for n,g,s in values if g==0],
            'gap':sum(g for n,g,s in values),'spare':sum(s for n,g,s in values)}

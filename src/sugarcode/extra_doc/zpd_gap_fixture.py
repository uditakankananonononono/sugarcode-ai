"""Row 1437, Zone of Proximal Development.

zpd_gap_fixture subtracts supplied current count y from task count x and
partitions gaps into independent nonpositive, supported positive at most
support and beyond above support. Returns sorted gaps and the three sorted
label lists. No real ZPD assessment, learner diagnosis, skill measurement,
task suitability or pedagogical recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
support defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, support, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: ZPD assessment, learner diagnosis, task suitability, production readiness.
"""

SCOPE = 'PARTIAL: supplied task/current count support-window screen, no ZPD assessment'
NOT_CLAIMED = ('ZPD assessment', 'learner diagnosis', 'task suitability', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def zpd_gap_fixture(rows, support=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(support) is not int or not 0 <= support <= 10:
        raise ValueError('support must be a nonbool integer between 0 and 10')
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
    values=sorted((n,x-y) for n,x,y in clean)
    return {'gaps':values,'supported':[n for n,v in values if 0<v<=support],
            'independent':[n for n,v in values if v<=0],'beyond':[n for n,v in values if v>support]}

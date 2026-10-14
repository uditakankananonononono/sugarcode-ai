"""Row 1447, Cooperative Learning.

cooperative_pair_fixture assigns supplied task count y plus extra_tasks
round-robin over supplied participant count x; earlier indices get remainder.
Returns sorted loads (label,list or None for zero participants), unassigned
task total for zero-participant rows and groups with participants. No
cooperative pedagogy, role content, group dynamics assessment or learning
outcome validation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
extra_tasks defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, extra_tasks, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: cooperative pedagogy, group dynamics assessment, learning outcome validation, production readiness.
"""

SCOPE = 'PARTIAL: supplied participant/task count round-robin load, no cooperative pedagogy'
NOT_CLAIMED = ('cooperative pedagogy', 'group dynamics assessment', 'learning outcome validation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def cooperative_pair_fixture(rows, extra_tasks=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(extra_tasks) is not int or not 0 <= extra_tasks <= 5:
        raise ValueError('extra_tasks must be a nonbool integer between 0 and 5')
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
    values=[]
    for n,people,tasks in sorted(clean,key=lambda r:r[0]):
        if people:
            q,r=divmod(tasks+extra_tasks,people); loads=[q+(i<r) for i in range(people)]
        else: loads=None
        values.append((n,loads))
    return {'loads':values,'unassigned':sum(y+extra_tasks for n,x,y in clean if x==0),
            'groups':sum(x>0 for n,x,y in clean)}

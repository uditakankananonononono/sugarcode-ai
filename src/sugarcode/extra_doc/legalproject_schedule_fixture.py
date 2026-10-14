"""Row 1314, Legal Project Management.

legalproject_schedule_fixture serializes abstract task duration of nonnegative x minus y
in label order from start. Returns tasks (label,start_index,end_index), end,
elapsed and zero-duration labels. No real deadline, legal readiness, calendar,
project commitment or external legal work is planned or executed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
start defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, start, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal project management, real deadlines, legal readiness, external execution, production readiness.
"""

SCOPE = 'PARTIAL: expands abstract supplied task counts, no legal project management'
NOT_CLAIMED = ('legal project management', 'real deadlines', 'legal readiness', 'external execution', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def legalproject_schedule_fixture(rows, start=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(start) is not int or not 0 <= start <= 10:
        raise ValueError('start must be a nonbool integer between 0 and 10')
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
    tasks=[]
    cursor=start
    for n,x,y in sorted(clean,key=lambda r:r[0]):
        duration=max(0,x-y)
        tasks.append((n,cursor,cursor+duration))
        cursor+=duration
    return {'tasks':tasks,'end':cursor,'elapsed':cursor-start,'zero':[n for n,a,b in tasks if a==b]}

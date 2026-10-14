"""Row 1501, Socratic Tutoring.

socratic_depth_fixture adds supplied starting depth x and question count
y, caps at max_depth and records overflow. Returns sorted depths
(label,capped_depth,overflow), at_cap including equality, overflow total and
total_depth. No Socratic tutoring, semantic questioning, reasoning quality,
actual conversation, learning effectiveness or recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
max_depth defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, max_depth, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: Socratic tutoring, semantic reasoning, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied question/depth count progression budget, no Socratic tutoring'
NOT_CLAIMED = ('Socratic tutoring', 'semantic reasoning', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def socratic_depth_fixture(rows, max_depth=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(max_depth) is not int or not 0 <= max_depth <= 10:
        raise ValueError('max_depth must be a nonbool integer between 0 and 10')
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
    values=sorted((n,min(x+y,max_depth),max(x+y-max_depth,0)) for n,x,y in clean)
    return {'depths':values,'at_cap':[n for n,d,o in values if d==max_depth],
            'overflow':sum(o for n,d,o in values),'total_depth':sum(d for n,d,o in values)}

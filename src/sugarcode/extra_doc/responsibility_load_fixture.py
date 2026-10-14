"""Row 1298, Professional Responsibility.

responsibility_load_fixture sums abstract paired duty-count tokens.
Returns sorted loads, over labels strictly beyond capacity, nonnegative spare
counts and total. No attorney duty, competence, conduct rule, professional
responsibility or misconduct is interpreted or assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
capacity defaults to 5, an exact int from 0 to 20.
Validation order: rows type, rows size, capacity, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: professional responsibility, legal duties, misconduct, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied duty count loads, no professional responsibility assessment'
NOT_CLAIMED = ('professional responsibility', 'legal duties', 'misconduct', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def responsibility_load_fixture(rows, capacity=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(capacity) is not int or not 0 <= capacity <= 20:
        raise ValueError('capacity must be a nonbool integer between 0 and 20')
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
    loads=[(n,x+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'loads':loads,'over':[n for n,v in loads if v>capacity],
            'spare':[(n,max(0,capacity-v)) for n,v in loads],'total':sum(v for n,v in loads)}

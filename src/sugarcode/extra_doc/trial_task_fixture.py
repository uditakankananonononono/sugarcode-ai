"""Row 1288, Trial Preparation.

trial_task_fixture adds extra to abstract required x and subtracts completed
y, flooring deficit at zero. Returns deficits descending then label, pending
positive labels, complete zero labels and total. No legal preparation,
evidence validity, readiness, court rules or trial strategy is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
extra defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, extra, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: trial preparation, legal readiness, evidence validity, case strategy, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied preparation tallies, no trial preparation'
NOT_CLAIMED = ('trial preparation', 'legal readiness', 'evidence validity', 'case strategy', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def trial_task_fixture(rows, extra=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(extra) is not int or not 0 <= extra <= 10:
        raise ValueError('extra must be a nonbool integer between 0 and 10')
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
    deficits=[(n,max(0,x+extra-y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    deficits.sort(key=lambda r:(-r[1],r[0]))
    return {'deficits':deficits,'pending':[n for n,v in deficits if v>0],
            'complete':[n for n,v in deficits if v==0],'total':sum(v for n,v in deficits)}

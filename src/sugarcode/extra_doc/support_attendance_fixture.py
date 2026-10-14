"""Row 1199, Substance Abuse Treatment.

support_attendance_fixture compares abstract planned x and completed y
session tallies, floors remaining at zero and compares with caller quota.
Returns sorted remaining, within_quota labels, total remaining and excess_done
labels with completed greater than planned. No treatment, recovery progress,
substance use, real session needs or clinical safety is evaluated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
quota defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, quota, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: substance abuse treatment, clinical advice, treatment effectiveness, diagnosis or safety, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied session tallies, no substance abuse treatment'
NOT_CLAIMED = ('substance abuse treatment', 'clinical advice', 'treatment effectiveness', 'diagnosis or safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def support_attendance_fixture(rows, quota=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(quota) is not int or not 0 <= quota <= 10:
        raise ValueError('quota must be a nonbool integer between 0 and 10')
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
    balances=[(n,max(0,x-y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'remaining':balances,'within_quota':[n for n,v in balances if v<=quota],
            'total':sum(v for n,v in balances),'excess_done':sorted(n for n,x,y in clean if y>x)}

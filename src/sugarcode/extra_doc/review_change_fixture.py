"""Row 1277, Judicial Review.

review_change_fixture subtracts abstract original x from reviewed y counts.
Returns sorted changes, over labels strictly beyond absolute threshold,
unchanged zero labels and sum. No judicial standard, decision, legal reasoning
or case outcome is read, interpreted or predicted.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
threshold defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: judicial review, legal standard, court reasoning, case outcome, production readiness.
"""

SCOPE = 'PARTIAL: compares abstract supplied review count changes, no judicial review'
NOT_CLAIMED = ('judicial review', 'legal standard', 'court reasoning', 'case outcome', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def review_change_fixture(rows, threshold=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 0 <= threshold <= 10:
        raise ValueError('threshold must be a nonbool integer between 0 and 10')
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
    changes=[(n,y-x) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'changes':changes,'over':[n for n,v in changes if abs(v)>threshold],
            'unchanged':[n for n,v in changes if v==0],'sum':sum(v for n,v in changes)}

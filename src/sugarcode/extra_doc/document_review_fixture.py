"""Row 1309, Document Review.

document_review_fixture subtracts abstract reviewed y from document count x,
floors at zero and compares to quota. Returns sorted pending, within labels
at most quota, over strictly beyond and total. No documents are read, content
understood, privilege/relevance or legal accuracy assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
quota defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, quota, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: document review, content understanding, relevance or privilege, legal accuracy, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied review shortfalls, no document review'
NOT_CLAIMED = ('document review', 'content understanding', 'relevance or privilege', 'legal accuracy', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def document_review_fixture(rows, quota=3):
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
    pending=[(n,max(0,x-y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'pending':pending,'within':[n for n,v in pending if v<=quota],
            'over':[n for n,v in pending if v>quota],'total':sum(v for n,v in pending)}

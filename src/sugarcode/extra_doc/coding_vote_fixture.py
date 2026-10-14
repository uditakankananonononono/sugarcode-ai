"""Row 1308, Predictive Coding.

coding_vote_fixture thresholds abstract supplied positive yes x and no y
count shares. Returns sorted votes Fraction strings, selected labels at least
percent/100 and other labels. No documents, relevance, privilege, training,
learned classifier or actual predictive coding is performed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
percent defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: predictive coding, document relevance, learned model, legal privilege, production readiness.
"""

SCOPE = 'PARTIAL: thresholds abstract supplied paired vote counts, no predictive coding'
NOT_CLAIMED = ('predictive coding', 'document relevance', 'learned model', 'legal privilege', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def coding_vote_fixture(rows, percent=50):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 0 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    votes=[(n,F(x,x+y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'votes':[(n,str(v)) for n,v in votes],'selected':[n for n,v in votes if 100*v>=percent],
            'other':[n for n,v in votes if 100*v<percent]}

"""Row 1227, Corporate Governance.

governance_vote_fixture sums supplied abstract yes x and no y counts.
Returns sorted totals, reached labels at least quorum, winning labels with
strict yes majority and reached quorum, tied equal-count labels. No voting
rights, corporate law, quorum validity or board action is determined.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
quorum defaults to 5, an exact int from 0 to 20.
Validation order: rows type, rows size, quorum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: corporate governance, valid voting rights, legal quorum, board action, production readiness.
"""

SCOPE = 'PARTIAL: counts abstract supplied vote pairs, no corporate governance advice'
NOT_CLAIMED = ('corporate governance', 'valid voting rights', 'legal quorum', 'board action', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def governance_vote_fixture(rows, quorum=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(quorum) is not int or not 0 <= quorum <= 20:
        raise ValueError('quorum must be a nonbool integer between 0 and 20')
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
    totals=[(n,x+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    reached=[n for n,v in totals if v>=quorum]
    winning=sorted(n for n,x,y in clean if x>y and x+y>=quorum)
    return {'totals':totals,'reached':reached,'winning':winning,
            'tied':sorted(n for n,x,y in clean if x==y)}

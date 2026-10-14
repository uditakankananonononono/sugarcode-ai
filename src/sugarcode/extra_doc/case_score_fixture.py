"""Row 1221, Case Law Analysis.

case_score_fixture subtracts penalty times supplied abstract conflict y from
support x. Returns scores descending then label, one-based rank (label,rank)
and nonnegative labels. No case content, binding precedent or authority is
interpreted, fetched or assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
penalty defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, penalty, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: case law analysis, precedential authority, legal interpretation, case retrieval, production readiness.
"""

SCOPE = 'PARTIAL: ranks abstract supplied citation tallies, no case law analysis'
NOT_CLAIMED = ('case law analysis', 'precedential authority', 'legal interpretation', 'case retrieval', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def case_score_fixture(rows, penalty=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(penalty) is not int or not 0 <= penalty <= 5:
        raise ValueError('penalty must be a nonbool integer between 0 and 5')
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
    scores=[(n,x-penalty*y) for n,x,y in clean]
    scores.sort(key=lambda r:(-r[1],r[0]))
    return {'scores':scores,'rank':[(n,i+1) for i,(n,v) in enumerate(scores)],
            'nonnegative':[n for n,v in scores if v>=0]}

"""Row 1473, Content Recommendation.

content_fit_fixture ranks supplied topic score x and difficulty count y
by absolute distance from target ascending, score descending, label ascending.
Returns ranked (label,distance,score), exact zero-distance labels in rank
order and best first label. No semantic relevance, actual content retrieval,
content recommendation model or learner needs inference is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
target defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: content recommendation model, semantic relevance, learner needs inference, production readiness.
"""

SCOPE = 'PARTIAL: supplied topic/difficulty count target-distance rank, no content recommendation model'
NOT_CLAIMED = ('content recommendation model', 'semantic relevance', 'learner needs inference', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def content_fit_fixture(rows, target=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(target) is not int or not 0 <= target <= 10:
        raise ValueError('target must be a nonbool integer between 0 and 10')
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
    ranked=sorted(clean,key=lambda r:(abs(r[2]-target),-r[1],r[0]))
    values=[(n,abs(y-target),x) for n,x,y in ranked]
    return {'ranked':values,'exact':[n for n,d,s in values if d==0],'best':values[0][0]}

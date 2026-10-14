"""Row 1457, Game-Based Learning.

gamelearning_attempt_fixture scores supplied completed level count x as
ten counts each less penalty times attempt count y, floored at zero.
Returns sorted scores, zero labels, total and best. Counts do not verify
levels or skill. No game-based pedagogy, game generation, learning
effectiveness, learner assessment or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
penalty defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, penalty, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: game based pedagogy, game generation, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied level-attempt count scoring with fixed penalty, no game-based pedagogy'
NOT_CLAIMED = ('game based pedagogy', 'game generation', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def gamelearning_attempt_fixture(rows, penalty=2):
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
    values=sorted((n,max(10*x-penalty*y,0)) for n,x,y in clean)
    return {'scores':values,'zero':[n for n,v in values if v==0],
            'total':sum(v for n,v in values),'best':max(v for n,v in values)}

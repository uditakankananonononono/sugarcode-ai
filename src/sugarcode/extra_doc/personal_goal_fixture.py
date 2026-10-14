"""Row 1433, Personalized Learning.

personal_goal_fixture subtracts supplied completed count y from goal
count x, floors at zero and multiplies gap by practice_per_gap. Returns
sorted plans (label,gap,practice_count), complete zero-gap labels and
practice/gaps totals. No actual personalized learning model, learner
diagnosis, skill validation, content selection or pedagogical recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
practice_per_gap defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, practice_per_gap, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: personalized learning model, learner diagnosis, pedagogical recommendation, production readiness.
"""

SCOPE = 'PARTIAL: supplied individual goal/completion count gap budgets, no personalized learning model'
NOT_CLAIMED = ('personalized learning model', 'learner diagnosis', 'pedagogical recommendation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def personal_goal_fixture(rows, practice_per_gap=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(practice_per_gap) is not int or not 1 <= practice_per_gap <= 5:
        raise ValueError('practice_per_gap must be a nonbool integer between 1 and 5')
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
    values=sorted((n,max(x-y,0),practice_per_gap*max(x-y,0)) for n,x,y in clean)
    return {'plans':values,'complete':[n for n,g,p in values if g==0],
            'practice':sum(p for n,g,p in values),'gaps':sum(g for n,g,p in values)}

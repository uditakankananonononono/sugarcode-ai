"""Row 1458, Gamification.

gamification_badge_fixture scores supplied activity x plus twice supplied
streak y counts and divides points into complete points_per_badge badges.
Returns sorted rewards (label,points,badges,remainder), badges total,
next_needed to the next badge including a full threshold at exact multiples,
and points total. No motivation inference, game design, gamification
efficacy, behavior validation or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
points_per_badge defaults to 5, an exact int from 1 to 10.
Validation order: rows type, rows size, points_per_badge, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: gamification efficacy, motivation inference, game design, production readiness.
"""

SCOPE = 'PARTIAL: supplied activity/streak count badge thresholds, no gamification efficacy claim'
NOT_CLAIMED = ('gamification efficacy', 'motivation inference', 'game design', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def gamification_badge_fixture(rows, points_per_badge=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(points_per_badge) is not int or not 1 <= points_per_badge <= 10:
        raise ValueError('points_per_badge must be a nonbool integer between 1 and 10')
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
    values=sorted((n,x+2*y,(x+2*y)//points_per_badge,(x+2*y)%points_per_badge) for n,x,y in clean)
    return {'rewards':values,'badges':sum(b for n,p,b,r in values),
            'next_needed':[(n,points_per_badge-r) for n,p,b,r in values],'points':sum(p for n,p,b,r in values)}

"""Row 761, Perspective Taking: tallying supplied stances by viewer.

Sees from other views by counting. Each row pairs a viewer name of 1
to 8 characters with a stance of 'for', 'neutral', or 'against', and
each viewer appears at most once. Reported: the three stance counts,
the majority stance (the one held by more than half the viewers, or
None when no stance holds a majority), and the viewer count.
Caps (checked before any work): 0 to 100 rows.
NOT_CLAIMED: real empathy, opinion polling, cognitive modeling,
negotiation, sentiment analysis, belief tracking, production readiness.
"""
SCOPE = 'PARTIAL: stance tallying over supplied rows, no real perspective taking'
NOT_CLAIMED = ('real empathy', 'opinion polling', 'cognitive modeling',
               'negotiation', 'sentiment analysis', 'belief tracking',
               'production readiness')

MAX_ROWS = 100
MAX_VIEWER = 8
STANCES = ('for', 'neutral', 'against')


def gather(views):
    if type(views) not in (list, tuple):
        raise TypeError('views must be a list or tuple')
    if len(views) > MAX_ROWS:
        raise ValueError('views must contain at most 100 rows')
    rows = []
    for row in views:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each view must be a (viewer, stance) row')
        viewer, stance = row
        if type(viewer) is not str or not 1 <= len(viewer) <= MAX_VIEWER:
            raise ValueError('viewer must be a string of 1 to 8 characters')
        if type(stance) is not str or stance not in STANCES:
            raise ValueError('stance must be for, neutral, or against')
        rows.append((viewer, stance))
    seen = set()
    for viewer, stance in rows:
        if viewer in seen:
            raise ValueError('each viewer may appear only once')
        seen.add(viewer)
    counts = {'for': 0, 'neutral': 0, 'against': 0}
    for viewer, stance in rows:
        counts[stance] += 1
    total = len(rows)
    majority = None
    for stance in STANCES:
        if counts[stance] * 2 > total:
            majority = stance
    return {'for': counts['for'], 'neutral': counts['neutral'],
            'against': counts['against'], 'majority': majority, 'total': total}

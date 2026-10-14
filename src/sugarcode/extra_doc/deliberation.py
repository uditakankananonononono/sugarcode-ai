"""Row 746, Deliberation: weighing supplied points for and against.

Discusses thoughtfully by totaling. Each row pairs a side of 'for' or
'against' with an integer weight from 1 to 10. Reported: the two side
totals, the balance (for minus against), the leaning ('for',
'against', or 'even' when the totals match), and the row count.
Caps (checked before any work): 0 to 100 rows.
NOT_CLAIMED: real judgment, discussion quality, facilitation,
decisions, argument mapping, truth, production readiness.
"""
SCOPE = 'PARTIAL: weight totaling over supplied rows, no real deliberation'
NOT_CLAIMED = ('real judgment', 'discussion quality', 'facilitation', 'decisions',
               'argument mapping', 'truth', 'production readiness')

MAX_ROWS = 100
MAX_WEIGHT = 10
SIDES = ('for', 'against')


def weigh(points):
    if type(points) not in (list, tuple):
        raise TypeError('points must be a list or tuple')
    if len(points) > MAX_ROWS:
        raise ValueError('points must contain at most 100 rows')
    rows = []
    for row in points:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each point must be a (side, weight) row')
        side, weight = row
        if type(side) is not str or side not in SIDES:
            raise ValueError('side must be for or against')
        if type(weight) is not int or not 1 <= weight <= MAX_WEIGHT:
            raise ValueError('weight must be an integer from 1 to 10')
        rows.append((side, weight))
    totals = {'for': 0, 'against': 0}
    for side, weight in rows:
        totals[side] += weight
    balance = totals['for'] - totals['against']
    leaning = 'for' if balance > 0 else 'against' if balance < 0 else 'even'
    return {'for': totals['for'], 'against': totals['against'],
            'balance': balance, 'leaning': leaning, 'rows': len(rows)}

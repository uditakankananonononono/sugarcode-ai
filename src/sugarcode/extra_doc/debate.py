"""Row 747, Debate: scoring alternating supplied rounds.

Argues positions by totaling. Each round pairs a side with an integer
score from 0 to 5, and the sides must alternate starting with 'pro'
(pro, con, pro, ...). Reported: the two side totals, the winner
('pro', 'con', or 'draw' when the totals match), and the round count.
Caps (checked before any work): 0 to 50 rounds.
NOT_CLAIMED: real debating, argument quality, judging, rebuttals,
timing, persuasion, production readiness.
"""
SCOPE = 'PARTIAL: round scoring over supplied rows, no real debate'
NOT_CLAIMED = ('real debating', 'argument quality', 'judging', 'rebuttals',
               'timing', 'persuasion', 'production readiness')

MAX_ROUNDS = 50
MAX_SCORE = 5
SIDES = ('pro', 'con')


def score(rounds):
    if type(rounds) not in (list, tuple):
        raise TypeError('rounds must be a list or tuple')
    if len(rounds) > MAX_ROUNDS:
        raise ValueError('rounds must contain at most 50 rows')
    rows = []
    for row in rounds:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each round must be a (side, points) row')
        side, points = row
        if type(side) is not str or side not in SIDES:
            raise ValueError('side must be pro or con')
        if type(points) is not int or not 0 <= points <= MAX_SCORE:
            raise ValueError('points must be an integer from 0 to 5')
        rows.append((side, points))
    for index, (side, points) in enumerate(rows):
        if side != ('pro' if index % 2 == 0 else 'con'):
            raise ValueError('sides must alternate starting with pro')
    totals = {'pro': 0, 'con': 0}
    for side, points in rows:
        totals[side] += points
    if totals['pro'] > totals['con']:
        winner = 'pro'
    elif totals['pro'] < totals['con']:
        winner = 'con'
    else:
        winner = 'draw'
    return {'pro': totals['pro'], 'con': totals['con'],
            'winner': winner, 'rounds': len(rows)}

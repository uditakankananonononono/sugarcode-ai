"""Row 742, Facilitation: measuring speaker balance in supplied turns.

Guides group process by counting. Each turn is a speaker name, a
string of 1 to 8 characters. Reported: the (speaker, count) pairs
sorted by speaker, the total turn count, and max_share_per_mille -
the largest single speaker's share of the turns per thousand,
computed with integer arithmetic, and 0 when there are no turns.
Caps (checked before any work): 0 to 100 turns.
NOT_CLAIMED: real meetings, group dynamics, intervention, agenda
design, sentiment, time tracking, production readiness.
"""
SCOPE = 'PARTIAL: speaker turn counting over supplied names, no real facilitation'
NOT_CLAIMED = ('real meetings', 'group dynamics', 'intervention', 'agenda design',
               'sentiment', 'time tracking', 'production readiness')

MAX_TURNS = 100
MAX_NAME = 8


def review(turns):
    if type(turns) not in (list, tuple):
        raise TypeError('turns must be a list or tuple')
    if len(turns) > MAX_TURNS:
        raise ValueError('turns must contain at most 100 rows')
    for turn in turns:
        if type(turn) is not str or not 1 <= len(turn) <= MAX_NAME:
            raise ValueError('turns must be speaker names of 1 to 8 characters')
    counts = {}
    for turn in turns:
        counts[turn] = counts.get(turn, 0) + 1
    total = len(turns)
    top = max(counts.values()) if counts else 0
    return {'turns': sorted(counts.items()), 'total': total,
            'max_share_per_mille': top * 1000 // total if total else 0}

"""Row 744, Consensus Building: judging agreement from supplied positions.

Finds agreement by counting. Each row pairs a member name of 1 to 8
characters with a position of 'support', 'accept', or 'block', and each
member appears at most once. Reported: the three position counts, the
row total, and consensus - true when nobody blocks and at least one
member supports. Caps (checked before any work): 0 to 100 rows.
NOT_CLAIMED: real decisions, group dynamics, facilitation, negotiation,
voting, conflict resolution, production readiness.
"""
SCOPE = 'PARTIAL: position counting over supplied rows, no real consensus process'
NOT_CLAIMED = ('real decisions', 'group dynamics', 'facilitation', 'negotiation',
               'voting', 'conflict resolution', 'production readiness')

MAX_ROWS = 100
MAX_MEMBER = 8
POSITIONS = ('support', 'accept', 'block')


def assess(votes):
    if type(votes) not in (list, tuple):
        raise TypeError('votes must be a list or tuple')
    if len(votes) > MAX_ROWS:
        raise ValueError('votes must contain at most 100 rows')
    rows = []
    for row in votes:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each vote must be a (member, position) row')
        member, position = row
        if type(member) is not str or not 1 <= len(member) <= MAX_MEMBER:
            raise ValueError('member must be a string of 1 to 8 characters')
        if type(position) is not str or position not in POSITIONS:
            raise ValueError('position must be support, accept, or block')
        rows.append((member, position))
    seen = set()
    for member, position in rows:
        if member in seen:
            raise ValueError('each member may vote only once')
        seen.add(member)
    counts = {'support': 0, 'accept': 0, 'block': 0}
    for member, position in rows:
        counts[position] += 1
    return {'support': counts['support'], 'accept': counts['accept'],
            'block': counts['block'],
            'consensus': counts['block'] == 0 and counts['support'] >= 1,
            'total': len(rows)}

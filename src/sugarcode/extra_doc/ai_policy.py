"""Row 1956, Title: AI Policy

count_anchors(rows): rows are (policy, pillar, score)
triples; policy and pillar strings of 1 to 16
characters; score a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each policy its
anchors (pillars scored by that policy alone), the
total anchors, the shared pillars (scored by more
than one policy, sorted alphabetically), and the
leader (the most anchors, first supplied on ties,
or None when no pillar is anchored).

SCOPE: PARTIAL: anchor counting over supplied scores
NOT_CLAIMED: pillar weighting, stakeholder mapping,
lobbying analysis, legislative forecasting,
production readiness.
"""

SCOPE = 'PARTIAL: anchor counting over supplied scores'
NOT_CLAIMED = ('pillar weighting', 'stakeholder mapping',
               'lobbying analysis', 'legislative forecasting',
               'production readiness')


def count_anchors(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (policy, pillar, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        policy, pillar, score = row
        if type(policy) is not str or not 1 <= len(policy) <= 16:
            raise ValueError(f'row {i}: policy must be a string of 1 to 16 characters')
        if type(pillar) is not str or not 1 <= len(pillar) <= 16:
            raise ValueError(f'row {i}: pillar must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    holders = {}
    order = {}
    for policy, pillar, score in rows:
        if pillar not in holders:
            holders[pillar] = {}
        if policy not in order:
            order[policy] = True
        holders[pillar][policy] = True
    anchors = {}
    shared = []
    count = 0
    for pillar in holders:
        if len(holders[pillar]) == 1:
            for policy in holders[pillar]:
                if policy not in anchors:
                    anchors[policy] = 0
                anchors[policy] += 1
                count += 1
        else:
            shared.append(pillar)
    leader = None
    for policy in order:
        if policy not in anchors:
            continue
        if leader is None or anchors[policy] > anchors[leader]:
            leader = policy
    return {'total': len(rows),
            'anchors': anchors,
            'count': count,
            'shared': sorted(shared),
            'leader': leader}

"""Row 1946, Title: AI Alignment

count_corrections(rows): rows are (goal, agent, drift)
triples; goal and agent strings of 1 to 16 characters;
drift a nonbool integer between 1 and 9. Caps (checked
before any work): 1 to 60 rows. Reported: the total row
count, for each agent its corrections (a drift of 1
while the agent has a raised flag; a drift above 1
raises the flag), the pending agents (flag still
raised at the end, sorted alphabetically), and the
leader (the most corrections, first supplied on ties,
or None when no agent corrects).

SCOPE: PARTIAL: correction counting over supplied drift
NOT_CLAIMED: goal specification, reward hacking,
interpretability, debate protocols, production
readiness.
"""

SCOPE = 'PARTIAL: correction counting over supplied drift'
NOT_CLAIMED = ('goal specification', 'reward hacking',
               'interpretability', 'debate protocols',
               'production readiness')


def count_corrections(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (goal, agent, drift) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        goal, agent, drift = row
        if type(goal) is not str or not 1 <= len(goal) <= 16:
            raise ValueError(f'row {i}: goal must be a string of 1 to 16 characters')
        if type(agent) is not str or not 1 <= len(agent) <= 16:
            raise ValueError(f'row {i}: agent must be a string of 1 to 16 characters')
        if type(drift) is not int or not 1 <= drift <= 9:
            raise ValueError(f'row {i}: drift must be a nonbool integer between 1 and 9')
    raised = {}
    order = {}
    corrections = {}
    for goal, agent, drift in rows:
        if agent not in order:
            order[agent] = True
        if agent not in raised:
            raised[agent] = False
        if drift > 1:
            raised[agent] = True
        elif raised[agent]:
            corrections[agent] = corrections.get(agent, 0) + 1
            raised[agent] = False
    pending = []
    for agent in raised:
        if raised[agent]:
            pending.append(agent)
    leader = None
    for agent in order:
        if agent not in corrections:
            continue
        if leader is None or corrections[agent] > corrections[leader]:
            leader = agent
    return {'total': len(rows),
            'corrections': corrections,
            'pending': sorted(pending),
            'leader': leader}

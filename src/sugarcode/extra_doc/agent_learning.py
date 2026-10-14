"""Row 1943, Title: Agent Learning

catch_frontier(rows): rows are (episode, agent, reward)
triples; episode and agent strings of 1 to 16
characters; reward a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each agent its
catches (rows where its reward equals the frontier,
the best reward seen on earlier rows, while the agent
itself is behind or new), the frontier after all rows,
and the leader (the most catches, first supplied on
ties, or None when no agent catches).

SCOPE: PARTIAL: frontier tracking over supplied rewards
NOT_CLAIMED: gradient computation, reward modeling,
exploration strategy, convergence proofs, production
readiness.
"""

SCOPE = 'PARTIAL: frontier tracking over supplied rewards'
NOT_CLAIMED = ('gradient computation', 'reward modeling',
               'exploration strategy', 'convergence proofs',
               'production readiness')


def catch_frontier(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected an (episode, agent, reward) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        episode, agent, reward = row
        if type(episode) is not str or not 1 <= len(episode) <= 16:
            raise ValueError(f'row {i}: episode must be a string of 1 to 16 characters')
        if type(agent) is not str or not 1 <= len(agent) <= 16:
            raise ValueError(f'row {i}: agent must be a string of 1 to 16 characters')
        if type(reward) is not int or not 1 <= reward <= 9:
            raise ValueError(f'row {i}: reward must be a nonbool integer between 1 and 9')
    own = {}
    order = {}
    catches = {}
    frontier = None
    for episode, agent, reward in rows:
        if agent not in order:
            order[agent] = True
        if (frontier is not None and reward == frontier
                and (agent not in own or own[agent] < frontier)):
            if agent not in catches:
                catches[agent] = 0
            catches[agent] += 1
        own[agent] = reward
        if frontier is None or reward > frontier:
            frontier = reward
    leader = None
    for agent in order:
        if agent not in catches:
            continue
        if leader is None or catches[agent] > catches[leader]:
            leader = agent
    return {'total': len(rows),
            'catches': catches,
            'frontier': frontier,
            'leader': leader}

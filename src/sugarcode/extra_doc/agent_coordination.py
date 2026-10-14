"""Row 1941, Title: Agent Coordination

tighten_spans(rows): rows are (agent, channel, load)
triples; agent and channel strings of 1 to 16
characters; load a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each agent its
cumulative load, the tightenings (rows after which the
span of the cumulative loads, taken over the agents
seen so far, strictly decreased from the previous
span), and the final span (0 when only one agent was
supplied).

SCOPE: PARTIAL: span tracking over supplied loads
NOT_CLAIMED: task scheduling, load balancing, fault
tolerance, network transport, production readiness.
"""

SCOPE = 'PARTIAL: span tracking over supplied loads'
NOT_CLAIMED = ('task scheduling', 'load balancing', 'fault tolerance',
               'network transport', 'production readiness')


def tighten_spans(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected an (agent, channel, load) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        agent, channel, load = row
        if type(agent) is not str or not 1 <= len(agent) <= 16:
            raise ValueError(f'row {i}: agent must be a string of 1 to 16 characters')
        if type(channel) is not str or not 1 <= len(channel) <= 16:
            raise ValueError(f'row {i}: channel must be a string of 1 to 16 characters')
        if type(load) is not int or not 1 <= load <= 9:
            raise ValueError(f'row {i}: load must be a nonbool integer between 1 and 9')
    sums = {}
    tightenings = 0
    previous = None
    for agent, channel, load in rows:
        if agent not in sums:
            sums[agent] = 0
        sums[agent] += load
        if len(sums) >= 2:
            span = max(sums.values()) - min(sums.values())
            if previous is not None and span < previous:
                tightenings += 1
            previous = span
    return {'total': len(rows),
            'sums': sums,
            'tightenings': tightenings,
            'span': previous if previous is not None else 0}

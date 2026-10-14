"""Row 517 Message Queue Design: exact tick-by-tick backlog of a bounded queue.

The caller supplies arrivals per tick (1 to 100 ints, each 0 to 10**6), a service capacity per tick
(int 0 to 10**6) and a queue capacity (int 0 to 10**6 messages). Each tick first admits arrivals up
to the free space (the rest are dropped) and then serves up to the service capacity. Reported: the
backlog after each tick, the messages served and dropped per tick and in total, the largest backlog,
and the number of extra ticks of service needed to drain the final backlog (None when the service
capacity is 0 and a backlog remains). Caps and the tick order are implementation choices, not spec
values. No broker is modelled: no redelivery, ordering, acknowledgement or latency.
NOT_CLAIMED: that the arrival counts or capacities are measured, that real traffic is tick-shaped,
delivery guarantees, ordering, durability, latency, that any queue size is right, approval-gate
clearance, deployment.
"""
NOT_CLAIMED = ('arrival counts or capacities measured', 'real traffic is tick-shaped',
               'delivery guarantees, ordering, durability or latency', 'any queue size is right',
               'approval-gate clearance', 'deployment')


def simulate_queue(arrivals, service, capacity):
    for label, v in (('service', service), ('capacity', capacity)):
        if type(v) is not int:
            raise TypeError(label + ' must be nonbool int')
        if not 0 <= v <= 10 ** 6:
            raise ValueError(label + ' must be between 0 and 1000000')
    if type(arrivals) not in (list, tuple):
        raise TypeError('arrivals must be a list or tuple')
    if not 1 <= len(arrivals) <= 100:
        raise ValueError('tick count must be between 1 and 100')
    for a in arrivals:
        if type(a) is not int:
            raise TypeError('arrivals must be nonbool int')
        if not 0 <= a <= 10 ** 6:
            raise ValueError('arrivals must be between 0 and 1000000')
    backlog = 0
    ticks = []
    for a in arrivals:
        admit = min(a, capacity - backlog)
        backlog += admit
        served = min(backlog, service)
        backlog -= served
        ticks.append({'arrived': a, 'dropped': a - admit, 'served': served, 'backlog': backlog})
    if backlog == 0:
        drain = 0
    elif service == 0:
        drain = None
    else:
        drain = -(-backlog // service)
    return {'ticks': ticks, 'total_served': sum(t['served'] for t in ticks),
            'total_dropped': sum(t['dropped'] for t in ticks), 'max_backlog': max(t['backlog'] for t in ticks),
            'drain_ticks': drain, 'queue_validated': False, 'not_claimed': NOT_CLAIMED}

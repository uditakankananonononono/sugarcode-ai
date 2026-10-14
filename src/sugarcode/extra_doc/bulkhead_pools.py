"""Row 658, Bulkhead Pattern: admission into isolated pools of supplied requests.

bulkhead_pools takes pools, a list or tuple of 1 to 6 (name, limit) pairs
(unique names of 1 to 12 characters, limit a nonbool int from 1 to 10), and
requests, a list or tuple of 0 to 40 pool names. No request finishes during
the run. total_limit is None (no shared cap) or a nonbool int from 1 to 60,
the cap on admitted requests over all pools. A request is rejected with
'pool_full' when its pool already holds limit admitted requests, else with
'total_full' when total_limit is set and reached, else it is 'admitted'.
Reported: statuses (one per request), in_flight (pool name to admitted
count, in pool order) and rejected (pool name to rejected count).
Checks, in this order: pools type, pools size, requests type, requests size,
total_limit, then each pool (pair shape, name, duplicate name, limit), then
each request (a string naming a known pool).
NOT_CLAIMED: real concurrency, thread or connection pools, timeouts, queueing,
production readiness.
"""
SCOPE = 'PARTIAL: pool admission arithmetic over supplied requests, no real concurrency'
NOT_CLAIMED = ('real concurrency', 'thread or connection pools', 'timeouts', 'queueing',
               'production readiness')


def bulkhead_pools(pools, requests, total_limit=None):
    if type(pools) not in (list, tuple):
        raise TypeError('pools must be a list or tuple')
    if not 1 <= len(pools) <= 6:
        raise ValueError('pools must contain 1 to 6 entries')
    if type(requests) not in (list, tuple):
        raise TypeError('requests must be a list or tuple')
    if len(requests) > 40:
        raise ValueError('requests must contain at most 40 entries')
    if total_limit is not None and (type(total_limit) is not int or not 1 <= total_limit <= 60):
        raise ValueError('total_limit must be None or a nonbool integer between 1 and 60')
    limits = {}
    for p in pools:
        if type(p) not in (list, tuple) or len(p) != 2:
            raise ValueError('each pool must be a (name, limit) pair')
        name, limit = p
        if type(name) is not str or not 1 <= len(name) <= 12:
            raise ValueError('pool names must be strings of 1 to 12 characters')
        if name in limits:
            raise ValueError('duplicate pool name')
        if type(limit) is not int or not 1 <= limit <= 10:
            raise ValueError('limit must be a nonbool integer between 1 and 10')
        limits[name] = limit
    for r in requests:
        if type(r) is not str or r not in limits:
            raise ValueError('each request must name a known pool')
    in_flight = {n: 0 for n in limits}
    rejected = {n: 0 for n in limits}
    statuses = []
    total = 0
    for r in requests:
        if in_flight[r] >= limits[r]:
            statuses.append('pool_full')
            rejected[r] += 1
        elif total_limit is not None and total >= total_limit:
            statuses.append('total_full')
            rejected[r] += 1
        else:
            statuses.append('admitted')
            in_flight[r] += 1
            total += 1
    return {'statuses': statuses, 'in_flight': in_flight, 'rejected': rejected}

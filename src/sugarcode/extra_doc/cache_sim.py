"""Row 518 Caching Strategy: exact hit/miss counts for a key trace under LRU or FIFO.

The caller supplies a trace of 1 to 200 keys (1 to 20 character str), a capacity (int 1 to 50) and a
policy, 'lru' or 'fifo', plus hit and miss latencies in milliseconds (ints 0 to 10**6, hit not above
miss). Reported: per access hit or miss, the hit and miss counts, the hit ratio (Fraction), the number
of evictions, the final contents from oldest to newest by the policy's own order, the average latency
with the cache and the miss latency used as the no-cache latency, and the speedup (Fraction, None when
the cached average is 0). Caps are implementation choices, not spec values. Nothing is cached or timed
here; the trace and latencies are the caller's.
NOT_CLAIMED: that the trace is representative of real traffic, that the latencies are measured,
consistency, staleness or invalidation behaviour, memory or cost, that either policy suits a real
workload, approval-gate clearance, deployment.
"""
from fractions import Fraction

NOT_CLAIMED = ('trace representative of real traffic', 'latencies measured',
               'consistency, staleness or invalidation behaviour', 'memory or cost',
               'either policy suits a real workload', 'approval-gate clearance', 'deployment')


def simulate_cache(trace, capacity, policy, hit_ms, miss_ms):
    for label, v, lo, hi in (('capacity', capacity, 1, 50), ('hit_ms', hit_ms, 0, 10 ** 6),
                             ('miss_ms', miss_ms, 0, 10 ** 6)):
        if type(v) is not int:
            raise TypeError(label + ' must be nonbool int')
        if not lo <= v <= hi:
            raise ValueError('%s must be between %d and %d' % (label, lo, hi))
    if hit_ms > miss_ms:
        raise ValueError('hit_ms must not exceed miss_ms')
    if type(policy) is not str:
        raise TypeError('policy must be str')
    if policy not in ('lru', 'fifo'):
        raise ValueError("policy must be 'lru' or 'fifo'")
    if type(trace) not in (list, tuple):
        raise TypeError('trace must be a list or tuple')
    if not 1 <= len(trace) <= 200:
        raise ValueError('trace length must be between 1 and 200')
    for k in trace:
        if type(k) is not str:
            raise TypeError('trace keys must be str')
        if not 1 <= len(k) <= 20:
            raise ValueError('trace keys must be 1 to 20 characters')
    order = []
    hits = []
    evictions = 0
    for k in trace:
        if k in order:
            hits.append(True)
            if policy == 'lru':
                order.remove(k)
                order.append(k)
        else:
            hits.append(False)
            if len(order) == capacity:
                order.pop(0)
                evictions += 1
            order.append(k)
    h = sum(hits)
    n = len(trace)
    avg = Fraction(h * hit_ms + (n - h) * miss_ms, n)
    return {'accesses': ['hit' if x else 'miss' for x in hits], 'hits': h, 'misses': n - h,
            'hit_ratio': Fraction(h, n), 'evictions': evictions, 'final_contents': tuple(order),
            'average_ms': avg, 'no_cache_ms': miss_ms, 'speedup': Fraction(miss_ms) / avg if avg else None,
            'strategy_validated': False, 'not_claimed': NOT_CLAIMED}

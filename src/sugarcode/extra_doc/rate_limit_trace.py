"""Row 619, Rate Limiting: replaying request times through a token bucket.

The bucket starts full with capacity tokens and gains one token every
interval time units, never holding more than capacity. A request at time t
takes one token and is allowed if a token is there, otherwise it is limited and
takes nothing. Time spent while the bucket is full earns nothing toward the
next token. Reported: allowed or limited per request, the counts of each, and
the tokens left right after the last request (no refill after it is counted).
Caps (checked before any work): 0 to 100 request times, capacity 1 to 100
(default 5), interval 1 to 1000 (default 10), times nonbool ints from 0 to
1000000 that do not decrease.
NOT_CLAIMED: real clocks, per-client keys, distributed counters, burst
tuning, fairness, response headers, production readiness.
"""
SCOPE = 'PARTIAL: token-bucket replay of supplied request times, no real clock or clients'
NOT_CLAIMED = ('real clocks', 'per-client keys', 'distributed counters', 'burst tuning',
               'fairness', 'response headers', 'production readiness')

MAX_REQUESTS = 100
MAX_TIME = 1000000


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def rate_limit_trace(requests, capacity=5, interval=10):
    if type(requests) not in (list, tuple):
        raise TypeError('requests must be a list or tuple')
    if len(requests) > MAX_REQUESTS:
        raise ValueError('requests must contain at most 100 entries')
    _int(capacity, 1, 100, 'capacity must be a nonbool integer between 1 and 100')
    _int(interval, 1, 1000, 'interval must be a nonbool integer between 1 and 1000')
    last = 0
    for t in requests:
        _int(t, 0, MAX_TIME, 'times must be nonbool integers between 0 and 1000000')
        if t < last:
            raise ValueError('times must not decrease')
        last = t
    tokens, clock, results = capacity, 0, []
    for t in requests:
        gained = (t - clock) // interval
        if tokens + gained >= capacity:
            tokens, clock = capacity, t
        else:
            tokens, clock = tokens + gained, clock + gained * interval
        if tokens >= 1:
            tokens -= 1
            results.append('allowed')
        else:
            results.append('limited')
    allowed = results.count('allowed')
    return {'results': results, 'allowed': allowed, 'limited': len(results) - allowed, 'tokens': tokens}

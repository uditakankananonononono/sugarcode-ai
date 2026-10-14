"""Row 618, Circuit Breaker: replaying a call trace through a three-state breaker.

Events are (time, ok) pairs in time order, ok being True for a call that
succeeds and False for one that fails. The breaker starts closed. In the closed
state threshold failures in a row open it at that call's time; a success resets
the count. While open, a call with time - opened_at < cooldown is rejected and
not run. The first call with time - opened_at >= cooldown is the half-open
probe: it is run, a success closes the breaker, a failure opens it again at
that call's time. Reported: the result per event ('success', 'failure' or
'rejected'), the final state ('closed' or 'open') and how many times it opened.
Caps (checked before any work): 0 to 100 events, threshold 1 to 10 (default 3),
cooldown 1 to 1000 (default 10), times nonbool ints from 0 to 1000000 that do
not decrease, ok an exact bool.
NOT_CLAIMED: real calls, timeouts, concurrency, half-open probe limits beyond a
single probe, error classification, metrics, production readiness.
"""
SCOPE = 'PARTIAL: replay of a supplied call trace through a closed, open and half-open breaker, no real calls'
NOT_CLAIMED = ('real calls', 'timeouts', 'concurrency', 'probe limits beyond a single probe',
               'error classification', 'metrics', 'production readiness')

MAX_EVENTS = 100
MAX_TIME = 1000000


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def replay_breaker(events, threshold=3, cooldown=10):
    if type(events) not in (list, tuple):
        raise TypeError('events must be a list or tuple')
    if len(events) > MAX_EVENTS:
        raise ValueError('events must contain at most 100 entries')
    _int(threshold, 1, 10, 'threshold must be a nonbool integer between 1 and 10')
    _int(cooldown, 1, 1000, 'cooldown must be a nonbool integer between 1 and 1000')
    last = 0
    for e in events:
        if type(e) not in (list, tuple) or len(e) != 2:
            raise ValueError('each event must be a (time, ok) pair')
        t, ok = e
        _int(t, 0, MAX_TIME, 'time must be a nonbool integer between 0 and 1000000')
        if type(ok) is not bool:
            raise ValueError('ok must be a bool')
        if t < last:
            raise ValueError('times must not decrease')
        last = t
    state, fails, opened_at, opens, results = 'closed', 0, 0, 0, []
    for t, ok in events:
        if state == 'open' and t - opened_at < cooldown:
            results.append('rejected')
            continue
        probe = state == 'open'
        results.append('success' if ok else 'failure')
        if ok:
            state, fails = 'closed', 0
        elif probe or fails + 1 >= threshold:
            state, fails, opened_at, opens = 'open', 0, t, opens + 1
        else:
            fails += 1
    return {'results': results, 'state': state, 'opens': opens}

"""Row 652, Idempotency: replay handling of supplied keyed requests.

idempotency_keys takes requests, a list or tuple of 0 to 40 (key, payload)
pairs: key a string of 1 to 12 characters, payload a nonbool int from 0 to
1000. capacity is a nonbool int from 1 to 20 (default 5), the number of keys
remembered. A key not remembered executes and is remembered; when more than
capacity keys are remembered the oldest-remembered one is forgotten, so it
would execute again. A remembered key with the same payload is a replay and
is not executed; with a different payload it is a conflict and is not
executed. A replay does not refresh the key. Reported: statuses (one of
'executed', 'replayed' or 'conflict' per request), counts (per status) and
remembered (keys, oldest first).
Checks, in this order: requests type, requests size, capacity, then per
request the pair shape, key and payload.
NOT_CLAIMED: storing real responses, expiry by time, concurrency, HTTP
headers, production readiness.
"""
SCOPE = 'PARTIAL: replay and conflict handling of supplied keyed requests, no real storage'
NOT_CLAIMED = ('storing real responses', 'expiry by time', 'concurrency', 'HTTP headers',
               'production readiness')

MAX_REQUESTS = 40


def idempotency_keys(requests, capacity=5):
    if type(requests) not in (list, tuple):
        raise TypeError('requests must be a list or tuple')
    if len(requests) > MAX_REQUESTS:
        raise ValueError('requests must contain at most 40 entries')
    if type(capacity) is not int or not 1 <= capacity <= 20:
        raise ValueError('capacity must be a nonbool integer between 1 and 20')
    for r in requests:
        if type(r) not in (list, tuple) or len(r) != 2:
            raise ValueError('each request must be a (key, payload) pair')
        key, payload = r
        if type(key) is not str or not 1 <= len(key) <= 12:
            raise ValueError('keys must be strings of 1 to 12 characters')
        if type(payload) is not int or not 0 <= payload <= 1000:
            raise ValueError('payload must be a nonbool integer between 0 and 1000')
    store = {}
    statuses = []
    for key, payload in requests:
        if key in store:
            statuses.append('replayed' if store[key] == payload else 'conflict')
        else:
            statuses.append('executed')
            store[key] = payload
            if len(store) > capacity:
                del store[next(iter(store))]
    counts = {s: statuses.count(s) for s in ('executed', 'replayed', 'conflict')}
    return {'statuses': statuses, 'counts': counts, 'remembered': list(store)}

"""Row 660, Ambassador Pattern: a proxy deciding over supplied requests.

ambassador_proxy takes allowed_paths, a list or tuple of 1 to 6 unique strings
of 1 to 16 characters, and requests, a list or tuple of 0 to 40 (client, path)
pairs (client a string of 1 to 12 characters, path a string of 1 to 16).
rate_limit is a nonbool int from 1 to 20 (default 3): the most requests
forwarded per client. A request for a path not allowed is 'denied' and does
not count against the client. Else, if the client already had rate_limit
requests forwarded, it is 'rate_limited' (not counted); otherwise it is
'forwarded'. Reported: statuses (one per request), forwarded (client to
forwarded count, in order of first forward) and counts (per status).
Checks, in this order: allowed_paths type, size, requests type, size,
rate_limit, then each allowed path (type, length, duplicate), then each
request (pair shape, client, path).
NOT_CLAIMED: real proxying, networking, authentication, time windows,
production readiness.
"""
SCOPE = 'PARTIAL: allow-list and rate decisions over supplied requests, no real proxying'
NOT_CLAIMED = ('real proxying', 'networking', 'authentication', 'time windows',
               'production readiness')


def ambassador_proxy(allowed_paths, requests, rate_limit=3):
    if type(allowed_paths) not in (list, tuple):
        raise TypeError('allowed_paths must be a list or tuple')
    if not 1 <= len(allowed_paths) <= 6:
        raise ValueError('allowed_paths must contain 1 to 6 entries')
    if type(requests) not in (list, tuple):
        raise TypeError('requests must be a list or tuple')
    if len(requests) > 40:
        raise ValueError('requests must contain at most 40 entries')
    if type(rate_limit) is not int or not 1 <= rate_limit <= 20:
        raise ValueError('rate_limit must be a nonbool integer between 1 and 20')
    allowed = set()
    for p in allowed_paths:
        if type(p) is not str or not 1 <= len(p) <= 16:
            raise ValueError('paths must be strings of 1 to 16 characters')
        if p in allowed:
            raise ValueError('duplicate allowed path')
        allowed.add(p)
    for r in requests:
        if type(r) not in (list, tuple) or len(r) != 2:
            raise ValueError('each request must be a (client, path) pair')
        client, path = r
        if type(client) is not str or not 1 <= len(client) <= 12:
            raise ValueError('clients must be strings of 1 to 12 characters')
        if type(path) is not str or not 1 <= len(path) <= 16:
            raise ValueError('paths must be strings of 1 to 16 characters')
    forwarded = {}
    statuses = []
    for client, path in requests:
        if path not in allowed:
            statuses.append('denied')
        elif forwarded.get(client, 0) >= rate_limit:
            statuses.append('rate_limited')
        else:
            statuses.append('forwarded')
            forwarded[client] = forwarded.get(client, 0) + 1
    counts = {s: statuses.count(s) for s in ('forwarded', 'denied', 'rate_limited')}
    return {'statuses': statuses, 'forwarded': forwarded, 'counts': counts}

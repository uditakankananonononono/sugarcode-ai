"""Row 628, Traffic Mirroring: choosing which requests to copy to a mirror.

Requests are (request_id, method) pairs in arrival order. Only GET and HEAD
requests may be copied; POST, PUT and DELETE are never mirrored. Among the
copyable requests, taken in order and counted from 0, the k-th is mirrored when
floor((k+1) * percent / 100) exceeds floor(k * percent / 100), so after any k
copyable requests exactly floor(k * percent / 100) have been mirrored. Reported: mirrored ids and
skipped (not copyable) ids in arrival order, the number of copyable requests
and the number mirrored.
Caps (checked before any work): 0 to 100 requests, unique ids of 1 to 16
characters, method one of GET, HEAD, POST, PUT, DELETE, percent a nonbool int
from 0 to 100 (default 25).
NOT_CLAIMED: copying real traffic, response handling, payload scrubbing,
mirror capacity, ordering guarantees at the mirror, production readiness.
"""
SCOPE = 'PARTIAL: even selection of supplied safe requests for mirroring, no real copying'
NOT_CLAIMED = ('copying real traffic', 'response handling', 'payload scrubbing', 'mirror capacity',
               'ordering guarantees at the mirror', 'production readiness')

MAX_REQUESTS = 100
METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE')
SAFE = ('GET', 'HEAD')


def mirror_plan(requests, percent=25):
    if type(requests) not in (list, tuple):
        raise TypeError('requests must be a list or tuple')
    if len(requests) > MAX_REQUESTS:
        raise ValueError('requests must contain at most 100 entries')
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 0 and 100')
    seen = set()
    for r in requests:
        if type(r) not in (list, tuple) or len(r) != 2:
            raise ValueError('each request must be a (request_id, method) pair')
        rid, method = r
        if type(rid) is not str or not 1 <= len(rid) <= 16:
            raise ValueError('request ids must be strings of 1 to 16 characters')
        if type(method) is not str or method not in METHODS:
            raise ValueError('method must be one of GET, HEAD, POST, PUT, DELETE')
        if rid in seen:
            raise ValueError('duplicate request id')
        seen.add(rid)
    mirrored, skipped, k = [], [], 0
    for rid, method in requests:
        if method not in SAFE:
            skipped.append(rid)
            continue
        if (k + 1) * percent // 100 > k * percent // 100:
            mirrored.append(rid)
        k += 1
    return {'mirrored': mirrored, 'skipped': skipped, 'eligible': k, 'count': len(mirrored)}

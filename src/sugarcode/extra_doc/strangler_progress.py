"""Row 695, Strangler Fig Pattern: cutover progress of supplied routes.

strangler_progress takes routes, a list or tuple of (path, target) pairs, and
max_routes, a nonbool int from 1 to 20 (default 8). A path is a string of 1 to
16 characters, distinct across routes. A target is 'legacy' or 'new'. The list
must hold 1 to max_routes routes.
Returns new and legacy (route counts), percent (new * 100 // total, rounded
down), phase ('not_started' with no new route, 'complete' with no legacy
route, else 'strangling') and next_route (the first legacy path in input
order, or None).
Checks, in this order: max_routes, routes type, routes size, each pair (shape,
path, target), duplicate paths.
NOT_CLAIMED: real traffic routing, route correctness, rollback safety,
legacy shutdown, production readiness.
"""
SCOPE = 'PARTIAL: count-based cutover summary of supplied routes, no traffic is routed'
NOT_CLAIMED = ('real traffic routing', 'route correctness', 'rollback safety',
               'legacy shutdown', 'production readiness')


def strangler_progress(routes, max_routes=8):
    if type(max_routes) is not int or not 1 <= max_routes <= 20:
        raise ValueError('max_routes must be a nonbool integer between 1 and 20')
    if type(routes) not in (list, tuple):
        raise TypeError('routes must be a list or tuple')
    if not 1 <= len(routes) <= max_routes:
        raise ValueError('routes must contain 1 to max_routes entries')
    rows = []
    for r in routes:
        if type(r) not in (list, tuple) or len(r) != 2:
            raise ValueError('each route must be a (path, target) pair')
        path, target = r
        if type(path) is not str or not 1 <= len(path) <= 16:
            raise ValueError('each path must be a string of 1 to 16 characters')
        if type(target) is not str or target not in ('legacy', 'new'):
            raise ValueError('target must be legacy or new')
        rows.append((path, target))
    if len({p for p, _ in rows}) != len(rows):
        raise ValueError('paths must be distinct')
    new = sum(1 for _, t in rows if t == 'new')
    legacy = len(rows) - new
    if new == 0:
        phase = 'not_started'
    elif legacy == 0:
        phase = 'complete'
    else:
        phase = 'strangling'
    nxt = next((p for p, t in rows if t == 'legacy'), None)
    return {'new': new, 'legacy': legacy, 'percent': new * 100 // len(rows),
            'phase': phase, 'next_route': nxt}

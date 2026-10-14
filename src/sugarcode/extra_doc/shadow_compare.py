"""Row 627, Shadow Traffic: comparing shadow responses with primary ones.

Each pair is (request_id, primary_status, shadow_status, primary_ms,
shadow_ms): the same request answered by the live service and by its shadow.
A pair is mismatched when the two statuses differ, and slow when the shadow
took more than slow_percent percent longer than the primary, that is
shadow_ms * 100 > primary_ms * (100 + slow_percent). A pair can be both.
Reported: sorted ids of mismatched, slow and clean (neither) pairs and the
total. Only supplied numbers are compared; nothing is sent anywhere.
Caps (checked before any work): 0 to 50 pairs, unique request ids of 1 to 16
characters, statuses nonbool ints from 100 to 599, times nonbool ints from 1
to 100000, slow_percent a nonbool int from 0 to 1000 (default 20).
NOT_CLAIMED: replaying real requests, response body comparison, side-effect
isolation, sampling, statistical significance, production readiness.
"""
SCOPE = 'PARTIAL: status and latency comparison of supplied primary and shadow results, nothing replayed'
NOT_CLAIMED = ('replaying real requests', 'response body comparison', 'side-effect isolation',
               'sampling', 'statistical significance', 'production readiness')

MAX_PAIRS = 50


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def compare_shadow(pairs, slow_percent=20):
    if type(pairs) not in (list, tuple):
        raise TypeError('pairs must be a list or tuple')
    if len(pairs) > MAX_PAIRS:
        raise ValueError('pairs must contain at most 50 entries')
    _int(slow_percent, 0, 1000, 'slow_percent must be a nonbool integer between 0 and 1000')
    seen = set()
    for p in pairs:
        if type(p) not in (list, tuple) or len(p) != 5:
            raise ValueError('each pair must be a (request_id, primary_status, shadow_status, primary_ms, shadow_ms) tuple')
        rid, ps, ss, pm, sm = p
        if type(rid) is not str or not 1 <= len(rid) <= 16:
            raise ValueError('request ids must be strings of 1 to 16 characters')
        _int(ps, 100, 599, 'status must be a nonbool integer between 100 and 599')
        _int(ss, 100, 599, 'status must be a nonbool integer between 100 and 599')
        _int(pm, 1, 100000, 'milliseconds must be nonbool integers between 1 and 100000')
        _int(sm, 1, 100000, 'milliseconds must be nonbool integers between 1 and 100000')
        if rid in seen:
            raise ValueError('duplicate request id')
        seen.add(rid)
    mismatched = sorted(p[0] for p in pairs if p[1] != p[2])
    slow = sorted(p[0] for p in pairs if p[4] * 100 > p[3] * (100 + slow_percent))
    clean = sorted(p[0] for p in pairs if p[1] == p[2] and p[4] * 100 <= p[3] * (100 + slow_percent))
    return {'mismatched': mismatched, 'slow': slow, 'clean': clean, 'total': len(pairs)}

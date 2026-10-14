"""Row 653, Exactly-Once Semantics: dedup of supplied redelivered messages.

exactly_once_apply takes deliveries, a list or tuple of 0 to 40 (msg_id, delta)
pairs: msg_id a nonbool int from 0 to 99, delta a nonbool int from -100 to
100. start is a nonbool int from -1000 to 1000 (default 0). Each msg_id has
its delta applied once, on first delivery; later deliveries of the same id
are skipped, and a later delivery of a known id with a different delta is
refused. Reported: balance (start plus the applied deltas), applied (ids in
first-delivery order), duplicates (number of skipped deliveries) and flags
(per delivery True when applied, False when skipped).
Checks, in this order: deliveries type, deliveries size, start, then per
delivery the pair shape, id, delta and then a changed delta for a known id.
NOT_CLAIMED: real brokers, transactions, persistence, ordering guarantees,
crash recovery, production readiness.
"""
SCOPE = 'PARTIAL: deduplicated application of supplied deliveries, no real broker'
NOT_CLAIMED = ('real brokers', 'transactions', 'persistence', 'ordering guarantees',
               'crash recovery', 'production readiness')

MAX_DELIVERIES = 40


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def exactly_once_apply(deliveries, start=0):
    if type(deliveries) not in (list, tuple):
        raise TypeError('deliveries must be a list or tuple')
    if len(deliveries) > MAX_DELIVERIES:
        raise ValueError('deliveries must contain at most 40 entries')
    _int(start, -1000, 1000, 'start must be a nonbool integer between -1000 and 1000')
    seen = {}
    flags = []
    for d in deliveries:
        if type(d) not in (list, tuple) or len(d) != 2:
            raise ValueError('each delivery must be a (msg_id, delta) pair')
        mid, delta = d
        _int(mid, 0, 99, 'msg_id must be a nonbool integer between 0 and 99')
        _int(delta, -100, 100, 'delta must be a nonbool integer between -100 and 100')
        if mid in seen:
            if seen[mid] != delta:
                raise ValueError('a known msg_id came again with a different delta')
            flags.append(False)
        else:
            seen[mid] = delta
            flags.append(True)
    return {
        'balance': start + sum(seen.values()),
        'applied': list(seen),
        'duplicates': flags.count(False),
        'flags': flags,
    }

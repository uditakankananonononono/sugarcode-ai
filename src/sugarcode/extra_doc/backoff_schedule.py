"""Row 657, Backoff Strategy: delay schedule for supplied retry counts.

backoff_schedule takes count, a nonbool int from 0 to 12 (retries to
schedule). base is a nonbool int from 1 to 1000 milliseconds (default 100).
kind is 'fixed', 'linear' or 'exponential' (default 'exponential'). cap is
a nonbool int from 1 to 100000 milliseconds (default 5000). Delay number i
(counting from 0) is base for fixed, base times (i + 1) for linear and base
times 2 to the power i for exponential, each limited to cap. Reported:
delays (one per retry), total (their sum) and capped (how many delays were
cut down to cap).
Checks, in this order: count, base, kind, cap.
NOT_CLAIMED: sleeping, random jitter, real clocks, retry execution,
production readiness.
"""
SCOPE = 'PARTIAL: backoff delay arithmetic for supplied counts, nothing waits'
NOT_CLAIMED = ('sleeping', 'random jitter', 'real clocks', 'retry execution',
               'production readiness')

KINDS = ('fixed', 'linear', 'exponential')


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def backoff_schedule(count, base=100, kind='exponential', cap=5000):
    _int(count, 0, 12, 'count must be a nonbool integer between 0 and 12')
    _int(base, 1, 1000, 'base must be a nonbool integer between 1 and 1000')
    if type(kind) is not str or kind not in KINDS:
        raise ValueError('kind must be fixed, linear or exponential')
    _int(cap, 1, 100000, 'cap must be a nonbool integer between 1 and 100000')
    delays = []
    capped = 0
    for i in range(count):
        if kind == 'fixed':
            d = base
        elif kind == 'linear':
            d = base * (i + 1)
        else:
            d = base * 2 ** i
        if d > cap:
            d = cap
            capped += 1
        delays.append(d)
    return {'delays': delays, 'total': sum(delays), 'capped': capped}

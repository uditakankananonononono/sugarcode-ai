"""Row 633, Alerting: replaying readings against threshold rules.

rules is a list or tuple of 1 to 20 (name, threshold, for_count) triples. A rule
starts ok. While ok, it fires at the reading where for_count readings in a row
have been above its threshold (strictly greater), counting only readings since
the rule last resolved. While firing it resolves at the first reading that is
at or below threshold - hysteresis, and may fire again later. Reported per rule:
the reading indexes where it fired and where it resolved, and its final state;
plus the sorted names still firing at the end.
Caps (checked before any work): unique rule names of 1 to 16 characters,
threshold nonbool int 0 to 1000000, for_count 1 to 10, 0 to 100 readings (nonbool
ints 0 to 1000000), hysteresis a nonbool int from 0 to 1000 (default 0).
NOT_CLAIMED: delivering notifications, paging, routing, silencing, deduplication,
real metric collection, production readiness.
"""
SCOPE = 'PARTIAL: threshold rule replay over supplied readings, no notifications sent'
NOT_CLAIMED = ('delivering notifications', 'paging', 'routing', 'silencing', 'deduplication',
               'real metric collection', 'production readiness')

MAX_RULES = 20
MAX_READINGS = 100


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def evaluate_alerts(rules, readings, hysteresis=0):
    if type(rules) not in (list, tuple):
        raise TypeError('rules must be a list or tuple')
    if not 1 <= len(rules) <= MAX_RULES:
        raise ValueError('rules must contain between 1 and 20 entries')
    if type(readings) not in (list, tuple):
        raise TypeError('readings must be a list or tuple')
    if len(readings) > MAX_READINGS:
        raise ValueError('readings must contain at most 100 entries')
    _int(hysteresis, 0, 1000, 'hysteresis must be a nonbool integer between 0 and 1000')
    names = set()
    for r in rules:
        if type(r) not in (list, tuple) or len(r) != 3:
            raise ValueError('each rule must be a (name, threshold, for_count) triple')
        name, threshold, for_count = r
        if type(name) is not str or not 1 <= len(name) <= 16:
            raise ValueError('rule names must be strings of 1 to 16 characters')
        if name in names:
            raise ValueError('duplicate rule name')
        names.add(name)
        _int(threshold, 0, 1000000, 'threshold must be a nonbool integer between 0 and 1000000')
        _int(for_count, 1, 10, 'for_count must be a nonbool integer between 1 and 10')
    for v in readings:
        _int(v, 0, 1000000, 'readings must be nonbool integers between 0 and 1000000')
    out = {}
    for name, threshold, for_count in rules:
        fired, resolved, firing, streak = [], [], False, 0
        for i, v in enumerate(readings):
            if firing:
                if v <= threshold - hysteresis:
                    firing = False
                    resolved.append(i)
            elif v > threshold:
                streak += 1
                if streak == for_count:
                    firing, streak = True, 0
                    fired.append(i)
            else:
                streak = 0
        out[name] = {'fired': fired, 'resolved': resolved, 'state': 'firing' if firing else 'ok'}
    return {'rules': out, 'firing': sorted(n for n, r in out.items() if r['state'] == 'firing')}

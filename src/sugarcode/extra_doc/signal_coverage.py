"""Row 629, Observability: which signals each service emits.

Signals are (service, pillar) pairs, a pillar being one of metrics, logs or
traces. For every service named in the signals, the pillars it emits and the
ones it is missing are reported (both sorted). A service is observed when it
emits at least min_pillars distinct pillars, otherwise blind. Reported:
coverage and missing per service, and the sorted observed and blind services.
Caps (checked before any work): 0 to 60 signals, service names are strings of
1 to 16 characters, a (service, pillar) pair appears once, min_pillars is a
nonbool int from 1 to 3 (default 2).
NOT_CLAIMED: signal quality, sampling, retention, alert rules, dashboards,
understanding a real system's state, production readiness.
"""
SCOPE = 'PARTIAL: pillar coverage count over supplied service signal pairs, no real telemetry'
NOT_CLAIMED = ('signal quality', 'sampling', 'retention', 'alert rules', 'dashboards',
               'understanding a real system state', 'production readiness')

MAX_SIGNALS = 60
PILLARS = ('metrics', 'logs', 'traces')


def coverage_report(signals, min_pillars=2):
    if type(signals) not in (list, tuple):
        raise TypeError('signals must be a list or tuple')
    if len(signals) > MAX_SIGNALS:
        raise ValueError('signals must contain at most 60 entries')
    if type(min_pillars) is not int or not 1 <= min_pillars <= 3:
        raise ValueError('min_pillars must be a nonbool integer between 1 and 3')
    seen = set()
    for s in signals:
        if type(s) not in (list, tuple) or len(s) != 2:
            raise ValueError('each signal must be a (service, pillar) pair')
        service, pillar = s
        if type(service) is not str or not 1 <= len(service) <= 16:
            raise ValueError('service names must be strings of 1 to 16 characters')
        if type(pillar) is not str or pillar not in PILLARS:
            raise ValueError('pillar must be one of metrics, logs, traces')
        if (service, pillar) in seen:
            raise ValueError('duplicate signal')
        seen.add((service, pillar))
    coverage = {}
    for service, pillar in signals:
        coverage.setdefault(service, []).append(pillar)
    coverage = {s: sorted(p) for s, p in coverage.items()}
    missing = {s: sorted(set(PILLARS) - set(p)) for s, p in coverage.items()}
    return {'coverage': coverage, 'missing': missing,
            'observed': sorted(s for s, p in coverage.items() if len(p) >= min_pillars),
            'blind': sorted(s for s, p in coverage.items() if len(p) < min_pillars)}

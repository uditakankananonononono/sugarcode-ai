"""Row 635, SLO/SLI Definition: attainment of a service level objective.

windows is a list or tuple of 1 to 60 (good, total) pairs of counts for
consecutive windows. The SLI is the pooled ratio of the summed good events to
the summed total events. The objective is met when the pooled good events
times 100 are at least target_percent times the pooled total events (exact
integer arithmetic, no floats). Reported: met, the pooled SLI in permille
(rounded down), windows_met (windows that meet the target on their own),
good_total and event_total.
Caps (checked before any work): counts nonbool ints, 0 <= good <= total,
total >= 1 and total <= 1000000; target_percent a nonbool int from 1 to 100
(default 99).
NOT_CLAIMED: measuring real traffic, rolling windows, time zones, alerting,
error budget policy, customer contracts, production readiness.
"""
SCOPE = 'PARTIAL: SLO attainment arithmetic over supplied counts, no real measurement'
NOT_CLAIMED = ('measuring real traffic', 'rolling windows', 'time zones', 'alerting',
               'error budget policy', 'customer contracts', 'production readiness')

MAX_WINDOWS = 60
MAX_TOTAL = 1000000


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def slo_attainment(windows, target_percent=99):
    if type(windows) not in (list, tuple):
        raise TypeError('windows must be a list or tuple')
    if not 1 <= len(windows) <= MAX_WINDOWS:
        raise ValueError('windows must contain 1 to 60 entries')
    _int(target_percent, 1, 100, 'target_percent must be a nonbool integer between 1 and 100')
    for w in windows:
        if type(w) not in (list, tuple) or len(w) != 2:
            raise ValueError('each window must be a (good, total) pair')
        good, total = w
        _int(total, 1, MAX_TOTAL, 'total must be a nonbool integer between 1 and 1000000')
        _int(good, 0, MAX_TOTAL, 'good must be a nonbool integer between 0 and 1000000')
        if good > total:
            raise ValueError('good must not exceed total')
    good_total = sum(w[0] for w in windows)
    event_total = sum(w[1] for w in windows)
    return {
        'met': good_total * 100 >= target_percent * event_total,
        'sli_permille': good_total * 1000 // event_total,
        'windows_met': sum(1 for g, t in windows if g * 100 >= target_percent * t),
        'good_total': good_total,
        'event_total': event_total,
    }

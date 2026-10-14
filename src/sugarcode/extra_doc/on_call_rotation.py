"""Row 640, On-Call Rotation: deterministic round-robin coverage with overrides.

People take the on-call duty in list order, shift_days days each, wrapping
around. Overrides replace the person for single days (0-based day index).
Reported: the person per day, shift counts per person (days on call), and the
day indexes where the person differs from the previous day (handoffs, counted
after overrides).
Caps (checked before any work): 1 to 10 unique people (strings of 1 to 16
characters), days 1 to 60, shift_days 1 to 7, nonbool ints; override days inside
the schedule and override people from the list.
NOT_CLAIMED: time zones, holidays, fairness beyond round-robin, paging or
escalation, real calendars, production readiness.
"""
SCOPE = 'PARTIAL: round-robin day schedule with single-day overrides, no calendars'
NOT_CLAIMED = ('time zones', 'holidays', 'fairness beyond round-robin', 'paging or escalation',
               'real calendars', 'production readiness')


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def on_call_schedule(people, days, shift_days=1, overrides=None):
    if type(people) not in (list, tuple):
        raise TypeError('people must be a list or tuple')
    if not 1 <= len(people) <= 10:
        raise ValueError('people must contain between 1 and 10 entries')
    if any(type(p) is not str or not 1 <= len(p) <= 16 for p in people) or len(set(people)) != len(people):
        raise ValueError('people must be unique strings of 1 to 16 characters')
    _int(days, 1, 60, 'days must be a nonbool integer between 1 and 60')
    _int(shift_days, 1, 7, 'shift_days must be a nonbool integer between 1 and 7')
    over = {} if overrides is None else overrides
    if type(over) is not dict:
        raise TypeError('overrides must be a dict or None')
    for d, p in over.items():
        if type(d) is not int or not 0 <= d < days:
            raise ValueError('override days must be nonbool integers within the schedule')
        if type(p) is not str or p not in people:
            raise ValueError('override people must be listed people')
    n = len(people)
    sched = [over.get(d, people[(d // shift_days) % n]) for d in range(days)]
    counts = {p: 0 for p in people}
    for p in sched:
        counts[p] += 1
    handoffs = [d for d in range(1, days) if sched[d] != sched[d - 1]]
    return {'schedule': sched, 'counts': counts, 'handoffs': handoffs}

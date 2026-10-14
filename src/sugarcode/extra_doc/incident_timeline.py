"""Row 637, Incident Management: stage timing of one supplied incident.

events is a list or tuple of 1 to 4 (minute, stage) pairs. Stages are the
strings 'open', 'ack', 'mitigate' and 'resolve', in that order. The first
event must be 'open', stages must strictly advance (a stage may be skipped,
never repeated or reversed) and minutes must be non-decreasing, each a
nonbool int from 0 to 100000. Reported: state (the last stage reached),
durations (minutes from open to ack, mitigate and resolve, None for a stage
not reached), resolved, elapsed (last minute minus open minute) and breached
(elapsed greater than breach_minutes, a nonbool int from 1 to 100000,
default 60).
Caps (checked before any work): the ranges above, checked per event in order.
NOT_CLAIMED: paging people, severity triage, status pages, ticket systems,
real clocks, production readiness.
"""
SCOPE = 'PARTIAL: stage timing of supplied incident events, no paging or tickets'
NOT_CLAIMED = ('paging people', 'severity triage', 'status pages', 'ticket systems',
               'real clocks', 'production readiness')

STAGES = ('open', 'ack', 'mitigate', 'resolve')
MAX_EVENTS = 4
MAX_MINUTE = 100000


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def incident_timeline(events, breach_minutes=60):
    if type(events) not in (list, tuple):
        raise TypeError('events must be a list or tuple')
    if not 1 <= len(events) <= MAX_EVENTS:
        raise ValueError('events must contain 1 to 4 entries')
    _int(breach_minutes, 1, MAX_MINUTE, 'breach_minutes must be a nonbool integer between 1 and 100000')
    last_stage, last_minute = -1, 0
    seen = {}
    for e in events:
        if type(e) not in (list, tuple) or len(e) != 2:
            raise ValueError('each event must be a (minute, stage) pair')
        minute, stage = e
        _int(minute, 0, MAX_MINUTE, 'minute must be a nonbool integer between 0 and 100000')
        if type(stage) is not str or stage not in STAGES:
            raise ValueError('stage must be open, ack, mitigate or resolve')
        idx = STAGES.index(stage)
        if last_stage == -1 and idx != 0:
            raise ValueError('the first event must be open')
        if idx <= last_stage:
            raise ValueError('stages must advance')
        if minute < last_minute:
            raise ValueError('minutes must not decrease')
        seen[stage] = minute
        last_stage, last_minute = idx, minute
    start = seen['open']
    elapsed = last_minute - start
    return {
        'state': STAGES[last_stage],
        'durations': {s: (seen[s] - start if s in seen else None) for s in STAGES[1:]},
        'resolved': 'resolve' in seen,
        'elapsed': elapsed,
        'breached': elapsed > breach_minutes,
    }

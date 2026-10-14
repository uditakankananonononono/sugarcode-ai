"""Row 516 Event-Driven Architecture: exact consumer load for caller-described event flows.

The caller supplies 1 to 12 unique events (name, rate): rate an int 0 to 10**6 events per second,
and 1 to 10 unique consumers (name, subscribes, service_ms, workers): subscribes the distinct event
names it handles (possibly none), service_ms an int 1 to 10000 per event and workers an int 1 to 1000.
Offered load per consumer is the summed rate of its events; utilisation is rate * service_ms /
(1000 * workers) as an exact Fraction; a consumer is overloaded when utilisation reaches 1. Reported:
per consumer the rate and utilisation, the overloaded consumers, the events no consumer handles and
the most utilised consumer (first on ties). Caps are implementation choices, not spec values. The
model is a steady-state average only: no queueing delay, burstiness, ordering or failure is modelled.
NOT_CLAIMED: that the rates or service times are measured, that utilisation below 1 means the system
keeps up under real bursts, latency, ordering, delivery guarantees, failure handling, that an
event-driven design is the right choice, approval-gate clearance, deployment.
"""
from fractions import Fraction

NOT_CLAIMED = ('rates or service times measured', 'utilisation below 1 keeps up under real bursts',
               'latency, ordering, delivery guarantees or failure handling',
               'an event-driven design is the right choice', 'approval-gate clearance', 'deployment')


def _name(v):
    if type(v) is not str:
        raise TypeError('names must be str')
    if not 1 <= len(v) <= 40:
        raise ValueError('names must be 1 to 40 characters')


def event_load(events, consumers):
    if type(events) not in (list, tuple) or type(consumers) not in (list, tuple):
        raise TypeError('events and consumers must be a list or tuple')
    if not 1 <= len(events) <= 12:
        raise ValueError('event count must be between 1 and 12')
    if not 1 <= len(consumers) <= 10:
        raise ValueError('consumer count must be between 1 and 10')
    rates = {}
    for e in events:
        if type(e) not in (list, tuple) or len(e) != 2:
            raise ValueError('each event must be (name, rate)')
        _name(e[0])
        if type(e[1]) is not int:
            raise TypeError('rate must be nonbool int')
        if not 0 <= e[1] <= 10 ** 6:
            raise ValueError('rate must be between 0 and 1000000')
        if e[0] in rates:
            raise ValueError('event names must be unique')
        rates[e[0]] = e[1]
    rows = []
    for c in consumers:
        if type(c) not in (list, tuple) or len(c) != 4:
            raise ValueError('each consumer must be (name, subscribes, service_ms, workers)')
        name, subs, ms, workers = c
        _name(name)
        if type(subs) not in (list, tuple):
            raise TypeError('subscribes must be a list or tuple')
        if len(subs) > len(rates):
            raise ValueError('subscribes cannot hold more names than there are events')
        for s in subs:
            if type(s) is not str:
                raise TypeError('subscribes must hold str names')
            if s not in rates:
                raise ValueError('subscribes names an unknown event')
        if len(set(subs)) != len(subs):
            raise ValueError('subscribes must not repeat a name')
        if type(ms) is not int or type(workers) is not int:
            raise TypeError('service_ms and workers must be nonbool int')
        if not 1 <= ms <= 10000:
            raise ValueError('service_ms must be between 1 and 10000')
        if not 1 <= workers <= 1000:
            raise ValueError('workers must be between 1 and 1000')
        rows.append((name, tuple(subs), ms, workers))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('consumer names must be unique')
    per = []
    for name, subs, ms, workers in rows:
        rate = sum(rates[s] for s in subs)
        u = Fraction(rate * ms, 1000 * workers)
        per.append({'name': name, 'rate': rate, 'utilisation': u, 'overloaded': u >= 1})
    handled = {s for r in rows for s in r[1]}
    top = max(range(len(per)), key=lambda i: (per[i]['utilisation'], -i))
    return {'consumers': per, 'overloaded': tuple(p['name'] for p in per if p['overloaded']),
            'unhandled_events': tuple(n for n in rates if n not in handled), 'most_utilised': per[top]['name'],
            'design_validated': False, 'not_claimed': NOT_CLAIMED}

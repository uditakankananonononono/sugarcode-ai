"""Row 617, Service Discovery: finding the live instances of a service in a supplied registry.

The registry is a list or tuple of up to 50 (service, instance, heartbeat)
triples. An instance of the asked service is live when now - heartbeat <= ttl
and stale otherwise. Reported: live and stale instance names (sorted), the age
of each instance of that service, and whether any live instance was found.
Caps (checked before any work): service and instance names are strings of 1 to
16 characters, heartbeat and now are nonbool ints from 0 to 1000000, ttl is a
nonbool int from 1 to 1000000 (default 30), a (service, instance) pair appears
once, and no heartbeat is after now.
NOT_CLAIMED: network lookup, DNS, health probes, load balancing, registration
or deregistration, consistency between registry replicas, production readiness.
"""
SCOPE = 'PARTIAL: heartbeat-age lookup in a supplied in-memory registry, no network or health probes'
NOT_CLAIMED = ('network lookup', 'DNS', 'health probes', 'load balancing',
               'registration or deregistration', 'consistency between registry replicas',
               'production readiness')

MAX_ENTRIES = 50
MAX_TIME = 1000000


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def _name(v, msg):
    if type(v) is not str or not 1 <= len(v) <= 16:
        raise ValueError(msg)


def discover(registry, service, now, ttl=30):
    if type(registry) not in (list, tuple):
        raise TypeError('registry must be a list or tuple')
    if len(registry) > MAX_ENTRIES:
        raise ValueError('registry must contain at most 50 entries')
    _name(service, 'service must be a string of 1 to 16 characters')
    _int(now, 0, MAX_TIME, 'now must be a nonbool integer between 0 and 1000000')
    _int(ttl, 1, MAX_TIME, 'ttl must be a nonbool integer between 1 and 1000000')
    seen = set()
    for e in registry:
        if type(e) not in (list, tuple) or len(e) != 3:
            raise ValueError('each entry must be a (service, instance, heartbeat) triple')
        s, i, beat = e
        _name(s, 'service names must be strings of 1 to 16 characters')
        _name(i, 'instance names must be strings of 1 to 16 characters')
        _int(beat, 0, MAX_TIME, 'heartbeat must be a nonbool integer between 0 and 1000000')
        if (s, i) in seen:
            raise ValueError('duplicate instance for a service')
        seen.add((s, i))
        if beat > now:
            raise ValueError('heartbeat is after now')
    ages = {i: now - beat for s, i, beat in registry if s == service}
    live = sorted(i for i, a in ages.items() if a <= ttl)
    stale = sorted(i for i, a in ages.items() if a > ttl)
    return {'live': live, 'stale': stale, 'ages': ages, 'found': bool(live)}

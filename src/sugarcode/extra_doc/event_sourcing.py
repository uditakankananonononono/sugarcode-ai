"""Row 648, Event Sourcing: state as a fold over an append-only event log.

Events are ('add', sku, qty), ('remove', sku, qty) or ('clear',). replay folds the
log (or its first upto events) into a stock dict and reports the version (events
applied). Removing more than is present is an inconsistent log and raises.
append adds one event with optimistic concurrency: expected_version must equal
the current log length, and the extended log must still replay.
Caps (checked before any work): at most 100 events, skus strings of 1 to 16
characters, qty nonbool ints from 1 to 1000, upto a nonbool int from 0 to len.
NOT_CLAIMED: durable storage, snapshots, event schema versioning, projections
beyond one stock map, concurrency control beyond one version check, production
readiness.
"""
SCOPE = 'PARTIAL: in-memory log fold for one stock aggregate with a version check'
NOT_CLAIMED = ('durable storage', 'snapshots', 'event schema versioning', 'other projections',
               'concurrency control beyond a version check', 'production readiness')


def _event(e):
    if type(e) not in (list, tuple) or not e or type(e[0]) is not str or e[0] not in ('add', 'remove', 'clear'):
        raise ValueError('each event must be add, remove or clear')
    if e[0] == 'clear':
        if len(e) != 1:
            raise ValueError('clear takes no arguments')
        return
    if len(e) != 3:
        raise ValueError('add and remove take a sku and a quantity')
    if type(e[1]) is not str or not 1 <= len(e[1]) <= 16:
        raise ValueError('sku must be a string of 1 to 16 characters')
    if type(e[2]) is not int or not 1 <= e[2] <= 1000:
        raise ValueError('quantity must be a nonbool integer between 1 and 1000')


def _check(events):
    if type(events) not in (list, tuple):
        raise TypeError('events must be a list or tuple')
    if len(events) > 100:
        raise ValueError('events must contain at most 100 entries')
    for e in events:
        _event(e)


def replay(events, upto=None):
    _check(events)
    if upto is None:
        upto = len(events)
    if type(upto) is not int or not 0 <= upto <= len(events):
        raise ValueError('upto must be a nonbool integer between 0 and the number of events')
    stock = {}
    for i, e in enumerate(events[:upto]):
        if e[0] == 'clear':
            stock = {}
        elif e[0] == 'add':
            stock[e[1]] = stock.get(e[1], 0) + e[2]
        else:
            left = stock.get(e[1], 0) - e[2]
            if left < 0:
                raise ValueError('remove exceeds quantity at event %d' % i)
            if left:
                stock[e[1]] = left
            else:
                stock.pop(e[1], None)
    return {'state': stock, 'version': upto}


def append(events, event, expected_version):
    _check(events)
    _event(event)
    if type(expected_version) is not int or expected_version < 0:
        raise ValueError('expected_version must be a nonbool integer of at least 0')
    if expected_version != len(events):
        raise ValueError('version conflict: expected %d, found %d' % (expected_version, len(events)))
    extended = list(events) + [event]
    replay(extended)
    return extended

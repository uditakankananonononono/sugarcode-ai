"""Row 862, Historical Thinking - Contextualizes: neighbours of an event in time.

history_context takes events, a list or tuple of 2 to 8 (name, year) tuples,
focus, a name, and window, a nonbool int from 1 to 100 (default 10). name is a
printable ASCII string of 1 to 12 characters (control characters are refused),
distinct across events. year is a nonbool int from 1 to 2100. focus must be
the name of one of the events.
Returns focus, year (the focus event's year), before (the events earlier than
the focus by 1 to window years, as (name, gap) with the smallest gap first and
ties by name), after (the same for later events), same_year (the names of the
other events in the focus year, sorted), outside (how many events are more than
window years away) and rank (1 plus the number of events strictly earlier than
the focus).
Checks, in this order: window, events type, events size, each event (shape,
name, year), distinct names, focus text, focus membership.
NOT_CLAIMED: real historical thinking, source criticism, causation, accuracy of
supplied dates, production readiness.
"""

SCOPE = 'PARTIAL: orders supplied events around a supplied one by year gap, no history is interpreted'
NOT_CLAIMED = ('real historical thinking', 'source criticism', 'causation',
               'accuracy of supplied dates', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def history_context(events, focus, window=10):
    if type(window) is not int or not 1 <= window <= 100:
        raise ValueError('window must be a nonbool integer between 1 and 100')
    if type(events) not in (list, tuple):
        raise TypeError('events must be a list or tuple')
    if not 2 <= len(events) <= 8:
        raise ValueError('events must contain 2 to 8 entries')
    rows = []
    for e in events:
        if type(e) not in (list, tuple) or len(e) != 2:
            raise ValueError('each event must be a (name, year) tuple')
        name, year = e
        if not _label(name):
            raise ValueError('each name must be a printable ASCII string of 1 to 12 characters')
        if type(year) is not int or not 1 <= year <= 2100:
            raise ValueError('year must be a nonbool integer between 1 and 2100')
        rows.append((name, year))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('names must be distinct')
    if not _label(focus):
        raise ValueError('focus must be a printable ASCII string of 1 to 12 characters')
    years = dict(rows)
    if focus not in years:
        raise ValueError('focus must name one of the events')
    fy = years[focus]
    before = sorted((fy - y, n) for n, y in rows if 0 < fy - y <= window)
    after = sorted((y - fy, n) for n, y in rows if 0 < y - fy <= window)
    return {'focus': focus, 'year': fy,
            'before': [(n, g) for g, n in before], 'after': [(n, g) for g, n in after],
            'same_year': sorted(n for n, y in rows if y == fy and n != focus),
            'outside': sum(1 for n, y in rows if abs(y - fy) > window),
            'rank': 1 + sum(1 for n, y in rows if y < fy)}

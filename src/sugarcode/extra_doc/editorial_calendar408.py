"""Row 408, Editorial Calendar: placing supplied items into weekly publication slots.

Schedules publications by week. items is a list or tuple of 0 to 60
(name, earliest) rows, each a 2-tuple or 2-list: name a str of 1 to 40
characters, distinct from every other name (compared exactly), earliest a
nonbool int from 1 to 52, the first week the item may run. per_week is a
nonbool int from 1 to 7, the slots in each week. Items are placed in
supplied order, each into the first week at or after its earliest week
that still has a free slot. Weeks run 1 to 52; an item with no free week
left is unscheduled. Reported: slots (a list of (week, name) rows in
placement order), unscheduled (names in supplied order) and last_week (the
highest week used, or None when nothing was placed). Checks, in this
order: per_week, items type, items size, then each row in order: row
shape, name, earliest, duplicate name.
NOT_CLAIMED: audience timing, content readiness, real dates, holidays,
production readiness.
"""
SCOPE = 'PARTIAL: first-free-week slot assignment over supplied items, no real dates'
NOT_CLAIMED = ('audience timing', 'content readiness', 'real dates', 'holidays',
               'production readiness')

MAX_ITEMS = 60
MAX_NAME = 40
MAX_WEEK = 52
MAX_PER_WEEK = 7


def schedule(items, per_week):
    if type(per_week) is not int or not 1 <= per_week <= MAX_PER_WEEK:
        raise ValueError('per_week must be a nonbool int from 1 to 7')
    if type(items) not in (list, tuple):
        raise TypeError('items must be a list or tuple')
    if len(items) > MAX_ITEMS:
        raise ValueError('items must hold at most 60 rows')
    seen = set()
    for row in items:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each item must be a (name, earliest) list or tuple')
        name, earliest = row
        if type(name) is not str or not 1 <= len(name) <= MAX_NAME:
            raise ValueError('names must be str of 1 to 40 characters')
        if type(earliest) is not int or not 1 <= earliest <= MAX_WEEK:
            raise ValueError('earliest must be a nonbool int from 1 to 52')
        if name in seen:
            raise ValueError('names must be distinct')
        seen.add(name)
    used = {}
    slots, unscheduled = [], []
    for name, earliest in items:
        week = earliest
        while week <= MAX_WEEK and used.get(week, 0) >= per_week:
            week += 1
        if week > MAX_WEEK:
            unscheduled.append(name)
        else:
            used[week] = used.get(week, 0) + 1
            slots.append((week, name))
    last = max((week for week, _ in slots), default=None)
    return {'slots': slots, 'unscheduled': unscheduled, 'last_week': last}

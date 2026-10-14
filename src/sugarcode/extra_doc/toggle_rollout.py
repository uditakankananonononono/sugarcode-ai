"""Row 697, Feature Toggle: percentage rollout of toggles for supplied users.

toggle_rollout takes toggles, a list or tuple of 1 to 8 (name, percent) pairs,
users, a list or tuple of 0 to max_users nonbool ints from 0 to 99999, and
max_users, a nonbool int from 1 to 50 (default 10). A name is a string of 1 to
12 characters, distinct across toggles. percent is a nonbool int from 0 to
100. A user sees a toggle when user % 100 < percent, so 0 shows it to nobody
and 100 to everybody.
Returns results ((name, enabled users in input order, count) per toggle in
toggle order).
Checks, in this order: max_users, toggles type, toggles size, each pair
(shape, name, percent), duplicate names, users type, users size, each user.
NOT_CLAIMED: real traffic, user hashing quality, flag service behaviour,
rollback safety, production readiness.
"""
SCOPE = 'PARTIAL: modulo-100 percentage rule over supplied toggles and users, no traffic is served'
NOT_CLAIMED = ('real traffic', 'user hashing quality', 'flag service behaviour',
               'rollback safety', 'production readiness')


def toggle_rollout(toggles, users, max_users=10):
    if type(max_users) is not int or not 1 <= max_users <= 50:
        raise ValueError('max_users must be a nonbool integer between 1 and 50')
    if type(toggles) not in (list, tuple):
        raise TypeError('toggles must be a list or tuple')
    if not 1 <= len(toggles) <= 8:
        raise ValueError('toggles must contain 1 to 8 entries')
    rows = []
    for t in toggles:
        if type(t) not in (list, tuple) or len(t) != 2:
            raise ValueError('each toggle must be a (name, percent) pair')
        name, pct = t
        if type(name) is not str or not 1 <= len(name) <= 12:
            raise ValueError('each name must be a string of 1 to 12 characters')
        if type(pct) is not int or not 0 <= pct <= 100:
            raise ValueError('percent must be a nonbool integer between 0 and 100')
        rows.append((name, pct))
    if len({n for n, _ in rows}) != len(rows):
        raise ValueError('names must be distinct')
    if type(users) not in (list, tuple):
        raise TypeError('users must be a list or tuple')
    if len(users) > max_users:
        raise ValueError('users must contain at most max_users entries')
    for u in users:
        if type(u) is not int or not 0 <= u <= 99999:
            raise ValueError('each user must be a nonbool integer between 0 and 99999')
    results = []
    for name, pct in rows:
        on = [u for u in users if u % 100 < pct]
        results.append((name, on, len(on)))
    return {'results': results}

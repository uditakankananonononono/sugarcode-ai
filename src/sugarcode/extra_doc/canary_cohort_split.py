"""Row 624, Canary Deployment: choosing which users see the new version.

Each user name gets a fixed bucket from 0 to 99, the sum of its code points
modulo 100. A user is in the canary cohort when bucket < percent, otherwise in
the control cohort. The same name always lands in the same cohort, and raising
the percent only adds users. Reported: the canary and control names (sorted)
and each user's bucket.
Caps (checked before any work): 0 to 50 unique user names (strings of 1 to 16
characters), percent a nonbool int from 0 to 100 (default 10).
NOT_CLAIMED: a statistically even split, real traffic, health comparison,
promotion or rollback, session stickiness across renames, production readiness.
"""
SCOPE = 'PARTIAL: fixed code-point-sum bucketing of supplied user names, no real traffic'
NOT_CLAIMED = ('a statistically even split', 'real traffic', 'health comparison',
               'promotion or rollback', 'session stickiness across renames', 'production readiness')

MAX_USERS = 50


def split_cohorts(users, percent=10):
    if type(users) not in (list, tuple):
        raise TypeError('users must be a list or tuple')
    if len(users) > MAX_USERS:
        raise ValueError('users must contain at most 50 entries')
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 0 and 100')
    if any(type(u) is not str or not 1 <= len(u) <= 16 for u in users) or len(set(users)) != len(users):
        raise ValueError('user names must be unique strings of 1 to 16 characters')
    buckets = {u: sum(ord(c) for c in u) % 100 for u in users}
    return {'canary': sorted(u for u in users if buckets[u] < percent),
            'control': sorted(u for u in users if buckets[u] >= percent),
            'buckets': buckets}

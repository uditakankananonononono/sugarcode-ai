"""Row 698, Trunk-Based Development: short-lived branch check.

trunk_branches takes branches, a list or tuple of 0 to 12 (name, age_days,
commits) triples, and max_age, a nonbool int from 1 to 14 (default 2). A name
is a string of 1 to 16 characters, distinct across branches. age_days is a
nonbool int from 0 to 365 and commits a nonbool int from 0 to 500. A branch is
stale when age_days > max_age. A branch is also big when commits > 20.
Returns stale (names in input order), big (names in input order),
oldest_age (largest age_days, 0 with no branches) and ok (no stale branch).
Checks, in this order: max_age, branches type, branches size, each triple
(shape, name, age, commits), duplicate names.
NOT_CLAIMED: real repository state, merge conflicts, build health,
release readiness, production readiness.
"""
SCOPE = 'PARTIAL: age and size thresholds over supplied branch records, no repository is read'
NOT_CLAIMED = ('real repository state', 'merge conflicts', 'build health',
               'release readiness', 'production readiness')


def trunk_branches(branches, max_age=2):
    if type(max_age) is not int or not 1 <= max_age <= 14:
        raise ValueError('max_age must be a nonbool integer between 1 and 14')
    if type(branches) not in (list, tuple):
        raise TypeError('branches must be a list or tuple')
    if len(branches) > 12:
        raise ValueError('branches must contain at most 12 entries')
    rows = []
    for b in branches:
        if type(b) not in (list, tuple) or len(b) != 3:
            raise ValueError('each branch must be a (name, age_days, commits) triple')
        name, age, commits = b
        if type(name) is not str or not 1 <= len(name) <= 16:
            raise ValueError('each name must be a string of 1 to 16 characters')
        if type(age) is not int or not 0 <= age <= 365:
            raise ValueError('age_days must be a nonbool integer between 0 and 365')
        if type(commits) is not int or not 0 <= commits <= 500:
            raise ValueError('commits must be a nonbool integer between 0 and 500')
        rows.append((name, age, commits))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('names must be distinct')
    stale = [n for n, a, _ in rows if a > max_age]
    big = [n for n, _, c in rows if c > 20]
    oldest = 0
    for _, a, _ in rows:
        if a > oldest:
            oldest = a
    return {'stale': stale, 'big': big, 'oldest_age': oldest, 'ok': not stale}

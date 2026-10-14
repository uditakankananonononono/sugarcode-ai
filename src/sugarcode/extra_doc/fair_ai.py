"""Row 1951, Title: Fair AI

count_breakaways(rows): rows are (metric, group, value)
triples; metric and group strings of 1 to 16
characters; value a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each group its
breakaways (rows whose value is strictly above the
current latest of every other group seen so far), the
total breakaways, and the leader (the most
breakaways, first supplied on ties, or None when no
group breaks away).

SCOPE: PARTIAL: breakaway counting over supplied values
NOT_CLAIMED: metric selection, bias auditing,
intersectional analysis, policy drafting, production
readiness.
"""

SCOPE = 'PARTIAL: breakaway counting over supplied values'
NOT_CLAIMED = ('metric selection', 'bias auditing',
               'intersectional analysis', 'policy drafting',
               'production readiness')


def count_breakaways(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (metric, group, value) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        metric, group, value = row
        if type(metric) is not str or not 1 <= len(metric) <= 16:
            raise ValueError(f'row {i}: metric must be a string of 1 to 16 characters')
        if type(group) is not str or not 1 <= len(group) <= 16:
            raise ValueError(f'row {i}: group must be a string of 1 to 16 characters')
        if type(value) is not int or not 1 <= value <= 9:
            raise ValueError(f'row {i}: value must be a nonbool integer between 1 and 9')
    latest = {}
    order = {}
    breakaways = {}
    total = 0
    for metric, group, value in rows:
        if group not in order:
            order[group] = True
        if len(latest) >= 2 or (len(latest) == 1 and group not in latest):
            ahead = True
            for other in latest:
                if other != group and value <= latest[other]:
                    ahead = False
            if ahead:
                if group not in breakaways:
                    breakaways[group] = 0
                breakaways[group] += 1
                total += 1
        latest[group] = value
    leader = None
    for group in order:
        if group not in breakaways:
            continue
        if leader is None or breakaways[group] > breakaways[leader]:
            leader = group
    return {'total': len(rows),
            'breakaways': breakaways,
            'count': total,
            'leader': leader}

"""Row 836, Near Transfer - Applies to similar: tasks close to the taught ones.

near_transfer_pick takes taught, a list or tuple of 1 to 6 distinct nonbool
ints from 0 to 50 (positions on a similarity line), tasks, a list or tuple of
1 to 8 (name, position, score) tuples, and reach, a nonbool int from 1 to 10
(default 2). name is an ASCII string of 1 to 12 characters, distinct across
tasks. position is a nonbool int from 0 to 50 and score a nonbool int from 0
to 10.
The distance of a task is the smallest absolute difference between its
position and a taught position. A task is similar when its distance is from 1
to reach. A task at distance 0 is the taught one itself and a task beyond
reach is not similar.
Returns near (a list of (name, distance, score) for the similar tasks, closest
first and ties by name), near_total (the scores of the similar tasks added up),
taught_count (tasks at distance 0), beyond_count (tasks beyond reach) and best
(the name of the similar task with the highest score, ties to the closer then
to the smaller name, None when no task is similar).
Checks, in this order: reach, taught type, taught size, each taught position,
distinct taught, tasks type, tasks size, each task (shape, name, position,
score), distinct names.
NOT_CLAIMED: real near transfer, learner ability, true task similarity,
curriculum fit, production readiness.
"""

SCOPE = 'PARTIAL: picks supplied tasks within a reach of supplied taught positions, no learner transfers'
NOT_CLAIMED = ('real near transfer', 'learner ability', 'true task similarity',
               'curriculum fit', 'production readiness')


def near_transfer_pick(taught, tasks, reach=2):
    if type(reach) is not int or not 1 <= reach <= 10:
        raise ValueError('reach must be a nonbool integer between 1 and 10')
    if type(taught) not in (list, tuple):
        raise TypeError('taught must be a list or tuple')
    if not 1 <= len(taught) <= 6:
        raise ValueError('taught must contain 1 to 6 entries')
    for t in taught:
        if type(t) is not int or not 0 <= t <= 50:
            raise ValueError('each taught position must be a nonbool integer between 0 and 50')
    if len(set(taught)) != len(taught):
        raise ValueError('taught positions must be distinct')
    if type(tasks) not in (list, tuple):
        raise TypeError('tasks must be a list or tuple')
    if not 1 <= len(tasks) <= 8:
        raise ValueError('tasks must contain 1 to 8 entries')
    rows = []
    for tk in tasks:
        if type(tk) not in (list, tuple) or len(tk) != 3:
            raise ValueError('each task must be a (name, position, score) tuple')
        name, position, score = tk
        if type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12:
            raise ValueError('each name must be an ASCII string of 1 to 12 characters')
        if type(position) is not int or not 0 <= position <= 50:
            raise ValueError('position must be a nonbool integer between 0 and 50')
        if type(score) is not int or not 0 <= score <= 10:
            raise ValueError('score must be a nonbool integer between 0 and 10')
        rows.append((name, position, score))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('names must be distinct')
    near = []
    same = beyond = 0
    for name, position, score in rows:
        distance = min(abs(position - t) for t in taught)
        if distance == 0:
            same += 1
        elif distance <= reach:
            near.append((distance, name, score))
        else:
            beyond += 1
    near.sort(key=lambda r: (r[0], r[1]))
    best = None
    if near:
        best = min(near, key=lambda r: (-r[2], r[0], r[1]))[1]
    return {'near': [(n, d, s) for d, n, s in near],
            'near_total': sum(r[2] for r in near), 'taught_count': same,
            'beyond_count': beyond, 'best': best}

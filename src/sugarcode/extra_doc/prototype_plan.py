"""Row 373 Prototype Development - Creates testable versions: supplied-task build schedule.

Tasks are (label, days, dependencies) with days an int 1..30 and dependencies a
list or tuple of other task indices. Returns a build order (Kahn, smallest ready
index first), each task's earliest finish with unlimited parallel workers and the
total duration (the longest dependency path). A dependency cycle is an error.
1 to 16 tasks, up to 8 dependencies each, labels unique strings of 1 to 40
characters with no control, format, private-use, surrogate or unassigned
characters. Caps are implementation choices.
NOT_CLAIMED: that a prototype was built or is testable, accuracy of the supplied
durations, staffing, quality, user acceptance or product viability.
"""
import unicodedata


def _label_ok(s):
    return type(s) is str and 1 <= len(s) <= 40 and all(unicodedata.category(c)[0] != 'C' for c in s)


def plan_prototype(tasks):
    if type(tasks) not in (list, tuple):
        raise TypeError('tasks must be a list or tuple')
    n = len(tasks)
    if not 1 <= n <= 16:
        raise ValueError('task count must be between 1 and 16')
    if any(type(t) not in (list, tuple) or len(t) != 3 for t in tasks):
        raise ValueError('tasks must be label days dependencies triples')
    if any(not _label_ok(t[0]) for t in tasks):
        raise ValueError('labels must be 1 to 40 characters without control or unassigned characters')
    if any(type(t[1]) is not int or not 1 <= t[1] <= 30 for t in tasks):
        raise ValueError('days must be nonbool integers 1 through 30')
    if any(type(t[2]) not in (list, tuple) or len(t[2]) > 8 for t in tasks):
        raise ValueError('dependencies must be lists or tuples of at most eight indices')
    if any(type(d) is not int or not 0 <= d < n for t in tasks for d in t[2]):
        raise ValueError('dependencies must be nonbool valid task indices')
    if any(i in t[2] or len(set(t[2])) != len(t[2]) for i, t in enumerate(tasks)):
        raise ValueError('dependencies must be unique and not self-referencing')
    if len({t[0] for t in tasks}) != n:
        raise ValueError('labels must be unique')
    done, order, finish = set(), [], [0] * n
    while len(order) < n:
        ready = [i for i in range(n) if i not in done and all(d in done for d in tasks[i][2])]
        if not ready:
            raise ValueError('dependencies contain a cycle')
        i = ready[0]
        finish[i] = max((finish[d] for d in tasks[i][2]), default=0) + tasks[i][1]
        done.add(i)
        order.append(i)
    return {'order': order, 'labels': [tasks[i][0] for i in order], 'finish': finish,
            'total_days': max(finish), 'prototype_built': False}

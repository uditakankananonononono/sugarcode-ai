"""Row 837, Far Transfer - Applies to different: tasks sharing no taught feature.

far_transfer_check takes taught, a list or tuple of 1 to 6 ASCII strings of 1
to 12 characters, distinct, naming the features of the taught work, tasks, a
list or tuple of 1 to 8 (name, features, score) tuples, and pass_score, a
nonbool int from 1 to 10 (default 6). name is an ASCII string of 1 to 12
characters, distinct across tasks. features is a list or tuple of 1 to 4 ASCII
strings of 1 to 12 characters, distinct within the tuple. score is a nonbool
int from 0 to 10.
A task is different when none of its features is in taught. A task sharing any
feature is not different.
Returns far (the names of the different tasks, in input order), far_passed
(how many of them have a score of at least pass_score), shared (how many tasks
share a feature), far_percent (far_passed as a percent of the different tasks,
rounded down, 0 when there are none) and reached (True when more than half of
the different tasks pass, compared exactly).
Checks, in this order: pass_score, taught type, taught size, each taught
entry, distinct taught, tasks type, tasks size, each task (shape, name,
features type, features size, each feature, distinct features, score),
distinct names.
NOT_CLAIMED: real far transfer, learner ability, true task difference,
curriculum fit, production readiness.
"""

SCOPE = 'PARTIAL: scores supplied tasks that share no supplied taught feature, no learner transfers'
NOT_CLAIMED = ('real far transfer', 'learner ability', 'true task difference',
               'curriculum fit', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and 1 <= len(x) <= 12


def far_transfer_check(taught, tasks, pass_score=6):
    if type(pass_score) is not int or not 1 <= pass_score <= 10:
        raise ValueError('pass_score must be a nonbool integer between 1 and 10')
    if type(taught) not in (list, tuple):
        raise TypeError('taught must be a list or tuple')
    if not 1 <= len(taught) <= 6:
        raise ValueError('taught must contain 1 to 6 entries')
    for t in taught:
        if not _label(t):
            raise ValueError('each taught entry must be an ASCII string of 1 to 12 characters')
    if len(set(taught)) != len(taught):
        raise ValueError('taught entries must be distinct')
    if type(tasks) not in (list, tuple):
        raise TypeError('tasks must be a list or tuple')
    if not 1 <= len(tasks) <= 8:
        raise ValueError('tasks must contain 1 to 8 entries')
    rows = []
    for tk in tasks:
        if type(tk) not in (list, tuple) or len(tk) != 3:
            raise ValueError('each task must be a (name, features, score) tuple')
        name, features, score = tk
        if not _label(name):
            raise ValueError('each name must be an ASCII string of 1 to 12 characters')
        if type(features) not in (list, tuple):
            raise ValueError('features must be a list or tuple')
        if not 1 <= len(features) <= 4:
            raise ValueError('features must contain 1 to 4 entries')
        for x in features:
            if not _label(x):
                raise ValueError('each feature must be an ASCII string of 1 to 12 characters')
        if len(set(features)) != len(features):
            raise ValueError('features must be distinct')
        if type(score) is not int or not 0 <= score <= 10:
            raise ValueError('score must be a nonbool integer between 0 and 10')
        rows.append((name, features, score))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('names must be distinct')
    far = [(n, s) for n, f, s in rows if not any(x in taught for x in f)]
    passed = sum(1 for _, s in far if s >= pass_score)
    return {'far': [n for n, _ in far], 'far_passed': passed,
            'shared': len(rows) - len(far),
            'far_percent': passed * 100 // len(far) if far else 0,
            'reached': passed * 2 > len(far)}

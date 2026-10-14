"""Row 833, Diagnostic Assessment - Identifies needs: skills below a threshold.

diagnostic_gaps takes items, a list or tuple of 1 to 8 (skill, asked, correct)
tuples, and threshold, a nonbool int from 1 to 100 (default 50). A skill is an
ASCII string of 1 to 12 characters, distinct across items. asked is a nonbool
int from 1 to 20 and correct a nonbool int from 0 to asked.
A skill is a need when its exact share correct / asked is below threshold
percent.
Returns needs (a list of (skill, percent) for every need, percent rounded
down, ordered by the exact share with the lowest first and ties by skill name),
secure (how many skills are not needs) and clear (True when there are no
needs).
Checks, in this order: threshold, items type, items size, each item (shape,
skill, asked, correct), distinct skills.
NOT_CLAIMED: real learner needs, test validity, curriculum coverage,
instructional fit, production readiness.
"""
from functools import cmp_to_key

SCOPE = 'PARTIAL: ranks supplied skill tallies against a threshold, no learner is diagnosed'
NOT_CLAIMED = ('real learner needs', 'test validity', 'curriculum coverage',
               'instructional fit', 'production readiness')


def _by_share(x, y):
    left = x[2] * y[1]
    right = y[2] * x[1]
    if left != right:
        return -1 if left < right else 1
    return -1 if x[0] < y[0] else (1 if x[0] > y[0] else 0)


def diagnostic_gaps(items, threshold=50):
    if type(threshold) is not int or not 1 <= threshold <= 100:
        raise ValueError('threshold must be a nonbool integer between 1 and 100')
    if type(items) not in (list, tuple):
        raise TypeError('items must be a list or tuple')
    if not 1 <= len(items) <= 8:
        raise ValueError('items must contain 1 to 8 entries')
    rows = []
    for it in items:
        if type(it) not in (list, tuple) or len(it) != 3:
            raise ValueError('each item must be a (skill, asked, correct) tuple')
        skill, asked, correct = it
        if type(skill) is not str or not skill.isascii() or not 1 <= len(skill) <= 12:
            raise ValueError('each skill must be an ASCII string of 1 to 12 characters')
        if type(asked) is not int or not 1 <= asked <= 20:
            raise ValueError('asked must be a nonbool integer between 1 and 20')
        if type(correct) is not int or not 0 <= correct <= asked:
            raise ValueError('correct must be a nonbool integer between 0 and asked')
        rows.append((skill, asked, correct))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('skills must be distinct')
    gaps = [r for r in rows if r[2] * 100 < threshold * r[1]]
    gaps.sort(key=cmp_to_key(_by_share))
    return {'needs': [(s, c * 100 // a) for s, a, c in gaps],
            'secure': len(rows) - len(gaps), 'clear': not gaps}

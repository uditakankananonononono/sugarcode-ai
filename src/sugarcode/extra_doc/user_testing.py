"""Row 374 User Testing - Gathers feedback systematically: supplied-session task tally.

Observations are (participant, task, outcome) with outcome one of pass, assist,
fail. Each participant may appear once per task. Returns per-task counts and the
exact pass rate (pass / observations of that task) in first-appearance order,
and the tasks with pass rate below one ranked by lowest pass rate then first
appearance. 1 to 64 observations; participant and task are strings of 1 to 40
characters with no control, format, private-use, surrogate or unassigned
characters. Caps are implementation choices.
NOT_CLAIMED: that any session took place, accuracy of the supplied outcomes,
sample representativeness, statistical significance, usability or product fit.
"""
import unicodedata
from fractions import Fraction

OUTCOMES = ('pass', 'assist', 'fail')


def _ok(s):
    return type(s) is str and 1 <= len(s) <= 40 and all(unicodedata.category(c)[0] != 'C' for c in s)


def tally_sessions(observations):
    if type(observations) not in (list, tuple):
        raise TypeError('observations must be a list or tuple')
    if not 1 <= len(observations) <= 64:
        raise ValueError('observation count must be between 1 and 64')
    if any(type(o) not in (list, tuple) or len(o) != 3 for o in observations):
        raise ValueError('observations must be participant task outcome triples')
    if any(not _ok(o[0]) or not _ok(o[1]) for o in observations):
        raise ValueError('participants and tasks must be 1 to 40 characters without control or unassigned characters')
    if any(type(o[2]) is not str or o[2] not in OUTCOMES for o in observations):
        raise ValueError('outcome must be pass, assist or fail')
    if len({(o[0], o[1]) for o in observations}) != len(observations):
        raise ValueError('each participant may appear once per task')
    tasks = {}
    for _, t, out in observations:
        row = tasks.setdefault(t, {'task': t, 'pass': 0, 'assist': 0, 'fail': 0})
        row[out] += 1
    rows = []
    for row in tasks.values():
        row['observations'] = row['pass'] + row['assist'] + row['fail']
        row['pass_rate'] = Fraction(row['pass'], row['observations'])
        rows.append(row)
    weak = sorted((i for i, r in enumerate(rows) if r['pass_rate'] < 1), key=lambda i: (rows[i]['pass_rate'], i))
    return {'tasks': rows, 'weak_tasks': [rows[i]['task'] for i in weak], 'sessions_validated': False}

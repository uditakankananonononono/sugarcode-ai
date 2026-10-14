"""Row 832, Summative Assessment - Assesses learning: weighted final grade.

summative_grade takes parts, a list or tuple of 1 to 6 (name, weight, earned,
possible) tuples, and pass_mark, a nonbool int from 1 to 100 (default 60). A
name is an ASCII string of 1 to 12 characters, distinct across parts. weight
is a nonbool int from 1 to 100 and the weights must add up to exactly 100.
possible is a nonbool int from 1 to 100 and earned a nonbool int from 0 to
possible.
Each part contributes weight * earned / possible percentage points. The total
is computed exactly, then rounded down where reported.
Returns breakdown ((name, contribution_tenths) per part, contribution in tenths
of a point rounded down), percent_tenths (the total in tenths of a point,
rounded down), grade (A at 90 or more, B at 80, C at 70, D at 60, else F,
compared on the exact total) and passed (the exact total is at least
pass_mark).
Checks, in this order: pass_mark, parts type, parts size, each part (shape,
name, weight, possible, earned), distinct names, weight sum.
NOT_CLAIMED: real learning, test validity, curriculum coverage, grading
fairness, production readiness.
"""
from fractions import Fraction

SCOPE = 'PARTIAL: exact weighted total and letter band of supplied part scores, no learner is assessed'
NOT_CLAIMED = ('real learning', 'test validity', 'curriculum coverage',
               'grading fairness', 'production readiness')


def summative_grade(parts, pass_mark=60):
    if type(pass_mark) is not int or not 1 <= pass_mark <= 100:
        raise ValueError('pass_mark must be a nonbool integer between 1 and 100')
    if type(parts) not in (list, tuple):
        raise TypeError('parts must be a list or tuple')
    if not 1 <= len(parts) <= 6:
        raise ValueError('parts must contain 1 to 6 entries')
    rows = []
    for p in parts:
        if type(p) not in (list, tuple) or len(p) != 4:
            raise ValueError('each part must be a (name, weight, earned, possible) tuple')
        name, weight, earned, possible = p
        if type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12:
            raise ValueError('each name must be an ASCII string of 1 to 12 characters')
        if type(weight) is not int or not 1 <= weight <= 100:
            raise ValueError('weight must be a nonbool integer between 1 and 100')
        if type(possible) is not int or not 1 <= possible <= 100:
            raise ValueError('possible must be a nonbool integer between 1 and 100')
        if type(earned) is not int or not 0 <= earned <= possible:
            raise ValueError('earned must be a nonbool integer between 0 and possible')
        rows.append((name, weight, earned, possible))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('names must be distinct')
    if sum(r[1] for r in rows) != 100:
        raise ValueError('weights must add up to 100')
    shares = [(n, Fraction(w * e, pos)) for n, w, e, pos in rows]
    total = sum(s for _, s in shares)
    if total >= 90:
        grade = 'A'
    elif total >= 80:
        grade = 'B'
    elif total >= 70:
        grade = 'C'
    elif total >= 60:
        grade = 'D'
    else:
        grade = 'F'
    return {'breakdown': [(n, (s * 10).__floor__()) for n, s in shares],
            'percent_tenths': (total * 10).__floor__(), 'grade': grade,
            'passed': total >= pass_mark}

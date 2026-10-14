"""Row 354 Design Sprint: finite prototype-scope selection under a sprint time box (exact).

Given candidate prototype features (id, value, hours) and a time box of
days x hours_per_day, choose the subset with the largest total value whose total
hours fit the box. Brute force over all subsets (at most 12 features, 4096
subsets); ties go to fewer total hours, then to fewer features, then to the
lexicographically smallest index tuple. days is an int 1 to 5; hours_per_day,
values and hours are nonbool int or Fraction (no float), numerator and
denominator at most 32 bits, nonnegative (hours_per_day positive). Ids are 1 to
40 character strings. Caps are implementation choices, not spec values.
Values are caller-supplied numbers; nothing is estimated from a prototype.
NOT_CLAIMED: that the chosen scope is the right problem or solution, user testing
or interview results, usability, desirability, feasibility, effort estimate
accuracy, team capacity or schedule realism, a real sprint outcome, deployment.
"""
from fractions import Fraction
from itertools import combinations

NOT_CLAIMED = ('right problem or solution', 'user testing results', 'usability', 'desirability',
               'feasibility', 'effort estimate accuracy', 'team capacity or schedule realism',
               'real sprint outcome', 'deployment')


def _number(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length() > 32:
            raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length() > 32 or v.denominator.bit_length() > 32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def plan_sprint(features, hours_per_day, days=5):
    if type(features) not in (list, tuple):
        raise TypeError('features must be a list or tuple')
    if not 1 <= len(features) <= 12:
        raise ValueError('feature count must be between 1 and 12')
    if type(days) is not int:
        raise TypeError('days must be nonbool int')
    if not 1 <= days <= 5:
        raise ValueError('days must be between 1 and 5')
    per_day = _number(hours_per_day)
    if per_day <= 0:
        raise ValueError('hours per day must be positive')
    rows = []
    for f in features:
        if type(f) not in (list, tuple) or len(f) != 3:
            raise ValueError('each feature must be (id, value, hours)')
        if type(f[0]) is not str:
            raise TypeError('feature ids must be str')
        if not 1 <= len(f[0]) <= 40:
            raise ValueError('feature ids must be 1 to 40 characters')
        rows.append((f[0], _number(f[1]), _number(f[2])))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('feature ids must be unique')
    if any(r[1] < 0 or r[2] < 0 for r in rows):
        raise ValueError('values and hours must be nonnegative')
    capacity = per_day * days
    best = None
    for size in range(len(rows) + 1):
        for combo in combinations(range(len(rows)), size):
            hours = sum((rows[i][2] for i in combo), Fraction(0))
            if hours > capacity:
                continue
            value = sum((rows[i][1] for i in combo), Fraction(0))
            key = (-value, hours, size, combo)
            if best is None or key < best:
                best = key
    neg_value, hours, size, combo = best
    return {'chosen': [rows[i][0] for i in combo], 'chosen_indices': list(combo), 'total_value': -neg_value,
            'total_hours': hours, 'capacity_hours': capacity, 'spare_hours': capacity - hours,
            'deferred': [r[0] for i, r in enumerate(rows) if i not in combo],
            'sprint_outcome_validated': False, 'not_claimed': NOT_CLAIMED}

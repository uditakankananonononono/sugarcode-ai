"""Row 129 Figure Design - Creates publication-quality visualizations.

PARTIAL: exact bounded 1-2-5 numeric-axis tick planning, no figure rendering.
Input exact dict bounds and target. Bounds is an exact two-value list of exact
integers -9..9 with lower < upper. Target is an exact integer 2..6. Candidate
steps are 1/10, 2/10, 5/10, 1, 2, 5, 10, 20, 50. For each step, enclose both
bounds with grid endpoints floor(lower/step)*step and ceil(upper/step)*step;
keep candidates with 2..20 ticks. Select by lexicographic key: absolute tick
count-target gap, total excess coverage, smaller step. Return step reduced pair,
ticks ordered reduced pairs, excess reduced pair, claims three False booleans.
No labels, pixel layout, readability or publication quality is assessed.
NOT_CLAIMED: figure rendering, publication quality, production readiness.
"""
from fractions import Fraction
SCOPE = 'PARTIAL: exact supplied-bound finite 1-2-5 axis tick planning only'
NOT_CLAIMED = ('figure rendering', 'publication quality', 'production readiness')


def plan(data):
    if type(data) is not dict or set(data) != {'bounds', 'target'}:
        raise ValueError('exact dict with bounds and target required')
    bounds = data['bounds']
    if type(bounds) is not list or len(bounds) != 2:
        raise ValueError('bounds must be an exact two-value list')
    for v in bounds:
        if type(v) is not int or not -9 <= v <= 9:
            raise ValueError('bounds must be exact integers -9..9')
    lower, upper = bounds
    if lower >= upper:
        raise ValueError('lower bound must be less than upper bound')
    target = data['target']
    if type(target) is not int or not 2 <= target <= 6:
        raise ValueError('target must be an exact integer 2..6')
    candidates = []
    for exponent in (-1, 0, 1):
        for base in (1, 2, 5):
            step = Fraction(base)*Fraction(10)**exponent
            left = lower//step
            right = -((-upper)//step)
            count = right-left+1
            if 2 <= count <= 20:
                excess = (right-left)*step-(upper-lower)
                candidates.append(((abs(count-target), excess, step), left, right))
    key, left, right = min(candidates)
    step = key[2]
    ticks = [i*step for i in range(left, right+1)]
    return {'step': [step.numerator, step.denominator], 'ticks': [[t.numerator, t.denominator] for t in ticks], 'excess': [key[1].numerator, key[1].denominator], 'claims': [False, False, False]}

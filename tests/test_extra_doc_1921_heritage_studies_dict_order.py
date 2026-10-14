"""Dict-order oracle pins for row 1921, Title: Heritage Studies.

Additive pins on top of the graded tests for row 1921: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import heritage_studies as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    baseline = {}
    declines = {}
    for site, region, care in rows:
        if site not in baseline:
            baseline[site] = care
            declines[site] = 0
        elif care < baseline[site]:
            declines[site] += 1
    steady = sorted(s for s in declines if declines[s] == 0)
    worst = None
    if declines:
        top = max(declines.values())
        supply = list(dict.fromkeys(s for s, _r, _c in rows))
        worst = next(s for s in supply if declines.get(s) == top)
    return {'total': len(rows), 'declines': declines,
            'steady': steady, 'worst': worst}


def _pin_order(rows):
    got = mod.gauge_care(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71921)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)

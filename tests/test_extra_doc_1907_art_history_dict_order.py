"""Dict-order oracle pins for row 1907, Title: Art History.

Additive pins on top of the graded tests for row 1907: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import art_history as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    tops = {}
    masters = {}
    for work, period, merit in rows:
        if period not in tops or merit > tops[period]:
            tops[period] = merit
            masters[period] = work
    celebrated = sorted(p for p in tops if tops[p] >= 8)
    thin = sorted(p for p in tops if tops[p] <= 3)
    top = max(tops.values())
    supply = list(dict.fromkeys(p for _w, p, _m in rows))
    finest = next(p for p in supply if tops[p] == top)
    return {'total': len(rows), 'masters': masters,
            'celebrated': celebrated, 'thin': thin, 'finest': finest}


def _pin_order(rows):
    got = mod.crown_periods(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71907)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)

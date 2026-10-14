"""Dict-order oracle pins for row 1898, Title: Theology.

Additive pins on top of the graded tests for row 1898: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import theology as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    first = {}
    last = {}
    for doctrine, school, weight in rows:
        if doctrine not in first:
            first[doctrine] = weight
        last[doctrine] = weight
    drifts = {}
    for doctrine in first:
        drifts[doctrine] = last[doctrine] - first[doctrine]
    hardened = sorted(d for d in drifts if drifts[d] >= 3)
    softened = sorted(d for d in drifts if drifts[d] <= -3)
    top = max(abs(v) for v in drifts.values())
    supply = list(dict.fromkeys(d for d, _s, _w in rows))
    volatile = next(d for d in supply if abs(drifts[d]) == top)
    return {'total': len(rows), 'drifts': drifts, 'hardened': hardened,
            'softened': softened, 'volatile': volatile}


def _pin_order(rows):
    got = mod.weigh_doctrines(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71898)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)

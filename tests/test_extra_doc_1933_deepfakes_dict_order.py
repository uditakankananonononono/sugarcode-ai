"""Dict-order oracle pins for row 1933, Title: Deepfakes.

Additive pins on top of the graded tests for row 1933: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import deepfakes as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    firsts = {}
    anchors = {}
    supplied = {}
    for frame, model, score in rows:
        if model not in firsts:
            firsts[model] = score
            anchors[model] = 0
            supplied[model] = 0
        supplied[model] += 1
        if score == firsts[model]:
            anchors[model] += 1
    steady = sorted(m for m in anchors if anchors[m] == supplied[m])
    firmest = None
    if anchors:
        top = max(anchors.values())
        supply = list(dict.fromkeys(m for _f, m, _s in rows))
        firmest = next(m for m in supply if anchors.get(m) == top)
    return {'total': len(rows), 'anchors': anchors,
            'steady': steady, 'firmest': firmest}


def _pin_order(rows):
    got = mod.anchor_counts(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71933)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)

"""Dict-order oracle pins for row 1922, Title: Digital Humanities.

Additive pins on top of the graded tests for row 1922: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import digital_humanities as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    counts = {}
    nines = {}
    for corpus, tool, gain in rows:
        if corpus not in counts:
            counts[corpus] = 0
            nines[corpus] = 0
        counts[corpus] += 1
        if gain == 9:
            nines[corpus] += 1
    polished = sorted(c for c in counts
                      if counts[c] >= 2 and nines[c] == counts[c])
    most_nines = None
    if nines:
        top = max(nines.values())
        supply = list(dict.fromkeys(c for c, _t, _g in rows))
        most_nines = next(c for c in supply if nines.get(c) == top)
    return {'total': len(rows), 'nines': nines,
            'polished': polished, 'most_nines': most_nines}


def _pin_order(rows):
    got = mod.mark_flawless(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71922)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)

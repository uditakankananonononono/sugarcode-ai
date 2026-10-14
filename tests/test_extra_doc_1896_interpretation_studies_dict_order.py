"""Dict-order oracle pins for row 1896, Title: Interpretation Studies.

Additive pins on top of the graded tests for row 1896: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import interpretation_studies as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    readings = {}
    for text, reader, clarity in rows:
        if text not in readings:
            readings[text] = []
        readings[text].append(clarity)
    medians = {}
    for text in readings:
        vals = sorted(readings[text])
        medians[text] = vals[(len(vals) - 1) // 2]
    lucid = sorted(t for t in medians if medians[t] >= 7)
    murky = sorted(t for t in medians if medians[t] <= 3)
    top = max(medians.values())
    supply = list(dict.fromkeys(t for t, _r, _c in rows))
    clearest = next(t for t in supply if medians[t] == top)
    return {'total': len(rows), 'medians': medians, 'lucid': lucid,
            'murky': murky, 'clearest': clearest}


def _pin_order(rows):
    got = mod.gauge_clarity(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71896)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)

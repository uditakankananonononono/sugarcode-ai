"""Dict-order oracle pins for row 1895, Title: Translation Studies.

Additive pins on top of the graded tests for row 1895: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import translation_studies as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    counts = {}
    low = {}
    high = {}
    for passage, translator, fidelity in rows:
        if passage not in counts:
            counts[passage] = 0
            low[passage] = fidelity
            high[passage] = fidelity
        counts[passage] += 1
        if fidelity < low[passage]:
            low[passage] = fidelity
        if fidelity > high[passage]:
            high[passage] = fidelity
    consensus = sorted(p for p in counts if counts[p] >= 2 and high[p] == low[p])
    disputed = sorted(p for p in counts if high[p] - low[p] >= 6)
    polarizing = None
    if counts:
        top = max(high[p] - low[p] for p in counts)
        supply = list(dict.fromkeys(p for p, _t, _f in rows))
        polarizing = next(p for p in supply
                          if p in counts and high[p] - low[p] == top)
    return {'total': len(rows), 'counts': counts, 'consensus': consensus,
            'disputed': disputed, 'polarizing': polarizing}


def _pin_order(rows):
    got = mod.assess_translations(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71895)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)

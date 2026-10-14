"""Dict-order oracle pins for row 1891, Title: Historical Linguistics.

Additive pins on top of the graded tests for row 1891: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import historical_linguistics as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    first = {}
    latest = {}
    for word, stage, score in rows:
        if word not in first:
            first[word] = score
        latest[word] = score
    drift = {}
    for word in first:
        drift[word] = latest[word] - first[word]
    risen = sorted(word for word in drift if drift[word] >= 3)
    fallen = sorted(word for word in drift if drift[word] <= -3)
    top = max(abs(v) for v in drift.values())
    supply = list(dict.fromkeys(w for w, _s, _c in rows))
    volatile = next(w for w in supply if abs(drift[w]) == top)
    return {'total': len(rows), 'drift': drift, 'risen': risen,
            'fallen': fallen, 'volatile': volatile}


def _pin_order(rows):
    got = mod.trace_shifts(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71891)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)

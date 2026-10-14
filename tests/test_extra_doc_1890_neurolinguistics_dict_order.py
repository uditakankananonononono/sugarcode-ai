"""Dict-order oracle pins for row 1890, Title: Neurolinguistics.

Additive pins on top of the graded tests for row 1890: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import neurolinguistics as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    activators = {}
    signal_sum = {}
    for region, task, signal in rows:
        if region not in activators:
            activators[region] = {}
            signal_sum[region] = 0
        if signal >= 5:
            activators[region][task] = True
        signal_sum[region] += signal
    engaged = {}
    for region in activators:
        engaged[region] = len(activators[region])
    hot = sorted(region for region in engaged if engaged[region] >= 3)
    cold = sorted(region for region in engaged if engaged[region] == 0)
    top = max(signal_sum.values())
    supply = list(dict.fromkeys(r for r, _t, _s in rows))
    busiest = next(r for r in supply if signal_sum[r] == top)
    return {'total': len(rows), 'engaged': engaged, 'hot': hot,
            'cold': cold, 'signal': signal_sum, 'busiest': busiest}


def _pin_order(rows):
    got = mod.map_activation(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71890)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)

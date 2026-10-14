import re
from fractions import Fraction
import pytest
from sugarcode.extra_doc import metrics_summary as ms

S = ms.summarize
NC = ("metric collection", "measurement accuracy", "units or timing", "storage or export",
      "performance of any system", "alerting thresholds")


class I(int):
    pass


class Li(list):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        S(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def oracle_pct(samples, p):               # independent: smallest sample v with at least p% of samples <= v
    n = len(samples)
    for v in sorted(set(samples)):
        if Fraction(sum(1 for x in samples if x <= v) * 100, n) >= p:
            return v


def test_constants():
    assert (ms.MAX_SAMPLES, ms.MAX_VALUE, ms.MAX_PERCENTILES) == (1000, 10 ** 9, 10) and ms.NOT_CLAIMED == NC


def test_hand_literals():
    r = S([5, 1, 3, 2, 4], [20, 50, 90, 100])    # ranks ceil(1)=1, ceil(2.5)=3, ceil(4.5)=5, 5
    assert r["percentile_values"] == [1, 3, 5, 5]
    assert (r["count"], r["minimum"], r["maximum"], r["sum"]) == (5, 1, 5, 15)
    assert (r["mean_numerator"], r["mean_denominator"]) == (3, 1)
    r = S([1, 2], [50])                           # rank ceil(1)=1 -> 1 ; mean 3/2
    assert r["percentile_values"] == [1] and (r["mean_numerator"], r["mean_denominator"]) == (3, 2)
    r = S([7], [1, 100])
    assert r["percentile_values"] == [7, 7] and r["mean_denominator"] == 1
    r = S([10, 20, 30, 40], [25, 26, 75, 76])    # ranks 1, 2, 3, 4
    assert r["percentile_values"] == [10, 20, 30, 40]
    r = S([0, 0, 0], [1])
    assert (r["sum"], r["mean_numerator"], r["mean_denominator"]) == (0, 0, 1)
    assert S([2, 4, 4], [100])["mean_denominator"] == 3 and S([2, 4, 4], [100])["mean_numerator"] == 10


def test_shape_and_input_untouched():
    s, p = [3, 1, 2], [50, 50, 1]
    r = S(s, p)
    assert s == [3, 1, 2] and p == [50, 50, 1]
    assert r == {"count": 3, "minimum": 1, "maximum": 3, "sum": 6, "mean_numerator": 2, "mean_denominator": 1,
                 "percentile_values": [2, 2, 1], "metrics_validated": False, "not_claimed": NC}


def test_oracle_exhaustive_small():
    import itertools
    for n in range(1, 8):
        for samples in itertools.product([0, 3, 9], repeat=n):
            ps = [1, 14, 15, 33, 34, 50, 51, 67, 99, 100]
            r = S(list(samples), ps)
            assert r["percentile_values"] == [oracle_pct(samples, p) for p in ps]
            assert Fraction(r["mean_numerator"], r["mean_denominator"]) == Fraction(sum(samples), n)


def test_bounds():
    r = S([10 ** 9] * 1000, [100] * 10)
    assert r["sum"] == 10 ** 12 and r["percentile_values"] == [10 ** 9] * 10 and r["count"] == 1000
    samples = list(range(1000))
    r = S(samples, [1, 50, 99, 100])
    assert r["percentile_values"] == [9, 499, 989, 999]


@pytest.mark.parametrize("bad", [(1,), None, "1", Li([1]), [], [1] * 1001])
def test_samples_shape_refusals(bad):
    refuse("samples: list of 1 to 1000 required", bad, [50])


@pytest.mark.parametrize("bad", [(50,), None, "5", Li([50]), [], [50] * 11])
def test_percentiles_shape_refusals(bad):
    refuse("percentiles: list of 1 to 10 required", [1], bad)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", "\u0661", None, I(1), -1, 10 ** 9 + 1])
def test_sample_refusals_every_slot(bad):
    refuse("samples[0]: whole number 0 to 1000000000 required", [bad, 1, 1], [50])
    refuse("samples[2]: whole number 0 to 1000000000 required", [1, 1, bad], [50])


@pytest.mark.parametrize("bad", [True, 1.0, "50", "\u0665\u0660", None, I(50), 0, 101, -1])
def test_percentile_refusals_every_slot(bad):
    refuse("percentiles[0]: whole number 1 to 100 required", [1], [bad, 50])
    refuse("percentiles[1]: whole number 1 to 100 required", [1], [50, bad])


def test_check_order():
    refuse("samples: list of 1 to 1000 required", None, None)
    refuse("percentiles: list of 1 to 10 required", [None], None)
    refuse("samples[0]: whole number 0 to 1000000000 required", [None], [0])
    refuse("samples[1]: whole number 0 to 1000000000 required", [1, -1], [0, 0])

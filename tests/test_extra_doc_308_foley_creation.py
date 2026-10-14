import math
import pytest
from sugarcode.extra_doc import foley_creation as f

A = pytest.approx
E = math.e


def test_constants():
    assert (f.MAX_SAMPLES, f.SR_RANGE) == (200000, (1000, 96000))
    assert f.STATUS_NOTE.startswith("PARTIAL")


def test_impact_hand_literals():
    # sr 1000, f 250 -> phase n*pi/2 ; decay 0.001 s -> exp(-n)
    s = f.impact([(250, 1)], 0.001, 0.004, 1000)
    assert len(s) == 4
    assert s == A([0.0, 1 / E, 0.0, -1 / E ** 3], abs=1e-12)


def test_two_partials_sum_with_amplitudes():
    s = f.impact([(250, 2), (125, 0.5)], 0.001, 0.004, 1000)
    # second partial phase n*pi/4: sin(pi/4)=sqrt(.5), sin(pi/2)=1, sin(3pi/4)=sqrt(.5)
    r = math.sqrt(0.5)
    want = [0.0, 2 / E + 0.5 * r / E, 0.0 + 0.5 / E ** 2, -2 / E ** 3 + 0.5 * r / E ** 3]
    assert s == A(want, abs=1e-12)


def test_default_sample_rate_and_length():
    s = f.impact([(100, 1)], 0.5, 0.25)
    assert len(s) == 2000 and s[0] == 0.0
    assert s[1] == A(math.exp(-1 / 4000) * math.sin(2 * math.pi * 100 / 8000), abs=1e-12)


def test_length_rounding():
    assert len(f.impact([(100, 1)], 1, 0.0025, 1000)) == 2  # 2.5 rounds to 2 (half to even)
    assert len(f.impact([(100, 1)], 1, 0.0026, 1000)) == 3
    assert len(f.impact([(100, 1)], 1, 0.0024, 1000)) == 2


def test_damping_decreases_peak_envelope():
    s = f.impact([(100, 1)], 0.05, 0.5, 8000)
    first = max(abs(x) for x in s[:800])
    last = max(abs(x) for x in s[-800:])
    assert last < first * math.exp(-0.4 / 0.05) * 1.5


@pytest.mark.parametrize("kw", [
    dict(partials=[(1, 1)], decay_s=0.001, duration_s=0.01, sample_rate=999),
    dict(partials=[(1, 1)], decay_s=0.001, duration_s=0.01, sample_rate=96001),
    dict(partials=[(1, 1)], decay_s=0.0009, duration_s=0.01),
    dict(partials=[(1, 1)], decay_s=10.1, duration_s=0.01),
    dict(partials=[(1, 1)], decay_s=1, duration_s=0.0009),
    dict(partials=[(1, 1)], decay_s=1, duration_s=10.1),
    dict(partials=[], decay_s=1, duration_s=0.01),
    dict(partials=[(1, 1)] * 17, decay_s=1, duration_s=0.01),
    dict(partials=[(0.5, 1)], decay_s=1, duration_s=0.01),
    dict(partials=[(4001, 1)], decay_s=1, duration_s=0.01),
    dict(partials=[(10, -1)], decay_s=1, duration_s=0.01),
    dict(partials=[(10, 10.5)], decay_s=1, duration_s=0.01),
    dict(partials=[(10,)], decay_s=1, duration_s=0.01),
    dict(partials=[10], decay_s=1, duration_s=0.01),
    dict(partials="ab", decay_s=1, duration_s=0.01),
    dict(partials=[(True, 1)], decay_s=1, duration_s=0.01),
    dict(partials=[(10, 1)], decay_s=True, duration_s=0.01),
    dict(partials=[(10, 1)], decay_s=1, duration_s=float("nan")),
    dict(partials=[(10, 1)], decay_s=1, duration_s=0.01, sample_rate="8000"),
    dict(partials=[(10, 1)], decay_s=1, duration_s=2e9),
])
def test_impact_rejects(kw):
    with pytest.raises(ValueError):
        f.impact(**kw)


def test_impact_edges_accepted():
    assert len(f.impact([(500, 10)] * 16, 0.001, 0.001, 1000)) == 1
    assert len(f.impact([(1, 0)], 10, 10, 1000)) == 10000
    assert len(f.impact([(48000, 1)], 1, 0.001, 96000)) == 96


def test_messages():
    with pytest.raises(ValueError, match="freq: must be within"):
        f.impact([(0.5, 1)], 1, 0.01)
    with pytest.raises(ValueError, match="amplitude: must be within"):
        f.impact([(10, 11)], 1, 0.01)
    with pytest.raises(ValueError, match="partials: 1 to 16 required"):
        f.impact([], 1, 0.01)
    with pytest.raises(ValueError, match=r"partial: \(freq, amplitude\) required"):
        f.impact([(1, 2, 3)], 1, 0.01)
    with pytest.raises(ValueError, match="decay_s: number required"):
        f.impact([(10, 1)], True, 0.01)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        f.impact([(10, 1)], 2e9, 0.01)


def test_sample_cap_exact_and_over():
    assert len(f.impact([(100, 1)], 1, 5, 40000)) == 200000
    with pytest.raises(ValueError, match="more than 200000 samples"):
        f.impact([(100, 1)], 1, 5, 40001)


def test_layer_hand():
    r = f.layer([(0, [1, 2]), (0.002, [10])], 1000)
    assert r["samples"] == [1, 2, 10] and r["onsets"] == [0, 2] and r["length"] == 3 and r["peak"] == 10
    r = f.layer([(0.001, [5]), (0, [1, 1, 1])], 1000)
    assert r["samples"] == [1, 6, 1] and r["onsets"] == [0, 1] and r["peak"] == 6
    r = f.layer([(0.0006, [1]), (0.0004, [2])], 1000)
    assert r["onsets"] == [0, 1] and r["samples"] == [2, 1]


def test_layer_negative_peak_and_default_rate():
    r = f.layer([(0, [-7, 1])])
    assert r["peak"] == 7 and r["length"] == 2
    r = f.layer([(0.001, [1])])
    assert r["onsets"] == [8] and r["length"] == 9


def test_layer_overlapping_sum_and_empty_buffer():
    r = f.layer([(0, [1, 1]), (0, [1, 1]), (0, [])], 1000)
    assert r["samples"] == [2, 2]


@pytest.mark.parametrize("args", [
    ([], 8000), ([(0, [1])] * 65, 8000), ("ab", 8000), ([(0,)], 8000), ([0], 8000), ([(11, [1])], 8000),
    ([(-1, [1])], 8000), ([(0, "ab")], 8000), ([(0, [True])], 8000), ([(0, [1e7])], 8000), ([(0, [1])], 999),
    ([(True, [1])], 8000), ([(0, [float("nan")])], 8000), ([(0, [])], 8000),
])
def test_layer_rejects(args):
    with pytest.raises(ValueError):
        f.layer(*args)


def test_layer_limits():
    assert f.layer([(0, [1])] * 64, 1000)["length"] == 1
    assert f.layer([(10, [1])], 1000)["length"] == 10001
    assert f.layer([(0, [1e6, -1e6])], 1000)["peak"] == 1e6
    with pytest.raises(ValueError, match="more than 200000 samples"):
        f.layer([(10, [1])], 20000)
    assert f.layer([(0, [0.0] * 200000)], 1000)["length"] == 200000
    with pytest.raises(ValueError, match="more than 200000 samples"):
        f.layer([(0, [0.0] * 200001)], 1000)
    with pytest.raises(ValueError, match="sample"):
        f.layer([(0, [1000000.5])], 1000)
    with pytest.raises(ValueError, match="sample"):
        f.layer([(0, [-1000000.5])], 1000)
    assert f.layer([(0, [-1e6])], 1000)["peak"] == 1e6


def test_layer_messages():
    with pytest.raises(ValueError, match="events: 1 to 64 required"):
        f.layer([])
    with pytest.raises(ValueError, match=r"event: \(offset_s, samples\) required"):
        f.layer([(0,)])
    with pytest.raises(ValueError, match="samples: list required"):
        f.layer([(0, "ab")])
    with pytest.raises(ValueError, match="offset_s: must be within"):
        f.layer([(10.5, [1])])


def test_decay_point_hand():
    assert f.decay_point([0, 1, .5, .1, .05, .01], 0.1) == 4
    assert f.decay_point([1, .05, .5, .05], 0.1) == 3
    assert f.decay_point([1, .5], 0.1) is None
    assert f.decay_point([0.1, 1], 0.1) is None
    assert f.decay_point([0, 0], 0.5) is None
    assert f.decay_point([-1, .5, -.05], 0.1) == 2
    assert f.decay_point([.5, 1, 1, .01], 0.5) == 3
    assert f.decay_point([1, 0.6, 0.4, 0.2], 0.5) == 2
    assert f.decay_point([1, 0.5], 1) == 1
    assert f.decay_point([1, 1], 1) is None
    assert f.decay_point([1, 0.0001], 0.0001) is None


def test_decay_point_real_impact():
    s = f.impact([(200, 1)], 0.01, 0.2, 8000)
    i = f.decay_point(s, 0.01)
    pk = max(abs(x) for x in s)
    assert all(abs(x) < 0.01 * pk for x in s[i:])
    assert abs(s[i - 1]) >= 0.01 * pk or i - 1 <= s.index(max(s, key=abs))


@pytest.mark.parametrize("args", [([1], 0.00009), ([1], 1.1), ([], 0.5), ("ab", 0.5), ([True], 0.5), ([1], True),
                                  ([1e7], 0.5), ([1], float("nan")), (None, 0.5), ([1] * 200001, 0.5)])
def test_decay_point_rejects(args):
    with pytest.raises(ValueError):
        f.decay_point(*args)


def test_decay_point_messages():
    with pytest.raises(ValueError, match="threshold: must be within"):
        f.decay_point([1], 2)
    with pytest.raises(ValueError, match="samples: non-empty list within limit required"):
        f.decay_point([], 0.5)
    assert f.decay_point([0.0] * 200000, 0.5) is None
    with pytest.raises(ValueError, match="samples: non-empty"):
        f.decay_point([0.0] * 200001, 0.5)


def test_layer_default_rate_exact_and_magnitude_edges():
    r = f.layer([(1, [1])])
    assert r["onsets"] == [8000] and r["length"] == 8001
    with pytest.raises(ValueError, match="must be within"):
        f.layer([(0, [1e9])], 1000)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        f.layer([(0, [1000000001.0])], 1000)
    with pytest.raises(ValueError, match="must be within"):
        f.impact([(10, 1)], 1e9, 0.01)
    with pytest.raises(ValueError, match="must be within"):
        f.impact([(10, 1)], 999999999, 0.01)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        f.impact([(10, 1)], 1000000001.0, 0.01)


def test_decay_point_sample_range_edges():
    assert f.decay_point([1e6, 1], 0.5) == 1
    assert f.decay_point([-1e6, 1], 0.5) == 1
    for bad in (1000000.5, -1000000.5):
        with pytest.raises(ValueError, match="must be within"):
            f.decay_point([bad], 0.5)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        f.decay_point([1000000001.0], 0.5)

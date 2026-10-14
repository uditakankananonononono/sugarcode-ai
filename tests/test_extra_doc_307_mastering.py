import math
import random
import pytest
from sugarcode.extra_doc import mastering as m

M = m.master
A = pytest.approx


def test_constants():
    assert (m.MAX_SAMPLES, m.MAX_ABS_DB) == (1000000, 200)
    assert m.STATUS_NOTE.startswith("PARTIAL")


def test_half_scale_square_hand_values():
    r = M([0.5, -0.5, 0.5, -0.5])
    assert r["samples"] == 4
    assert r["peak_db"] == A(-6.020599913279624, abs=1e-9)
    assert r["rms_db"] == A(-6.020599913279624, abs=1e-9)
    assert r["crest_db"] == A(0.0, abs=1e-9)
    assert r["dc_offset"] == 0.0 and r["clipped"] == 0
    assert r["gain_db"] == A(-16 + 6.020599913279624, abs=1e-9)  # target RMS -16
    assert r["limited_by"] == "target" and r["meets_ceiling"] is True


def test_quiet_buffer_boosted_to_target():
    r = M([0.1, -0.1, 0.1, -0.1])  # peak = rms = -20 dBFS
    assert r["gain_db"] == A(4.0, abs=1e-9) and r["limited_by"] == "target"


def test_ceiling_limits_gain():
    r = M([1.0, 0, 0, 0], target_rms_db=-3)  # rms 0.5 = -6.0206 -> want 3.0206 ; room -1
    assert r["gain_db"] == A(-1.0, abs=1e-9)
    assert r["limited_by"] == "ceiling" and r["meets_ceiling"] is True
    assert r["peak_db"] == 0.0 and r["crest_db"] == A(6.020599913279624, abs=1e-9)
    assert r["rms_db"] == A(-6.020599913279624, abs=1e-9)


def test_tie_goes_to_target():
    r = M([0.5, -0.5], target_rms_db=-1, ceiling_db=-1)
    assert r["limited_by"] == "target" and r["gain_db"] == A(5.020599913279624, abs=1e-9)


def test_dc_and_clipping():
    r = M([0.5, 0.5, 0.5, 0.1])
    assert r["dc_offset"] == A(0.4, abs=1e-12)
    r = M([1.0, -1.0, 0.999, 2.0])
    assert r["clipped"] == 3
    assert r["peak_db"] == A(6.020599913279624, abs=1e-9)
    assert M([-0.25, -0.75])["dc_offset"] == -0.5


def test_silence():
    r = M([0, 0.0, -0.0])
    assert r["peak_db"] == -math.inf and r["rms_db"] == -math.inf
    assert r["crest_db"] is None and r["gain_db"] == 0.0
    assert r["limited_by"] == "silence" and r["clipped"] == 0 and r["samples"] == 3
    assert r["dc_offset"] == 0.0 and r["meets_ceiling"] is True
    assert r["status"] == m.STATUS_NOTE


@pytest.mark.parametrize("bad", [[], "abc", None, 5, [True], ["1"], [float("nan")], [float("inf")], [1e7], [-1e7], [None]])
def test_bad_samples(bad):
    with pytest.raises(ValueError):
        M(bad)


def test_sample_count_cap_and_exact_boundary():
    assert M([0.0] * 1000000)["samples"] == 1000000
    with pytest.raises(ValueError, match="more than 1000000"):
        M([0.0] * 1000001)
    with pytest.raises(ValueError, match="more than 1000000"):
        M([0.0] * 2000000)


def test_sample_magnitude_range_boundary():
    assert M([1e6])["samples"] == 1
    with pytest.raises(ValueError, match="sample"):
        M([1000000.5])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        M([2e9])


@pytest.mark.parametrize("kw", [{"target_rms_db": 0.1}, {"target_rms_db": -200.5}, {"target_rms_db": True},
                                {"target_rms_db": "x"}, {"target_rms_db": float("nan")}, {"target_rms_db": 2e9},
                                {"ceiling_db": 0.1}, {"ceiling_db": -201}, {"ceiling_db": False},
                                {"ceiling_db": float("inf")}])
def test_bad_targets(kw):
    with pytest.raises(ValueError):
        M([0.5], **kw)


def test_target_edges_accepted():
    assert M([0.5], target_rms_db=0, ceiling_db=0)["limited_by"] == "target"
    assert M([0.5], target_rms_db=-200, ceiling_db=-200)["samples"] == 1


def test_error_names():
    with pytest.raises(ValueError, match="target_rms_db: number required"):
        M([0.5], target_rms_db=True)
    with pytest.raises(ValueError, match="ceiling_db: must be within"):
        M([0.5], ceiling_db=1)
    with pytest.raises(ValueError, match="samples: list required"):
        M("ab")
    with pytest.raises(ValueError, match="at least one"):
        M([])
    with pytest.raises(ValueError, match="finite"):
        M([float("nan")])


def test_apply_gain_hand():
    assert m.apply_gain([0.1, -0.2], 20) == A([1.0, -2.0], abs=1e-12)
    assert m.apply_gain([0.5], 0) == [0.5]
    assert m.apply_gain([1.0], -20) == A([0.1], abs=1e-12)
    assert m.apply_gain([0.5], 6.020599913279624) == A([1.0], abs=1e-9)
    assert m.apply_gain([], 3) == []
    assert m.apply_gain((0.5,), 200)[0] == A(0.5 * 1e10, rel=1e-9)


@pytest.mark.parametrize("args", [([0.5], True), ([0.5], 201), ([0.5], -201), ([0.5], "1"), ([0.5], float("nan")),
                                  ("ab", 1), (None, 1), ([True], 1), ([1e7], 1), ([0.0] * 1000001, 1)])
def test_apply_gain_bad(args):
    with pytest.raises(ValueError):
        m.apply_gain(*args)


def test_apply_gain_cap_message():
    with pytest.raises(ValueError, match="samples"):
        m.apply_gain([0.0] * 1000001, 1)
    assert len(m.apply_gain([0.0] * 1000000, 1)) == 1000000


def test_random_against_independent_measurement():
    rnd = random.Random(7)
    for _ in range(60):
        xs = [rnd.uniform(-0.9, 0.9) * rnd.choice([0.05, 0.5, 1]) for _ in range(rnd.randint(1, 40))]
        t, c = rnd.uniform(-30, -6), rnd.uniform(-6, -0.5)
        r = M(xs, t, c)
        peak = max(map(abs, xs))
        rms = math.sqrt(math.fsum(x * x for x in xs) / len(xs))
        assert r["peak_db"] == A(20 * math.log(peak, 10), abs=1e-9)
        assert r["rms_db"] == A(20 * math.log(rms, 10), abs=1e-9)
        ys = m.apply_gain(xs, r["gain_db"])
        pk2 = 20 * math.log(max(map(abs, ys)), 10)
        rms2 = 20 * math.log(math.sqrt(math.fsum(y * y for y in ys) / len(ys)), 10)
        assert pk2 <= c + 1e-9 and rms2 <= t + 1e-9
        assert min(c - pk2, t - rms2) == A(0, abs=1e-9)


def test_tiny_samples_rms_not_underflowed():
    r = M([1e-200])  # true RMS equals the peak: -4000 dBFS
    assert r["rms_db"] == A(-4000.0, abs=1e-6) and r["peak_db"] == A(-4000.0, abs=1e-6)
    assert r["crest_db"] == A(0.0, abs=1e-6)
    assert r["gain_db"] == A(3984.0, abs=1e-6) and r["limited_by"] == "target"
    r = M([1e-200, -1e-200, 1e-200, -1e-200], target_rms_db=-200, ceiling_db=-200)
    assert r["rms_db"] == A(-4000.0, abs=1e-6) and r["gain_db"] == A(3800.0, abs=1e-6)
    r = M([5e-324])  # smallest subnormal
    assert r["rms_db"] == r["peak_db"] and r["rms_db"] == A(20 * math.log10(5e-324), abs=1e-6)
    r = M([1e-160])
    assert r["rms_db"] == A(-3200.0, abs=1e-9) and r["peak_db"] == A(-3200.0, abs=1e-9)
    r = M([3e-200, 4e-200])  # rms = 5e-200 / sqrt(2) = 3.5355e-200
    assert r["rms_db"] == A(20 * math.log10(math.sqrt(12.5) * 1e-200), abs=1e-6)
    assert r["peak_db"] == A(20 * math.log10(4e-200), abs=1e-6)


def test_ceiling_met_despite_float_error():
    # peak_db + gain_db exceeds the ceiling by 1.8e-15 in floating point; still counts as meeting it
    r = M([0.032], -10, -10.81)
    assert r["limited_by"] == "ceiling"
    assert r["peak_db"] + r["gain_db"] > -10.81
    assert r["meets_ceiling"] is True


def test_magnitude_cap_exact_and_sample_range_both_sides():
    with pytest.raises(ValueError, match="must be within"):
        M([999999999])
    with pytest.raises(ValueError, match="must be within"):
        M([1e9])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        M([1000000001.0])
    assert M([-1e6])["peak_db"] == A(120.0, abs=1e-9)
    with pytest.raises(ValueError, match="must be within"):
        M([-1000000.5])
    assert m.apply_gain([1e6, -1e6], 0) == [1e6, -1e6]
    for bad in (1000000.5, -1000000.5):
        with pytest.raises(ValueError, match="must be within"):
            m.apply_gain([bad], 0)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        m.apply_gain([1000000001.0], 0)
    with pytest.raises(ValueError, match="gain_db: must be within"):
        m.apply_gain([1], 200.5)

from fractions import Fraction as Fr
import random
import pytest
from sugarcode.extra_doc import scientific_illustration as s

B = s.scale_bar


def test_constants():
    assert (s.PPU_RANGE, s.WIDTH_RANGE, s.FRACTION_RANGE) == ((1e-4, 1e6), (10, 100000), (0.05, 0.5))
    assert s.STATUS_NOTE.startswith("PARTIAL")


def test_hand_values():
    r = B(10, 1000)  # budget 250 px -> at most 25 um -> 20 um
    assert r["length_um"] == 20 and r["bar_px"] == 200 and r["label"] == "20 um"
    assert r["fraction_of_width"] == Fr(1, 5) and r["status"] == s.STATUS_NOTE
    r = B(1000, 1000)  # at most 0.25 um -> 0.2 um = 200 nm
    assert r["length_um"] == Fr(1, 5) and r["bar_px"] == 200 and r["label"] == "200 nm"
    r = B(0.001, 1000)  # at most 250000 um -> 200000 um = 200 mm
    assert r["length_um"] == 200000 and r["label"] == "200 mm" and float(r["bar_px"]) == pytest.approx(200, rel=1e-15)
    assert B(1, 100)["label"] == "20 um"


def test_exact_budget_boundary_is_inclusive():
    r = B(10, 40)  # budget 10 px, 1 um is exactly 10 px
    assert r["length_um"] == 1 and r["label"] == "1 um"
    r = B(10, 100, 0.5)
    assert r["length_um"] == 5 and r["bar_px"] == 50 and r["fraction_of_width"] == Fr(1, 2)
    assert B(10, 39)["length_um"] == Fr(5, 10) and B(10, 39)["label"] == "500 nm"


def test_extremes_and_unit_labels():
    assert B(1e-4, 100000, 0.5)["label"] == "5000 mm" and B(1e-4, 100000, 0.5)["length_um"] == 5000000
    assert B(1e6, 100000, 0.5)["length_um"] == Fr(1, 20)
    assert B(1e6, 100000, 0.5)["label"] == "50 nm"
    assert B(1, 20)["label"] == "5 um" and B(1, 20)["bar_px"] == 5
    assert B(1, 4000)["label"] == "1 mm" and B(1, 4000)["length_um"] == 1000
    assert B(1, 3999)["label"] == "500 um"


def test_nothing_fits():
    with pytest.raises(ValueError, match="no scale bar fits"):
        B(1e6, 10, 0.05)
    with pytest.raises(ValueError, match="no scale bar fits"):
        B(1e6, 10, 0.5)


def test_smallest_candidate_boundary():
    # 0.001 um at 1e6 px/um is 1000 px: needs budget >= 1000
    assert B(1e6, 10000, 0.1)["length_um"] == Fr(1, 1000)
    with pytest.raises(ValueError, match="no scale bar fits"):
        B(1e6, 9999, 0.1)


def test_random_against_brute_force_candidates():
    rnd = random.Random(5)
    cands = sorted(Fr(m * 10 ** k) if k >= 0 else Fr(m, 10 ** -k) for k in range(-3, 7) for m in (1, 2, 5))
    for _ in range(200):
        ppu = rnd.choice([0.01, 0.5, 1, 3, 7.5, 40, 250, 1000, 12345])
        w = rnd.choice([10, 640, 1000, 1920, 5000, 99999])
        fr = rnd.choice([0.05, 0.1, 0.25, 0.4, 0.5])
        fits = [c for c in cands if c * Fr(ppu) <= Fr(w) * Fr(fr)]
        if not fits:
            with pytest.raises(ValueError):
                B(ppu, w, fr)
            continue
        assert B(ppu, w, fr)["length_um"] == fits[-1]


@pytest.mark.parametrize("args", [
    (0.00009, 100), (1000001, 100), (True, 100), ("1", 100), (float("nan"), 100), (1, 9), (1, 100001), (1, True),
    (1, None), (1, 100, 0.04), (1, 100, 0.51), (1, 100, True), (1, 100, "0.25"), (1, 100, float("inf")),
    (2e9, 100), (1, 100, -3e9),
])
def test_scale_bar_rejects(args):
    with pytest.raises(ValueError):
        B(*args)


def test_scale_bar_messages_and_magnitude():
    with pytest.raises(ValueError, match="px_per_um: must be within"):
        B(0, 100)
    with pytest.raises(ValueError, match="image_width_px: must be within"):
        B(1, 9)
    with pytest.raises(ValueError, match="max_fraction: must be within"):
        B(1, 100, 0.6)
    with pytest.raises(ValueError, match="px_per_um: number required"):
        B(True, 100)
    with pytest.raises(ValueError, match="px_per_um: finite"):
        B(float("nan"), 100)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        B(1000000001.0, 100)
    with pytest.raises(ValueError, match="must be within"):
        B(1e9, 100)
    with pytest.raises(ValueError, match="must be within"):
        B(999999999, 100)
    # binary 0.0001 is slightly above 1e-4, so 5e4 um is 5.0000000000000004 px and is excluded
    assert B(0.0001, 10, 0.5)["length_um"] == 20000


def test_scale_bar_edges_accepted():
    assert B(1, 10, 0.05)["label"] == "500 nm"
    assert B(1, 100000, 0.5)["length_um"] == 50000
    assert B(1, 100000)["length_um"] == 20000


def test_magnification():
    assert s.magnification(50, 100) == 500
    assert s.magnification(1, 1000) == 1
    assert float(s.magnification(0.001, 1000000000)) == pytest.approx(1e-9, rel=1e-15)
    assert float(s.magnification(100000, 0.001)) == pytest.approx(1e11, rel=1e-15)
    assert s.magnification(2.5, 10) == 250
    assert s.magnification(1, 3) == Fr(1000, 3)
    for bad in [(0.0009, 1), (100001, 1), (1, 0.0009), (1, 1e9 + 1), (True, 1), (1, "5"), (float("nan"), 1)]:
        with pytest.raises(ValueError):
            s.magnification(*bad)
    with pytest.raises(ValueError, match="drawn_mm: must be within"):
        s.magnification(0, 1)
    with pytest.raises(ValueError, match="real_um: must be within"):
        s.magnification(1, 0)


def test_magnification_real_um_upper_edge():
    assert s.magnification(1, 1e9) == Fr(1000, 10 ** 9)
    assert s.magnification(1, 10 ** 9) == Fr(1, 10 ** 6)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        s.magnification(1, 1000000001.0)

import itertools
import random
import pytest
from sugarcode.extra_doc import packaging_design as p

A = p.analyze_package


def test_constants():
    assert (p.MAX_MM, p.GLUE_FLAP_MM) == (10000, 15) and p.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal():
    # box 100 x 50 x 200 ; shelf 450 wide, 410 high, 300 deep
    r = A((100, 50, 200), (450, 410, 300), (1000, 700))
    assert r["surface_area_mm2"] == 2 * (5000 + 20000 + 10000) == 70000
    assert r["volume_mm3"] == 1_000_000
    # orientations (w,h,d): (100,50,200) 4*8*1=32 ; (100,200,50) 4*2*6=48 ; (50,100,200) 9*4*1=36 ; (50,200,100) 9*2*3=54 ;
    # (200,100,50) 2*4*6=48 ; (200,50,100) 2*8*3=48 -> best (50,200,100) = 54
    assert r["best_shelf_fit"] == {"orientation": {"width": 50, "height": 200, "depth": 100}, "count": 54,
                                   "across": 9, "high": 2, "deep": 3}
    assert r["front_face_share"] == pytest.approx(50 * 200 / (450 * 410))
    # net: width 2*(100+50)+15 = 315 ; height 200 + 100 = 300 ; sheet 1000x700: 3*2=6 vs (1000//300=3)*(700//315=2)=6
    assert r["net_mm"] == {"width": 315, "height": 300} and r["nets_per_sheet"] == 6 and r["net_fits_sheet"] is True
    assert r["sheet_utilisation"] == pytest.approx(6 * 315 * 300 / 700000)


def test_ties_keep_first_in_sorted_orientation_order():
    r = A((10, 10, 10), (100, 100, 100), (500, 500))
    assert r["best_shelf_fit"]["orientation"] == {"width": 10, "height": 10, "depth": 10} and r["best_shelf_fit"]["count"] == 1000
    # 2 x 3 x 4 into 12x12x12: every orientation packs 6*4*3=72 or so; sorted-first wins ties
    r = A((2, 3, 4), (12, 12, 12), (500, 500))
    assert r["best_shelf_fit"]["count"] == 72
    assert r["best_shelf_fit"]["orientation"] == {"width": 2, "height": 3, "depth": 4}


def test_shelf_fit_matches_brute_force_loop_oracle():
    rng = random.Random(286)
    for _ in range(80):
        box = tuple(rng.randint(1, 12) for _ in range(3))
        shelf = tuple(rng.randint(1, 40) for _ in range(3))
        r = A(box, shelf, (100, 100))
        best = 0
        for a, b, c in itertools.permutations(box):
            cnt = 0
            for x in range(0, shelf[0] - a + 1, a):
                for y in range(0, shelf[1] - b + 1, b):
                    for z in range(0, shelf[2] - c + 1, c):
                        cnt += 1
            best = max(best, cnt)
        assert r["best_shelf_fit"]["count"] == best
        o = r["best_shelf_fit"]["orientation"]
        assert sorted((o["width"], o["height"], o["depth"])) == sorted(box)
        assert r["best_shelf_fit"]["across"] * r["best_shelf_fit"]["high"] * r["best_shelf_fit"]["deep"] == best
        assert r["volume_mm3"] == box[0] * box[1] * box[2]


def test_net_sheet_fit_rotation_and_boundary():
    # net for box 10 x 10 x 10: width 2*20+15 = 55, height 30
    assert A((10, 10, 10), (50, 50, 50), (55, 30))["nets_per_sheet"] == 1
    assert A((10, 10, 10), (50, 50, 50), (30, 55))["nets_per_sheet"] == 1          # rotated
    assert A((10, 10, 10), (50, 50, 50), (54, 30))["net_fits_sheet"] is False
    assert A((10, 10, 10), (50, 50, 50), (55, 29))["net_fits_sheet"] is False
    assert A((10, 10, 10), (50, 50, 50), (54, 30))["nets_per_sheet"] == 0
    assert A((10, 10, 10), (50, 50, 50), (54, 30))["sheet_utilisation"] == 0.0
    # mixed: sheet 110 x 60 fits 2x2 =4 upright ; rotated 110//30=3 * 60//55=1 = 3 -> 4
    assert A((10, 10, 10), (50, 50, 50), (110, 60))["nets_per_sheet"] == 4
    # rotated better: sheet 60 x 110: upright 1*3=3 ; rotated 60//30=2 * 110//55=2 = 4
    assert A((10, 10, 10), (50, 50, 50), (60, 110))["nets_per_sheet"] == 4
    assert A((10, 10, 10), (50, 50, 50), (60, 110))["sheet_utilisation"] == pytest.approx(4 * 55 * 30 / 6600)


def test_non_cube_net_dimensions():
    r = A((30, 20, 70), (500, 500, 500), (1000, 1000))
    assert r["net_mm"] == {"width": 2 * 50 + 15, "height": 70 + 40}


def test_validation():
    ok_s, ok_sh = (100, 100, 100), (100, 100)
    for bad, m in [((1, 2), "three integers"), ("abc", "three integers"), ((1, 2, 3, 4), "three integers"),
                   ((True, 2, 3), r"box\[0\]: integer"), ((1, 2.0, 3), r"box\[1\]: integer"), ((1, 2, "3"), r"box\[2\]: integer"),
                   ((0, 2, 3), r"box\[0\]: must be within \[1, 10000\]"), ((1, 10001, 3), r"box\[1\]: must be within"),
                   ((1, 2, 10 ** 10), "magnitude above 1000000000"), ((1, 2, -(10 ** 10)), "magnitude above 1000000000"),
                   ((1, 2, 10 ** 9), "must be within")]:
        with pytest.raises(ValueError, match=m):
            A(bad, ok_s, ok_sh)
        with pytest.raises(ValueError, match=m.replace("box", "shelf")):
            A((1, 1, 1), bad, ok_sh)
    for bad, m in [((1,), "two integers"), ("ab", "two integers"), ((1, 2, 3), "two integers"), ((0, 5), r"sheet\[0\]"),
                   ((5, 10001), r"sheet\[1\]: must be within"), ((True, 5), r"sheet\[0\]: integer")]:
        with pytest.raises(ValueError, match=m):
            A((1, 1, 1), ok_s, bad)
    assert A((10000, 10000, 10000), (10000, 10000, 10000), (10000, 10000))["best_shelf_fit"]["count"] == 1
    assert A((1, 1, 1), (1, 1, 1), (1, 1))["best_shelf_fit"]["count"] == 1
    assert A((1, 1, 1), (1, 1, 1), (1, 1))["net_fits_sheet"] is False        # net is 19 x 3


def test_fits_with_exactly_one_net_and_cap_boundary():
    r = A((10, 10, 10), (50, 50, 50), (55, 30))
    assert r["nets_per_sheet"] == 1 and r["net_fits_sheet"] is True and r["sheet_utilisation"] == 1.0
    with pytest.raises(ValueError, match=r"box\[0\]: must be within"):
        A((10 ** 9, 1, 1), (5, 5, 5), (5, 5))
    with pytest.raises(ValueError, match="magnitude above 1000000000"):
        A((10 ** 9 + 1, 1, 1), (5, 5, 5), (5, 5))
    with pytest.raises(ValueError, match=r"sheet\[1\]: must be within"):
        A((1, 1, 1), (5, 5, 5), (5, 10 ** 9))

import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc import animation_principles as a

K = a.analyze_keyframes


def F(t, y, sx=1, sy=1):
    return {"t": t, "y": y, "sx": sx, "sy": sy}


def test_constants():
    assert (a.MAX_FRAMES, a.MAX_ABS, a.SCALE_RANGE, a.DEFAULT_TOLERANCE) == (500, 10 ** 6, (Fraction(1, 10), Fraction(10)), Fraction(1, 50))
    assert a.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal_jump_with_anticipation():
    # crouch down 2 then jump up to 10: net up, lead-in frames 0..2 (y 0,-1,-2 then rises at frame 3)
    r = K([F(0, 0, 1.25, 0.8), F(1, -1, 1.25, 0.8), F(2, -2, 1.2, 0.9), F(4, 3, 0.8, 1.25), F(6, 10, 1, 1)])
    assert r["net_direction"] == "up"
    ant = r["anticipation"]
    assert ant == {"frames": 3, "duration": 2.0, "share_of_total": pytest.approx(2 / 6), "depth": 2.0}
    assert [x["pose"] for x in r["frames"]] == ["squash", "squash", "squash", "stretch", "rest"]
    assert [x["area_ok"] for x in r["frames"]] == [True, True, False, True, True]         # 1.2*0.9 = 1.08 -> error 0.08 > 0.02
    assert r["squash_frames"] == 3 and r["stretch_frames"] == 1


def test_area_error_exact_and_tolerance_boundary():
    e = [x["area_error"] for x in K([F(0, 0, 2, 0.5), F(1, 1, 1.5, 0.5), F(2, 2, 1, 1)], 0)["frames"]]
    assert e == [0.0, 0.25, 0.0]
    r = K([F(0, 0, Fraction(51, 50), 1), F(1, 1), F(2, 2)], Fraction(1, 50))
    assert r["frames"][0]["area_ok"] is True and r["all_area_ok"] is True            # error exactly 1/50
    r = K([F(0, 0, Fraction(52, 50), 1), F(1, 1), F(2, 2)], Fraction(1, 50))
    assert r["frames"][0]["area_ok"] is False and r["all_area_ok"] is False
    assert K([F(0, 0, 1.01, 1), F(1, 1), F(2, 2)])["all_area_ok"] is True            # default 1/50
    assert K([F(0, 0, 1.03, 1), F(1, 1), F(2, 2)])["all_area_ok"] is False


def test_no_anticipation_cases():
    assert K([F(0, 0), F(1, 1), F(2, 2)])["anticipation"] is None                    # moves straight up
    assert K([F(0, 0), F(1, 0), F(2, 5)])["anticipation"] is None                    # first step zero
    assert K([F(0, 0), F(1, -1), F(2, 0)])["anticipation"] is None and K([F(0, 0), F(1, -1), F(2, 0)])["net_direction"] == "none"
    assert K([F(0, 0), F(1, -1), F(2, -2)])["anticipation"] is None                  # never reverses: no lead-in
    down = K([F(0, 5), F(1, 6), F(2, 7), F(3, 0)])
    assert down["net_direction"] == "down" and down["anticipation"]["frames"] == 3 and down["anticipation"]["depth"] == 2.0
    assert down["anticipation"]["duration"] == 2.0 and down["anticipation"]["share_of_total"] == pytest.approx(2 / 3)


def test_random_lead_in_matches_scan_oracle():
    rng = random.Random(295)
    for _ in range(80):
        n = rng.randint(3, 9)
        ys = [rng.randint(-5, 5) for _ in range(n)]
        r = K([F(i, ys[i]) for i in range(n)])
        net = ys[-1] - ys[0]
        want = None
        if net != 0 and ys[1] != ys[0] and (ys[1] > ys[0]) != (net > 0):
            d = 1 if net > 0 else -1
            for k in range(1, n):
                if (ys[k] - ys[k - 1]) * d > 0:
                    want = k
                    break
        assert (r["anticipation"] or {}).get("frames") == want


def test_validation():
    ok = [F(0, 0), F(1, 1), F(2, 2)]
    for fr, m in [([], "3..500"), (ok[:2], "3..500"), ("x", "3..500"), ([5, 5, 5], r"frames\[0\]: dict"),
                  ([F(0, 0), F(0, 1), F(1, 2)], "strictly increasing"), ([F(0, 0), F(2, 1), F(1, 2)], "strictly increasing"),
                  ([F(-1, 0), F(1, 1), F(2, 2)], r"\.t: must be within"), ([F(True, 0), F(1, 1), F(2, 2)], "number required"),
                  ([F(0, "1"), F(1, 1), F(2, 2)], "number required"), ([F(0, float("nan")), F(1, 1), F(2, 2)], "finite"),
                  ([F(0, 10 ** 6 + 1), F(1, 1), F(2, 2)], "magnitude above 1000000"),
                  ([F(0, 0, 0.09), F(1, 1), F(2, 2)], r"\.sx: must be within"), ([F(0, 0, 1, 10.5), F(1, 1), F(2, 2)], r"\.sy: must be within"),
                  ([{"t": 0, "y": 0, "sx": 1}, F(1, 1), F(2, 2)], "number required")]:
        with pytest.raises(ValueError, match=m):
            K(fr)
    for tl, m in [(True, "tolerance"), (-0.1, "tolerance"), (1.5, "tolerance"), ("1", "number required")]:
        with pytest.raises(ValueError, match=m):
            K(ok, tl)
    assert K([F(0, 0, Fraction(1, 10), 10), F(1, 1, 10, Fraction(1, 10)), F(2, 2)], 1)["all_area_ok"] is True
    assert K([F(0, -10 ** 6), F(1, 0), F(10 ** 6, 10 ** 6)])["net_direction"] == "up"
    assert len(K([F(i, i) for i in range(500)])["frames"]) == 500
    with pytest.raises(ValueError, match="3..500"):
        K([F(i, i) for i in range(501)])


def test_offset_start_time_and_position():
    # start at t=10, y=100: crouch to 96 by t=12, then rise to 130 at t=20. net up, lead-in covers frames 0..2
    r = K([F(10, 100), F(11, 98), F(12, 96), F(14, 110), F(20, 130)])
    assert r["anticipation"] == {"frames": 3, "duration": 2.0, "share_of_total": pytest.approx(2 / 10), "depth": 4.0}
    # downward net with a lead-in upward: depth is measured against the start, in the lead-in direction
    d = K([F(5, 50), F(6, 53), F(8, 57), F(9, 40), F(15, 10)])
    assert d["net_direction"] == "down"
    assert d["anticipation"] == {"frames": 3, "duration": 3.0, "share_of_total": pytest.approx(3 / 10), "depth": 7.0}
    # lead-in ends at the first rising step even when it plateaus first
    p = K([F(0, 0), F(1, -2), F(2, -2), F(3, -3), F(4, 5)])
    assert p["anticipation"]["frames"] == 4 and p["anticipation"]["depth"] == 3.0 and p["anticipation"]["duration"] == 3.0


def test_net_direction_with_unit_and_fractional_motion():
    assert K([F(0, 0), F(1, 0), F(2, 1)])["net_direction"] == "up"
    assert K([F(0, 1), F(1, 1), F(2, 0)])["net_direction"] == "down"
    assert K([F(0, 0), F(1, 0), F(2, Fraction(1, 1000))])["net_direction"] == "up"
    assert K([F(0, 0), F(1, 0), F(2, -Fraction(1, 1000))])["net_direction"] == "down"
    assert K([F(0, 0), F(1, 5), F(2, 0)])["net_direction"] == "none"


def test_small_net_down_has_anticipation_lead_in():
    # net movement is -0.5 (down); the lead-in is the first 2 frames going up by 0.5
    r = K([F(0, 0), F(1, .5), F(2, -.5)])
    assert r["net_direction"] == "down"
    assert r["anticipation"] == {"frames": 2, "duration": 1, "share_of_total": 0.5, "depth": 0.5}

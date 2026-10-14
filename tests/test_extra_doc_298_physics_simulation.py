import math
import random
import pytest
from sugarcode.extra_doc import physics_simulation as p

S = p.simulate_projectile


def discrete_oracle(speed, angle, g, dt, y0):
    """Closed form of semi-implicit Euler: v_n = vy - g n dt, y_n = y0 + vy n dt - g dt^2 n(n+1)/2."""
    vx, vy = speed * math.cos(math.radians(angle)), speed * math.sin(math.radians(angle))
    y = lambda n: y0 + vy * n * dt - g * dt * dt * n * (n + 1) / 2
    n = 1
    while y(n) >= 0:
        n += 1
    apex = max(y(k) for k in range(0, n))
    frac = y(n - 1) / (y(n - 1) - y(n))
    t = (n - 1 + frac) * dt
    return n, t, vx * t, apex


def test_constants():
    assert (p.MAX_STEPS, p.MAX_SPEED, p.G_RANGE, p.DT_RANGE, p.MAX_HEIGHT) == (100000, 1000, (0.1, 100), (0.0001, 0.1), 10000)
    assert p.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal_vertical_throw():
    # speed 1.7 up, g=10, dt=0.1: y_n = 0.17 n - 0.05 n(n+1): 0.07, 0.04, then -0.09 at n=3
    r = S(1.7, 90, 10, 0.1)
    assert r["steps"] == 3
    assert r["landing_time"] == pytest.approx((2 + 0.04 / 0.13) * 0.1)          # 0.230769...
    assert r["apex"] == pytest.approx(0.07)
    assert r["range"] == pytest.approx(0.0, abs=1e-12)
    assert r["analytic"]["flight_time"] == pytest.approx(0.34) and r["analytic"]["apex"] == pytest.approx(0.1445)
    assert r["errors"]["time"] == pytest.approx(0.34 - 0.23076923076923) and r["errors"]["apex"] == pytest.approx(0.0745)


def test_analytic_values_hand_literals():
    r = S(20, 45, 10, 0.001)
    assert r["analytic"]["range"] == pytest.approx(40.0, abs=1e-9)          # v^2 sin(2a)/g = 400/10
    assert r["analytic"]["apex"] == pytest.approx(10.0, abs=1e-9)           # (v sin a)^2 / 2g = 200/20
    assert r["analytic"]["flight_time"] == pytest.approx(2 * 20 * math.sin(math.pi / 4) / 10)
    # from a height: y0 = 5, horizontal throw (angle 0): t = sqrt(2*5/10) = 1, range = vx
    h = S(7, 0, 10, 0.001, 5)
    assert h["analytic"]["flight_time"] == pytest.approx(1.0) and h["analytic"]["range"] == pytest.approx(7.0)
    assert h["analytic"]["apex"] == 5.0


def test_matches_discrete_closed_form_on_random_inputs():
    rng = random.Random(298)
    for _ in range(40):
        sp, ang = rng.uniform(1, 50), rng.uniform(5, 85)
        g, dt, y0 = rng.uniform(1, 20), rng.choice([0.05, 0.01, 0.003]), rng.choice([0, 0, 3.5, 20])
        r = S(sp, ang, g, dt, y0)
        n, t, rng_, apex = discrete_oracle(sp, ang, g, dt, y0)
        assert r["steps"] == n
        assert r["landing_time"] == pytest.approx(t, rel=1e-7, abs=1e-9)
        assert r["range"] == pytest.approx(rng_, rel=1e-7, abs=1e-9)
        assert r["apex"] == pytest.approx(apex, rel=1e-9, abs=1e-9)


def test_errors_shrink_with_dt_first_order():
    e = [S(20, 60, 9.81, dt)["errors"]["time"] for dt in (0.08, 0.04, 0.02, 0.01)]
    assert e[0] > e[1] > e[2] > e[3]
    assert e[1] / e[0] == pytest.approx(0.5, abs=0.1) and e[3] / e[2] == pytest.approx(0.5, abs=0.1)
    r = S(20, 60, 9.81, 0.0001)
    assert r["errors"]["time"] < 1e-3 and r["errors"]["range"] < 1e-2 and r["errors"]["apex"] < 1e-2


def test_edge_cases():
    z = S(0, 45, 9.81, 0.01, 10)                                              # dropped from rest at height 10
    assert z["analytic"]["apex"] == 10.0 and z["analytic"]["range"] == 0.0 and z["range"] == 0.0
    assert z["landing_time"] == pytest.approx(math.sqrt(2 * 10 / 9.81), abs=0.02)
    flat = S(5, 0, 10, 0.01)                                                  # ground launch at angle 0 lands at once
    assert flat["steps"] == 1 and flat["landing_time"] == 0.0 and flat["range"] == 0.0 and flat["apex"] == 0.0


def test_step_cap_errors():
    with pytest.raises(ValueError, match="more than 100000 steps"):
        S(1000, 90, 0.1, 0.0001)                                              # flight 20000 s / 0.0001 = 2e8 steps
    assert S(1, 90, 9.81, 0.1)["steps"] >= 1                                  # 1 m/s up, short flight


def test_validation():
    for kw, m in [(dict(speed=True), "number required"), (dict(speed="1"), "number required"), (dict(speed=-1), r"speed: must be within \[0, 1000\]"),
                  (dict(speed=1001), r"speed: must be within"), (dict(speed=float("nan")), "finite"), (dict(speed=1e10), "magnitude above 1e9"),
                  (dict(angle_deg=-1), r"angle_deg: must be within \[0, 90\]"), (dict(angle_deg=90.1), r"angle_deg: must be within"),
                  (dict(g=0.09), r"g: must be within \[0.1, 100\]"), (dict(g=100.1), r"g: must be within"),
                  (dict(dt=0.00009), r"dt: must be within"), (dict(dt=0.11), r"dt: must be within"),
                  (dict(height=-1), r"height: must be within \[0, 10000\]"), (dict(height=10001), r"height: must be within")]:
        args = dict(speed=10, angle_deg=45, g=9.81, dt=0.01, height=0)
        args.update(kw)
        with pytest.raises(ValueError, match=m):
            S(**args)
    assert S(1000, 90, 100, 0.1)["steps"] > 1
    assert S(0, 0, 0.1, 0.0001, 0)["steps"] == 1
    assert S(1, 45, 100, 0.1, 10000)["analytic"]["apex"] == pytest.approx(10000.0025)
    assert S(10, 90, 9.81, 0.01)["steps"] == S(10, 90)["steps"] == S(10, 90, 9.81, 0.01, 0)["steps"]


def test_exact_zero_height_is_not_a_landing():
    # speed 1 up, g 1, dt 1/16: y_n = n(31 - n)/512 exactly in binary floats, so y_31 == 0.0 (still airborne), y_32 < 0
    r = S(1, 90, 1, 0.0625)
    assert r["steps"] == 32 and r["landing_time"] == 1.9375 and r["apex"] == pytest.approx(15 * 16 / 512)
    assert r["analytic"]["flight_time"] == 2.0 and r["analytic"]["apex"] == 0.5


def test_small_vertical_speed_apex_and_step_cap_boundary():
    r = S(0.5, 90, 9.81, 0.01)
    assert r["analytic"]["apex"] == pytest.approx(0.25 / 19.62)           # vy 0.5 < 1 still counts as rising
    # flight exactly 100000 steps long is accepted, a little longer is rejected
    ok = S(500, 90, 0.1, 0.1)
    assert ok["steps"] == 100000 and ok["landing_time"] == pytest.approx(9999.9, abs=1e-3)
    with pytest.raises(ValueError, match="more than 100000 steps"):
        S(500.1, 90, 0.1, 0.1)


def test_magnitude_cap_boundary():
    with pytest.raises(ValueError, match=r"speed: must be within"):
        S(1e9, 45)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        S(1e9 + 1000, 45)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        S(-1e9 - 1000, 45)

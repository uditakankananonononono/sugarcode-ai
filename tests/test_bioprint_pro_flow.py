"""BUG 57/58 regression: extrusion flow must be the self-consistent fixed point
of the HP/Cross relation, and the constitutive label must not claim Oldroyd-B
shear thinning (Oldroyd-B has constant shear viscosity)."""
import math
import numpy as np
from scipy.optimize import brentq
from sugarcode.modules.bioprint_pro import oldroyd_b_extrusion, calibrate
from sugarcode.modules.bioprint_pro.core import INKS, _viscosity


def test_flow_rate_is_self_consistent_fixed_point():
    r = oldroyd_b_extrusion(100, 0.4)
    ink = INKS["alginate_2pct"]
    rr, dp, L = 2e-4, 100000.0, 0.010
    q = r["flow_rate_mm3_s"] * 1e-9
    eta_at_q = _viscosity(ink, 4 * q / (math.pi * rr ** 3))
    flow_at_q = math.pi * rr ** 4 * dp / (8 * eta_at_q * L)
    assert abs(q - flow_at_q) / q < 1e-9
    assert abs(r["viscosity_Pa_s_at_wall"] - eta_at_q) < 1e-9
    assert abs(r["wall_shear_s-1"] - 4 * r["velocity_mm_s"] * 1e-3 / rr) < 1e-6


def test_alginate_flow_matches_independent_root_find():
    r = oldroyd_b_extrusion(100, 0.4)
    ink = INKS["alginate_2pct"]
    rr, dp, L = 2e-4, 100000.0, 0.010
    F = lambda q: q - math.pi * rr ** 4 * dp / (8 * _viscosity(ink, 4 * q / (math.pi * rr ** 3)) * L)
    q_fp = brentq(F, 1e-12, 1e-6)
    assert abs(r["flow_rate_mm3_s"] - q_fp * 1e9) < 1e-3
    assert abs(r["flow_rate_mm3_s"] - 0.928) < 0.01  # verified fixed point, was 0.213 pre-fix


def test_constitutive_label_is_honest_about_oldroyd_b():
    s = oldroyd_b_extrusion(100, 0.4)["constitutive_model"]
    assert "Giesekus" in s and "constant shear viscosity" in s


def test_calibrate_pressure_recomputes():
    w8 = [w for w in calibrate("alginate_2pct")["printability_window"] if w["speed_mm_s"] == 8][0]
    assert w8["pressure_kPa"] == 104.2 and w8["wall_shear_s-1"] == 160.0 and w8["viscosity_Pa_s"] == 6.512


def test_viability_sane_post_fix():
    r = oldroyd_b_extrusion(100, 0.4)
    assert 0 < r["mean_viability"] <= 1 and len(r["cell_viability"]) == 500

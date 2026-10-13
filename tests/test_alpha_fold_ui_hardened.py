from fractions import Fraction
import math
import numpy as np
import pytest
from sugarcode.modules.alpha_fold_ui import core
from sugarcode.modules.alpha_fold_ui.hardened import (
    safe_mutation_stability as ms, safe_rigid_transform as rt, safe_physical_energy as pe,
    safe_residue_graph as rg, safe_refine_coordinates as refine)

NAN = float("nan")
X = [[0, 0, 0], [3.8, 0, 0], [7.6, 0, 0], [7.6, 3.8, 0]]
R90 = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
SCALE2 = [[2, 0, 0], [0, 2, 0], [0, 0, 2]]


def test_red_core_defects():
    assert core.mutation_stability("ACDEFG", -1, "A")["wild_type"] == "G"  # last residue, not an error
    assert core.mutation_stability("ACDEFG", 1.7, "A")["position"] == 1  # silent truncation
    assert core.physical_energy([[0, 0, 0], [NAN, 0, 0], [1, 1, 1]])["lennard_jones"] != 0  # nan atom ignored, finite result
    assert np.isclose(core.rigid_transform(X, SCALE2, [0, 0, 0])[1][0], 7.6)  # "rigid" doubles distances
    assert np.isnan(core.refine_coordinates(X, None, 5, NAN)["coordinates"][0][0])
    assert abs(core.refine_coordinates(X, None, 5, 1e9)["coordinates"][0][0]) > 1e6
    assert len(core.refine_coordinates(X, None, -5)["energy_trajectory"]) == 1
    assert core.residue_graph(X, NAN)["edges"] == []


@pytest.mark.parametrize("a", [(-1, "A"), (99, "A"), (1.7, "A"), (NAN, "A"), (True, "A"), (1, "Z"), (1, "a"), (1, "AC"), (1, None)])
def test_green_ms_rejects(a):
    with pytest.raises(ValueError):
        ms("ACDEFG", *a)


@pytest.mark.parametrize("a", [(X, SCALE2, [0, 0, 0]), (X, [[1, 0], [0, 1]], [0, 0, 0]), (X, R90, [0, 0]),
                               (X, [[1, 0, 0], [0, 1, 0], [0, 0, -1]], [0, 0, 0]), (X, R90, [NAN, 0, 0]),
                               ([[0, NAN, 0]], R90, [0, 0, 0]), ([1, 2, 3], R90, [0, 0, 0]), ("abc", R90, [0, 0, 0])])
def test_green_rt_rejects(a):
    with pytest.raises(ValueError):
        rt(*a)


@pytest.mark.parametrize("kw", [dict(coords=[[0, 0, 0], [NAN, 0, 0], [1, 1, 1]]), dict(sigma=0), dict(sigma=NAN), dict(epsilon=-1),
                                dict(charges=[1]), dict(charges=[1, 1, NAN, 1]), dict(coords=np.zeros((5000, 3)))])
def test_green_pe_rejects(kw):
    args = dict(coords=X)
    args.update(kw)
    with pytest.raises(ValueError):
        pe(**args)


@pytest.mark.parametrize("a", [(X, NAN), (X, -1), (X, True), ([1, 2, 3],)])
def test_green_rg_rejects(a):
    with pytest.raises(ValueError):
        rg(*a)


@pytest.mark.parametrize("kw", [dict(learning_rate=NAN), dict(learning_rate=1e9), dict(steps=-5), dict(steps=10**9), dict(steps=2.5),
                                dict(restrain_bonds=1), dict(bond_length=0), dict(k_bond=-1), dict(coords=[[0, 0, 0]])])
def test_green_refine_rejects(kw):
    args = dict(coords=X)
    args.update(kw)
    with pytest.raises(ValueError):
        refine(**args)


def test_green_ms_oracle_from_table():
    out = ms("ACDEFG", 4, "V")  # wild F, mutant V
    p0, p1 = core.CF["F"], core.CF["V"]
    hyd = set("AILMFWVY")
    ddg = Fraction(8, 10) * Fraction(max(p1) - max(p0)).limit_denominator(10**6) / 100 - Fraction(12, 10) * ((("V" in hyd) - ("F" in hyd)))
    assert out["wild_type"] == "F" and out["position"] == 4
    assert out["ddg_relative"] == pytest.approx(float(ddg), abs=1e-9)


def test_green_rigid_exact_integer_oracle():
    out = rt([[1, 0, 0], [0, 2, 0]], R90, [1, 1, 1])
    assert out.tolist() == [[1, 2, 1], [-1, 1, 1]]  # rotate 90 deg about z then translate, exact integers


def test_green_rigid_preserves_distances():
    c = np.array(X)
    out = rt(c, R90, [5, -3, 2])
    d0 = np.linalg.norm(c[:, None] - c[None], axis=2)
    d1 = np.linalg.norm(out[:, None] - out[None], axis=2)
    assert np.allclose(d0, d1)


def test_green_pe_fraction_oracle_three_atoms():
    # only pair (0,2) is nonbonded (j>=i+2). sigma=1, r=2: sr=1/2 -> 4*eps*(1/4-1/2); eps=1/10
    out = pe([[0, 0, 0], [1, 0, 0], [2, 0, 0]], [1, 0, 1], sigma=1.0, epsilon=0.1)
    sr = Fraction(1, 2)
    lj = 4 * Fraction(1, 10) * (sr**12 - sr**6)
    elec = Fraction(5, 100) * 1 * 1 / 2
    assert out["lennard_jones"] == pytest.approx(float(lj), rel=1e-12)
    assert out["electrostatic"] == pytest.approx(float(elec), rel=1e-12)


def test_green_refine_keeps_bonds():
    out = refine(X, None, 3, 0.002)
    assert out["max_bond_deviation_A"] < 1e-6
    b = np.linalg.norm(np.diff(np.array(out["coordinates"]), axis=0), axis=1)
    assert np.allclose(b, 3.8, atol=1e-6)


# ---- v2 ----
HUGE = 10**1000


@pytest.mark.parametrize("call", [
    lambda: pe([[HUGE, 0, 0]]),
    lambda: pe(X, [HUGE, 0, 0, 0]),
    lambda: rg([[HUGE, 0, 0]]),
    lambda: rt([[HUGE, 0, 0]], R90, [0, 0, 0]),
    lambda: rt(X, [[HUGE, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0]),
    lambda: rt(X, R90, [HUGE, 0, 0]),
    lambda: refine([[0, 0, 0], [HUGE, 0, 0]]),
    lambda: refine(X, [HUGE, 0, 0, 0]),
])
def test_v2_huge_int_is_valueerror_not_overflow(call):
    with pytest.raises(ValueError):
        call()


@pytest.mark.parametrize("q", [[NAN, 1], [1], [1, 2, 3], [1, float("inf")], "ab", [2000, 0]])
def test_v2_refine_validates_charges_like_physical_energy(q):
    two = [[0, 0, 0], [3.8, 0, 0]]
    with pytest.raises(ValueError):
        pe(two, q)
    with pytest.raises(ValueError):
        refine(two, charges=q)


def test_v2_refine_accepts_valid_charges():
    out = refine([[0, 0, 0], [3.8, 0, 0], [7.6, 0, 0]], charges=[1, 0, -1], steps=2)
    assert out["bond_restraint"] is True


def test_v2_rotation_tolerance_has_no_relative_slack():
    # diag(1.000004, 1, 1): with default rtol=1e-5 np.allclose admits it; it scales x by 4e-6 (4 units at 1e6)
    r = [[1.000004, 0, 0], [0, 1, 0], [0, 0, 1]]
    with pytest.raises(ValueError):
        rt([[1e6, 0, 0], [0, 0, 0]], r, [0, 0, 0])
    assert np.allclose(np.array(r) @ np.array(r).T, np.eye(3))  # documents why rtol=0 is needed


def test_v2_rigid_distance_error_bounded():
    th = 0.3
    r = [[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]]
    c = np.array([[1e6, 0, 0], [0, 0, 0]])
    out = rt(c, r, [0, 0, 0])
    assert abs(np.linalg.norm(out[0] - out[1]) - 1e6) < 1e-3

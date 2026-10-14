import copy
from fractions import Fraction

import pytest

from sugarcode.extra_doc import kriging as m
from sugarcode.extra_doc.kriging import KrigingError, kriging as run

KEYS = "data keys must be exactly points, values, nugget, slope, targets"
LITERAL_NOT_CLAIMED = [
    "the linear variogram suits the data",
    "the field is stationary",
    "the prediction is accurate",
    "the coordinates are real locations",
    "real-world outcome",
]


def d(points, values, targets, nugget=0, slope=1):
    return {"points": [list(p) for p in points], "values": list(values), "nugget": nugget,
            "slope": slope, "targets": [list(t) for t in targets]}


def bad(data, msg):
    with pytest.raises(KrigingError) as e:
        run(data)
    assert str(e.value) == msg


def gam(p, q, nugget, slope):
    h = abs(p[0] - q[0]) + abs(p[1] - q[1])
    return Fraction(0) if h == 0 else Fraction(nugget + slope * h)


def check_equations(pts, vals, tgt, nugget, slope, rec):
    lam = [Fraction(w) for w in rec["weights"]]
    mu = Fraction(rec["multiplier"])
    assert sum(lam) == 1
    for i, p in enumerate(pts):
        assert sum(lam[j] * gam(p, pts[j], nugget, slope) for j in range(len(pts))) + mu == gam(p, tgt, nugget, slope)
    assert Fraction(rec["prediction"]) == sum(l * v for l, v in zip(lam, vals))
    assert Fraction(rec["variance"]) == sum(l * gam(p, tgt, nugget, slope) for l, p in zip(lam, pts)) + mu


def test_hand_two_point_cases():
    out = run(d([[0, 0], [2, 0]], [2, 6], [[1, 0], [3, 0]]))
    a, b = out["predictions"]
    assert a["weights"] == ["1/2", "1/2"] and a["multiplier"] == "0" and a["prediction"] == "4" and a["variance"] == "1"
    assert b["weights"] == ["0", "1"] and b["multiplier"] == "1" and b["prediction"] == "6" and b["variance"] == "2"
    assert a["target"] == [1, 0] and out["points"] == 2


def test_exact_interpolation_at_data_point():
    out = run(d([[0, 0], [2, 0], [0, 3]], [5, -3, 9], [[2, 0]], nugget=4, slope=3))
    r = out["predictions"][0]
    assert r["weights"] == ["0", "1", "0"] and r["prediction"] == "-3" and r["variance"] == "0"


def test_nugget_changes_weights_and_variance():
    base = run(d([[0, 0], [4, 0]], [0, 8], [[1, 0]], nugget=0, slope=1))["predictions"][0]
    nug = run(d([[0, 0], [4, 0]], [0, 8], [[1, 0]], nugget=5, slope=1))["predictions"][0]
    # no nugget: gamma01 = 4, gammas 1 and 3 -> weights 3/4, 1/4 (mu 0): prediction 2, variance 3/4+3/4 = 3/2
    assert base["weights"] == ["3/4", "1/4"] and base["prediction"] == "2" and base["variance"] == "3/2"
    # nugget 5: gamma01 = 9, gamma to target 6 and 8 -> lam2 - lam1 solves 9(l2 - l1) = 2 ... checked by equations
    check_equations([(0, 0), (4, 0)], [0, 8], (1, 0), 5, 1, nug)
    assert nug["variance"] != base["variance"]


def test_equations_hold_on_irregular_layouts():
    pts = [(0, 0), (3, 1), (-2, 4), (5, -3), (1, 1), (7, 7)]
    vals = [4, -2, 9, 0, 3, -8]
    tg = [(2, 2), (0, 0), (-5, 5), (10, 1)]
    for nugget, slope in ((0, 1), (3, 2), (1000, 1000)):
        out = run(d(pts, vals, tg, nugget, slope))
        for t, rec in zip(tg, out["predictions"]):
            check_equations(pts, vals, t, nugget, slope, rec)
            assert rec["target"] == list(t)


def test_constant_field_predicts_the_constant():
    out = run(d([[0, 0], [1, 5], [4, 2]], [7, 7, 7], [[9, 9], [2, 2]], nugget=2, slope=3))
    assert [r["prediction"] for r in out["predictions"]] == ["7", "7"]


def test_claims_and_input_not_mutated():
    data = d([[0, 0], [2, 0]], [2, 6], [[1, 0]])
    before = copy.deepcopy(data)
    out = run(data)
    assert data == before
    assert out["claims"] == {"variogram_suitable": False, "stationary": False, "accurate": False, "coordinates_real": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    again = run(data)
    assert again["claims"]["real_world"] is False and again["not_claimed"] == LITERAL_NOT_CLAIMED
    assert tuple(again["not_claimed"]) == m.NOT_CLAIMED


def test_constants():
    assert (m.MIN_N, m.MAX_N, m.MAX_TARGETS, m.MAX_VALUE, m.MAX_PARAM) == (2, 20, 10, 1000, 1000)


def test_structure_refusals_and_caps():
    ok = d([[0, 0], [2, 0]], [2, 6], [[1, 0]])
    for x in (None, [], {"points": []}, dict(ok, extra=1)):
        bad(x, KEYS)
    bad(dict(ok, points="ab"), "points must be a list")
    bad(dict(ok, values=(1, 2)), "values must be a list")
    bad(dict(ok, targets=None), "targets must be a list")
    bad(dict(ok, points=[[0, 0]], values=[1]), "points length out of range")
    bad(dict(ok, points=[[i, 0] for i in range(21)], values=[1] * 21), "points length out of range")
    run(dict(ok, points=[[i, 0] for i in range(20)], values=[1] * 20))
    bad(dict(ok, values=[1]), "values length out of range")
    bad(dict(ok, values=[1] * 21), "values length out of range")
    bad(dict(ok, values=[1, 2, 3]), "points and values must have the same length")
    bad(dict(ok, targets=[]), "targets length out of range")
    bad(dict(ok, targets=[[1, 0]] * 11), "targets length out of range")
    run(dict(ok, targets=[[1, 0]] * 10))
    for p in ([0, 0, 0], [0], (0, 0), "ab"):
        bad(dict(ok, points=[p, [2, 0]]), "point must be a [u, v] list")
        bad(dict(ok, targets=[p]), "point must be a [u, v] list")
    bad(dict(ok, points=[[1, 1], [1, 1]]), "points must be distinct")
    # a target may coincide with a data point
    run(dict(ok, targets=[[0, 0]]))


def test_value_refusals_and_caps():
    ok = d([[0, 0], [2, 0]], [2, 6], [[1, 0]])
    for v in (True, 1.0, "1", None):
        bad(dict(ok, nugget=v), "nugget must be an int")
        bad(dict(ok, slope=v), "slope must be an int")
        bad(dict(ok, values=[v, 6]), "value must be an int")
        bad(dict(ok, points=[[v, 0], [2, 0]]), "coordinate must be an int")
        bad(dict(ok, targets=[[0, v]]), "coordinate must be an int")
    for v in (-1, 1001):
        bad(dict(ok, nugget=v), "nugget out of range")
    for v in (0, 1001, -1):
        bad(dict(ok, slope=v), "slope out of range")
    for v in (1001, -1001):
        bad(dict(ok, values=[v, 6]), "value out of range")
        bad(dict(ok, points=[[v, 0], [2, 0]]), "coordinate out of range")
        bad(dict(ok, targets=[[0, v]]), "coordinate out of range")
    run(dict(ok, nugget=0, slope=1))
    run(dict(ok, nugget=1000, slope=1000))
    run(dict(ok, values=[1000, -1000], points=[[1000, 1000], [-1000, -1000]], targets=[[-1000, 1000]]))

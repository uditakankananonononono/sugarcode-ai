import copy
from fractions import Fraction

import pytest

from sugarcode.extra_doc import point_pattern as m
from sugarcode.extra_doc.point_pattern import PointPatternError, point_pattern as run

KEYS = "data keys must be exactly width, height, points, nx, ny, radii_squared, critical"
LITERAL_NOT_CLAIMED = [
    "the pattern is clustered, random or regular",
    "the window is the right study region",
    "the coordinates are real locations",
    "real-world outcome",
]


def d(points, w=10, h=10, nx=2, ny=2, radii=(4,), crit=None):
    return {"width": w, "height": h, "points": [list(p) for p in points], "nx": nx, "ny": ny,
            "radii_squared": list(radii), "critical": crit}


def bad(data, msg):
    with pytest.raises(PointPatternError) as e:
        run(data)
    assert str(e.value) == msg


def test_hand_quadrat_case():
    # 10x10 window, 2x2 grid: cells split at 5. Points: (1,1),(2,2),(3,3) in cell 0; (7,1) in cell 1.
    out = run(d([[1, 1], [2, 2], [3, 3], [7, 1]], crit=[3, 1]))
    q = out["quadrat"]
    assert q["counts"] == [3, 1, 0, 0] and q["mean"] == "1"
    # sum sq dev = 4 + 0 + 1 + 1 = 6 ; var = 2 ; vmr = 2 ; chi = 6 ; df 3
    assert q["variance"] == "2" and q["variance_to_mean"] == "2" and q["chi_square"] == "6"
    assert q["degrees_of_freedom"] == 3 and q["exceeds_critical"] is True
    assert run(d([[1, 1], [2, 2], [3, 3], [7, 1]], crit=[6, 1]))["quadrat"]["exceeds_critical"] is False
    assert run(d([[1, 1], [2, 2], [3, 3], [7, 1]], crit=[11, 2]))["quadrat"]["exceeds_critical"] is True
    assert run(d([[1, 1], [2, 2], [3, 3], [7, 1]]))["quadrat"]["exceeds_critical"] is None


def test_cell_assignment_row_major_and_non_dividing_grid():
    out = run(d([[0, 0], [9, 0], [0, 9], [9, 9]]))
    assert out["quadrat"]["counts"] == [1, 1, 1, 1]
    # width 7, nx 3: cell = x*3//7 -> x 0,1,2 -> 0 ; 3,4 -> 1 ; 5,6 -> 2
    out = run(d([[0, 0], [2, 0], [3, 0], [4, 0], [5, 0], [6, 0]], w=7, h=1, nx=3, ny=1))
    assert out["quadrat"]["counts"] == [2, 2, 2]
    # row-major: y bucket picks the row
    out = run(d([[0, 0], [0, 9], [0, 9]], w=10, h=10, nx=1, ny=2))
    assert out["quadrat"]["counts"] == [1, 2]
    out = run(d([[9, 0], [9, 0], [0, 9]], w=10, h=10, nx=2, ny=2))
    assert out["quadrat"]["counts"] == [0, 2, 1, 0]


def test_nearest_neighbour_and_ties_and_repeats():
    out = run(d([[0, 0], [3, 4], [3, 4], [9, 9]]))
    assert out["nearest_neighbour"]["squared_distances"] == [25, 0, 0, 61]
    assert out["nearest_neighbour"]["mean_squared_distance"] == "43/2"


def test_ripley_hand_and_boundary():
    # points on a line: 0,3,4 at y=0 ; squared distances 9,16,1
    out = run(d([[0, 0], [3, 0], [4, 0]], radii=[1, 9, 16, 17]))
    assert [r["ordered_pairs"] for r in out["ripley_k"]] == [2, 4, 6, 6]
    # K = area * pairs / (n(n-1)) = 100 * 2/6 = 100/3
    assert out["ripley_k"][0]["k"] == "100/3" and out["ripley_k"][2]["k"] == "100"
    assert out["window_area"] == 100 and out["ripley_k"][1]["radius_squared"] == 9


def test_matches_independent_recount():
    pts = [(1, 1), (8, 2), (3, 7), (3, 7), (9, 9), (5, 5), (0, 6)]
    out = run(d(pts, w=10, h=10, nx=3, ny=2, radii=[2, 10, 30, 90, 200]))
    n = len(pts)
    for r in out["ripley_k"]:
        c = 0
        for i, a in enumerate(pts):
            for j, b in enumerate(pts):
                if i != j and (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 <= r["radius_squared"]:
                    c += 1
        assert r["ordered_pairs"] == c and r["k"] == str(Fraction(100 * c, n * (n - 1)))
    cnt = {}
    for x, y in pts:
        cnt[(y * 2 // 10) * 3 + x * 3 // 10] = cnt.get((y * 2 // 10) * 3 + x * 3 // 10, 0) + 1
    assert out["quadrat"]["counts"] == [cnt.get(i, 0) for i in range(6)]
    assert sum(out["quadrat"]["counts"]) == n


def test_claims_and_input_not_mutated():
    data = d([[1, 1], [2, 2], [3, 3]], crit=[2, 1])
    before = copy.deepcopy(data)
    out = run(data)
    assert data == before
    assert out["claims"] == {"pattern_type": False, "window_valid": False, "coordinates_real": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    out["quadrat"]["counts"][0] = 99
    again = run(data)
    assert again["claims"]["real_world"] is False and again["not_claimed"] == LITERAL_NOT_CLAIMED
    assert again["quadrat"]["counts"][0] != 99
    assert tuple(again["not_claimed"]) == m.NOT_CLAIMED


def test_constants():
    assert (m.MIN_N, m.MAX_N, m.MAX_SIDE, m.MAX_GRID, m.MAX_RADII, m.MAX_R2, m.MAX_CRIT) == (3, 50, 1000, 10, 5, 2000000, 1000000)


def test_structure_refusals_and_caps():
    ok = d([[1, 1], [2, 2], [3, 3]])
    for x in (None, [], {"width": 1}, dict(ok, extra=1)):
        bad(x, KEYS)
    bad(dict(ok, points="ab"), "points must be a list")
    bad(dict(ok, points=[[1, 1], [2, 2]]), "points length out of range")
    bad(dict(ok, points=[[1, 1]] * 51), "points length out of range")
    run(dict(ok, points=[[1, 1]] * 50))
    bad(dict(ok, radii_squared="ab"), "radii_squared must be a list")
    bad(dict(ok, radii_squared=[]), "radii_squared length out of range")
    bad(dict(ok, radii_squared=[1, 2, 3, 4, 5, 6]), "radii_squared length out of range")
    run(dict(ok, radii_squared=[1, 2, 3, 4, 5]))
    bad(dict(ok, radii_squared=[2, 2]), "radii_squared must be strictly increasing")
    bad(dict(ok, radii_squared=[3, 2]), "radii_squared must be strictly increasing")
    bad(dict(ok, nx=1, ny=1), "grid must have at least 2 cells")
    run(dict(ok, nx=1, ny=2))
    run(dict(ok, nx=2, ny=1))
    for p in ([1], [1, 1, 1], (1, 1), "ab"):
        bad(dict(ok, points=[p, [2, 2], [3, 3]]), "point must be an [x, y] list")
    for c in ("x", [1], [1, 2, 3], (1, 2)):
        bad(dict(ok, critical=c), "critical must be null or a [num, den] list")
    for c in ([True, 1], [1, True], [1.0, 1]):
        bad(dict(ok, critical=c), "critical parts must be ints")
    for c in ([-1, 1], [1000001, 1], [1, 0], [1, 1000001]):
        bad(dict(ok, critical=c), "critical out of range")
    for c in ([0, 1], [1000000, 1], [1, 1000000]):
        run(dict(ok, critical=c))


def test_value_refusals_and_caps():
    ok = d([[1, 1], [2, 2], [3, 3]])
    for name in ("width", "height", "nx", "ny"):
        for v in (True, 1.0, "1", None):
            bad(dict(ok, **{name: v}), f"{name} must be an int")
        bad(dict(ok, **{name: 0}), f"{name} out of range")
    bad(dict(ok, width=1001), "width out of range")
    bad(dict(ok, height=1001), "height out of range")
    bad(dict(ok, nx=11), "nx out of range")
    bad(dict(ok, ny=11), "ny out of range")
    run(dict(ok, width=1000, height=1000, nx=10, ny=10))
    run(dict(ok, width=4, height=4))
    for v in (True, 1.0, "1"):
        bad(dict(ok, points=[[v, 1], [2, 2], [3, 3]]), "x must be an int")
        bad(dict(ok, points=[[1, v], [2, 2], [3, 3]]), "y must be an int")
        bad(dict(ok, radii_squared=[v]), "radius squared must be an int")
    bad(dict(ok, points=[[10, 1], [2, 2], [3, 3]]), "x out of range")
    bad(dict(ok, points=[[-1, 1], [2, 2], [3, 3]]), "x out of range")
    bad(dict(ok, points=[[1, 10], [2, 2], [3, 3]]), "y out of range")
    bad(dict(ok, points=[[1, -1], [2, 2], [3, 3]]), "y out of range")
    run(dict(ok, points=[[0, 0], [9, 9], [3, 3]]))
    bad(dict(ok, radii_squared=[0]), "radius squared out of range")
    bad(dict(ok, radii_squared=[2000001]), "radius squared out of range")
    run(dict(ok, radii_squared=[1]))
    run(dict(ok, radii_squared=[2000000]))


def test_all_points_in_one_cell_and_minimum_window():
    q = run(d([[0, 0], [1, 1], [2, 2], [3, 3]]))["quadrat"]
    # counts 4,0,0,0 mean 1: sum sq dev 9+1+1+1 = 12 ; var 4 ; chi 12
    assert q["counts"] == [4, 0, 0, 0] and q["variance"] == "4" and q["chi_square"] == "12" and q["variance_to_mean"] == "4"
    out = run(d([[0, 0], [0, 1], [0, 1]], w=1, h=2, nx=1, ny=2, radii=[1]))
    assert out["quadrat"]["counts"] == [1, 2] and out["window_area"] == 2
    q = run(d([[0, 0], [0, 1], [0, 1]], w=1, h=2, nx=1, ny=2))["quadrat"]
    # mean 3/2, deviations -1/2 and 1/2: ss = 1/2, var = 1/2, chi = 1/3
    assert q["variance"] == "1/2" and q["chi_square"] == "1/3" and q["degrees_of_freedom"] == 1


def test_variance_to_mean_with_non_unit_mean():
    q = run(d([[0, 0], [1, 1], [2, 2]]))["quadrat"]
    assert q["counts"] == [3, 0, 0, 0] and q["mean"] == "3/4"
    assert q["variance"] == "9/4" and q["variance_to_mean"] == "3" and q["chi_square"] == "9"
    # counts 2,1,0,0: ss = 25/16 + 1/16 + 9/16 + 9/16 = 11/4 ; var 11/12 ; vmr 11/9 ; chi 11/3
    q = run(d([[0, 0], [1, 1], [7, 1]]))["quadrat"]
    assert q["counts"] == [2, 1, 0, 0] and q["mean"] == "3/4"
    assert q["variance"] == "11/12" and q["variance_to_mean"] == "11/9" and q["chi_square"] == "11/3"

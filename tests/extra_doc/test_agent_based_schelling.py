import copy
import random
from fractions import Fraction

import pytest

from sugarcode.extra_doc import agent_based_schelling as m
from sugarcode.extra_doc.agent_based_schelling import SchellingError, agent_based_schelling as run

KEYS = "data keys must be exactly grid, tol_num, tol_den, max_rounds"
LITERAL_NOT_CLAIMED = [
    "the run says anything about real neighbourhoods or people",
    "another update order gives the same grid",
    "the model explains real segregation",
    "real-world outcome",
]
HAND = [[1, 2, 1], [2, 1, 2], [1, 2, 0]]


def d(grid, num=1, den=2, rounds=10):
    return {"grid": [list(r) for r in grid], "tol_num": num, "tol_den": den, "max_rounds": rounds}


def bad(data, msg):
    with pytest.raises(SchellingError) as e:
        run(data)
    assert str(e.value) == msg


def ref_run(grid, num, den, rounds):
    # dictionary-based reimplementation, written separately from the module
    h, w = len(grid), len(grid[0])
    cell = {(r, c): grid[r][c] for r in range(h) for c in range(w)}
    tol = Fraction(num, den)

    def nbrs(p):
        return [cell[(p[0] + a, p[1] + b)] for a in (-1, 0, 1) for b in (-1, 0, 1)
                if (a, b) != (0, 0) and (p[0] + a, p[1] + b) in cell]

    def ok(p, kind):
        vals = [v for v in nbrs(p) if v]
        if not vals:
            return True
        return Fraction(sum(1 for v in vals if v == kind), len(vals)) >= tol

    log = []
    for _ in range(rounds):
        n = 0
        for p in sorted(cell):
            kind = cell[p]
            if kind == 0 or ok(p, kind):
                continue
            cell[p] = 0
            dest = next((q for q in sorted(cell) if cell[q] == 0 and q != p and ok(q, kind)), None)
            if dest is None:
                cell[p] = kind
            else:
                cell[dest] = kind
                n += 1
        log.append(n)
        if n == 0:
            break
    return [[cell[(r, c)] for c in range(w)] for r in range(h)], log


def test_hand_trace():
    out = run(d(HAND))
    assert out["grid"] == [[1, 1, 1], [2, 0, 2], [1, 2, 2]]
    assert out["moves_per_round"] == [2, 0] and out["rounds"] == 2 and out["settled"] is True
    assert out["happy_share_start"] == "1/4" and out["happy_share_end"] == "3/4"
    assert out["segregation_start"] == "113/280" and out["segregation_end"] == "1/2"


def test_matches_separate_reimplementation_on_random_grids():
    rng = random.Random(11)
    for _ in range(60):
        h, w = rng.randint(2, 6), rng.randint(2, 6)
        grid = [[rng.choice((0, 1, 1, 2, 2)) for _ in range(w)] for _ in range(h)]
        den = rng.choice((1, 2, 3, 5, 10))
        num = rng.randint(0, den)
        rounds = rng.randint(1, 6)
        out = run(d(grid, num, den, rounds))
        final, log = ref_run(grid, num, den, rounds)
        assert out["grid"] == final and out["moves_per_round"] == log, (grid, num, den, rounds)
        assert out["settled"] == (log[-1] == 0)


def test_agents_are_conserved_and_input_untouched():
    grid = [[1, 2, 0, 1], [2, 0, 1, 2], [0, 1, 2, 0], [1, 2, 1, 0]]
    before = copy.deepcopy(grid)
    out = run(d(grid, 2, 3, 20))
    assert grid == before
    for kind in (0, 1, 2):
        assert sum(r.count(kind) for r in out["grid"]) == sum(r.count(kind) for r in before)


def test_zero_tolerance_nobody_moves_and_full_tolerance_stops_when_stuck():
    out = run(d(HAND, 0, 1, 5))
    assert out["grid"] == HAND and out["moves_per_round"] == [0] and out["settled"] is True
    assert out["happy_share_start"] == "1" and out["happy_share_end"] == "1"
    # no empty cell: nobody can move
    full = [[1, 2], [2, 1]]
    out = run(d(full, 1, 1, 3))
    assert out["grid"] == full and out["settled"] is True and out["moves_per_round"] == [0]


def test_max_rounds_cuts_off_unsettled_runs():
    grid = [[1, 2, 1, 2, 0], [2, 1, 2, 1, 0], [1, 2, 1, 2, 0], [2, 1, 2, 1, 0]]
    out = run(d(grid, 1, 1, 1))
    assert out["rounds"] == 1 and len(out["moves_per_round"]) == 1
    full = run(d(grid, 1, 1, 20))
    assert full["rounds"] == len(full["moves_per_round"]) <= 20
    if not full["settled"]:
        assert full["rounds"] == 20


def test_isolated_agent_is_happy_and_empty_board():
    out = run(d([[1, 0], [0, 0]], 1, 1, 3))
    assert out["grid"] == [[1, 0], [0, 0]] and out["happy_share_start"] == "1" and out["segregation_start"] == "0"
    out = run(d([[0, 0], [0, 0]], 1, 2, 3))
    assert out["happy_share_end"] == "1" and out["segregation_end"] == "0" and out["rounds"] == 1


def test_tolerance_boundary_is_at_least():
    # (0,0) and (0,1) each see one like and one other neighbour: share exactly 1/2; (1,0) sees no like
    grid = [[1, 1, 0], [2, 0, 0]]
    assert run(d(grid, 1, 2, 1))["happy_share_start"] == "2/3"
    assert run(d(grid, 51, 100, 1))["happy_share_start"] == "0"
    assert run(d(grid, 50, 100, 1))["happy_share_start"] == "2/3"


def test_claims_and_input_not_mutated():
    data = d(HAND)
    before = copy.deepcopy(data)
    out = run(data)
    assert data == before
    assert out["claims"] == {"real_neighbourhoods": False, "order_independent": False, "explains_segregation": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    out["grid"][0][0] = 9
    again = run(data)
    assert again["claims"]["real_world"] is False and again["not_claimed"] == LITERAL_NOT_CLAIMED
    assert again["grid"][0][0] != 9
    assert tuple(again["not_claimed"]) == m.NOT_CLAIMED


def test_constants():
    assert (m.MIN_SIDE, m.MAX_SIDE, m.MAX_DEN, m.MAX_ROUNDS) == (2, 8, 100, 20)


def test_refusals_and_caps():
    ok = d(HAND)
    for x in (None, [], {"grid": HAND}, dict(ok, extra=1)):
        bad(x, KEYS)
    for name in ("tol_num", "tol_den", "max_rounds"):
        for v in (True, 1.0, "1", None):
            bad(dict(ok, **{name: v}), f"{name} must be an int")
    bad(dict(ok, tol_den=0), "tol_den out of range")
    bad(dict(ok, tol_den=101), "tol_den out of range")
    bad(dict(ok, tol_num=-1), "tol_num out of range")
    bad(dict(ok, tol_num=3), "tol_num out of range")
    run(dict(ok, tol_num=2, tol_den=2))
    run(dict(ok, tol_num=0, tol_den=1))
    run(dict(ok, tol_num=100, tol_den=100))
    bad(dict(ok, max_rounds=0), "max_rounds out of range")
    bad(dict(ok, max_rounds=21), "max_rounds out of range")
    run(dict(ok, max_rounds=1))
    run(dict(ok, max_rounds=20))
    bad(dict(ok, grid="ab"), "grid must be a list")
    bad(dict(ok, grid=[[1, 2]]), "grid height out of range")
    bad(dict(ok, grid=[[1, 2]] * 9), "grid height out of range")
    run(dict(ok, grid=[[1, 2]] * 8))
    bad(dict(ok, grid=[(1, 2), (2, 1)]), "grid row must be a list")
    bad(dict(ok, grid=[[1], [2]]), "grid width out of range")
    bad(dict(ok, grid=[[1] * 9, [2] * 9]), "grid width out of range")
    run(dict(ok, grid=[[1] * 8, [2] * 8]))
    bad(dict(ok, grid=[[1, 2], [1, 2, 1]]), "grid rows must have equal length")
    for v in (True, 1.0, "1", None):
        bad(dict(ok, grid=[[v, 1], [2, 1]]), "cell must be an int")
    for v in (-1, 3):
        bad(dict(ok, grid=[[v, 1], [2, 1]]), "cell out of range")

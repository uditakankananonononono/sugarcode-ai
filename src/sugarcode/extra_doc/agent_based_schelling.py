"""Agent-Based Simulation - exact deterministic Schelling segregation run.

Pure function over caller data. No retrieval, no network, no clock, no randomness, no
floats. Input: grid, a list of 2..8 equal-length rows (each 2..8 integers) holding 0 for
an empty cell and 1 or 2 for an agent of that type; tol_num / tol_den, the tolerance as an
integer fraction (tol_den 1..100, tol_num 0..tol_den); and max_rounds (integer 1..20). An
agent is happy when the share of agents of its own type among its occupied neighbours
(the up to 8 surrounding cells inside the grid, no wrap-around) is at least the
tolerance; an agent with no neighbours is happy. Each round visits the agents in
row-major order; an unhappy agent moves to the first empty cell in row-major order where
it would be happy once its old cell is empty, and stays put when there is none. The run
stops after a round with no move or after max_rounds. Everything is decided on exact
integers and Fractions. The result gives the final grid, the number of rounds run, the
moves in each round, whether it settled (a round with no moves occurred), the share of
happy agents and the segregation index (mean over agents with neighbours of the share of
like neighbours) before the run and after it, as exact Fractions in strings.

Scope: PARTIAL for the Agent-Based Simulation line. It runs one fixed agent-based model
(Schelling) with one fixed deterministic update order. It has no randomness, no other
model, no parameter sweep, no statistics over many runs and no calibration to data.

Not claimed: that the run says anything about real neighbourhoods or people, that another
update order would give the same grid, that the model explains any real segregation, or
anything about the real world. Every claim flag in the result is False.
"""
from fractions import Fraction

MIN_SIDE = 2
MAX_SIDE = 8
MAX_DEN = 100
MAX_ROUNDS = 20
_TOP = frozenset({"grid", "tol_num", "tol_den", "max_rounds"})

NOT_CLAIMED = (
    "the run says anything about real neighbourhoods or people",
    "another update order gives the same grid",
    "the model explains real segregation",
    "real-world outcome",
)
CLAIMS = {"real_neighbourhoods": False, "order_independent": False, "explains_segregation": False, "real_world": False}


class SchellingError(ValueError):
    pass


def _int(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise SchellingError(f"{name} must be an int")
    if v < lo or v > hi:
        raise SchellingError(f"{name} out of range")
    return v


def _like(g, r, c, kind):
    like = other = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr or dc) and 0 <= r + dr < len(g) and 0 <= c + dc < len(g[0]):
                v = g[r + dr][c + dc]
                if v == kind:
                    like += 1
                elif v:
                    other += 1
    return like, other


def _happy(g, r, c, kind, tol):
    like, other = _like(g, r, c, kind)
    return like + other == 0 or Fraction(like, like + other) >= tol


def _stats(g, tol):
    happy = agents = 0
    shares = []
    for r, row in enumerate(g):
        for c, kind in enumerate(row):
            if kind:
                agents += 1
                like, other = _like(g, r, c, kind)
                happy += _happy(g, r, c, kind, tol)
                if like + other:
                    shares.append(Fraction(like, like + other))
    return (Fraction(happy, agents) if agents else Fraction(1)), (sum(shares) / len(shares) if shares else Fraction(0))


def agent_based_schelling(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise SchellingError("data keys must be exactly grid, tol_num, tol_den, max_rounds")
    den = _int(data["tol_den"], 1, MAX_DEN, "tol_den")
    num = _int(data["tol_num"], 0, den, "tol_num")
    rounds_cap = _int(data["max_rounds"], 1, MAX_ROUNDS, "max_rounds")
    rows = data["grid"]
    if not isinstance(rows, list):
        raise SchellingError("grid must be a list")
    if not MIN_SIDE <= len(rows) <= MAX_SIDE:
        raise SchellingError("grid height out of range")
    width = None
    grid = []
    for row in rows:
        if not isinstance(row, list):
            raise SchellingError("grid row must be a list")
        if not MIN_SIDE <= len(row) <= MAX_SIDE:
            raise SchellingError("grid width out of range")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise SchellingError("grid rows must have equal length")
        grid.append([_int(v, 0, 2, "cell") for v in row])
    tol = Fraction(num, den)
    start_happy, start_seg = _stats(grid, tol)
    moves_per_round = []
    settled = False
    for _ in range(rounds_cap):
        moves = 0
        for r in range(len(grid)):
            for c in range(width):
                kind = grid[r][c]
                if kind == 0 or _happy(grid, r, c, kind, tol):
                    continue
                grid[r][c] = 0
                target = None
                for r2 in range(len(grid)):
                    for c2 in range(width):
                        if grid[r2][c2] == 0 and (r2, c2) != (r, c) and _happy(grid, r2, c2, kind, tol):
                            target = (r2, c2)
                            break
                    if target:
                        break
                if target is None:
                    grid[r][c] = kind
                else:
                    grid[target[0]][target[1]] = kind
                    moves += 1
        moves_per_round.append(moves)
        if moves == 0:
            settled = True
            break
    end_happy, end_seg = _stats(grid, tol)
    return {
        "grid": [list(row) for row in grid],
        "rounds": len(moves_per_round),
        "moves_per_round": moves_per_round,
        "settled": settled,
        "happy_share_start": str(start_happy),
        "happy_share_end": str(end_happy),
        "segregation_start": str(start_seg),
        "segregation_end": str(end_seg),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }

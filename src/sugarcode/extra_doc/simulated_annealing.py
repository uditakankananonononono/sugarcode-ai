"""Simulated Annealing - exact deterministic annealing run over a caller-supplied landscape.

Pure function over caller data. No retrieval, no network, no clock, no floats and no
hidden randomness: choices come from a fixed integer generator seeded by the caller.
Input: landscape (3..40 integers, -1000..1000, the cost at each position), start (position
index), steps (integer 1..100), t0 (integer 1..1000, the starting temperature), cool_num /
cool_den (cooling ratio r = cool_num / cool_den, cool_den 1..100, cool_num 1..cool_den) and
seed (integer 0..2147483647). The temperature at step k (k = 0, 1, ...) is the exact
Fraction t0 * r^k. Generator: x -> (1103515245 * x + 12345) mod 2^31, output x >> 16.
Each step draws a direction (output mod 2: 0 is left, 1 is right); a move off either end
is rejected. Otherwise with delta = cost(new) - cost(current): delta <= 0 is accepted
without a draw; delta > 0 draws u = output mod 32768 and is accepted exactly when
u * (T + delta) < T * 32768, that is with probability T / (T + delta). This is the
rational-acceptance variant of annealing (not the exponential Metropolis rule), chosen so
every decision is exact. The result gives the best position and cost seen, the final
position, the path of positions (steps + 1 entries), the counts of downhill or level
moves, accepted uphill moves, rejected uphill moves and moves off the ends, and the
landscape minimum with whether the best cost equals it.

Scope: PARTIAL for the Simulated Annealing line. It anneals on a one-dimensional table
with unit moves, one geometric schedule and the rational acceptance rule above. No
exponential Metropolis rule, other neighbourhoods, reheating, restarts or multiple chains,
and no guarantee of finding the minimum.

Not claimed: that the run finds the global minimum, that the acceptance rule matches the
Metropolis rule, that the generator is statistically strong, or anything about the real
world. Every claim flag in the result is False.
"""
from fractions import Fraction

MIN_N = 3
MAX_N = 40
MAX_COST = 1000
MAX_STEPS = 100
MAX_T0 = 1000
MAX_DEN = 100
MAX_SEED = 2147483647
_TOP = frozenset({"landscape", "start", "steps", "t0", "cool_num", "cool_den", "seed"})
_A, _C, _M = 1103515245, 12345, 2 ** 31

NOT_CLAIMED = (
    "the run finds the global minimum",
    "the acceptance rule matches the Metropolis rule",
    "the generator is statistically strong",
    "real-world outcome",
)
CLAIMS = {"finds_minimum": False, "metropolis": False, "generator_strong": False, "real_world": False}


class AnnealingError(ValueError):
    pass


def _int(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise AnnealingError(f"{name} must be an int")
    if v < lo or v > hi:
        raise AnnealingError(f"{name} out of range")
    return v


def simulated_annealing(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise AnnealingError("data keys must be exactly landscape, start, steps, t0, cool_num, cool_den, seed")
    land_in = data["landscape"]
    if not isinstance(land_in, list):
        raise AnnealingError("landscape must be a list")
    if not MIN_N <= len(land_in) <= MAX_N:
        raise AnnealingError("landscape length out of range")
    n = len(land_in)
    start = _int(data["start"], 0, n - 1, "start")
    steps = _int(data["steps"], 1, MAX_STEPS, "steps")
    t0 = _int(data["t0"], 1, MAX_T0, "t0")
    den = _int(data["cool_den"], 1, MAX_DEN, "cool_den")
    num = _int(data["cool_num"], 1, den, "cool_num")
    seed = _int(data["seed"], 0, MAX_SEED, "seed")
    land = [_int(v, -MAX_COST, MAX_COST, "cost") for v in land_in]
    state = seed

    def draw():
        nonlocal state
        state = (_A * state + _C) % _M
        return state >> 16

    ratio = Fraction(num, den)
    temp = Fraction(t0)
    cur = start
    best = (land[cur], cur)
    path = [cur]
    down = up_taken = up_refused = off_end = 0
    for _ in range(steps):
        nxt = cur + (1 if draw() % 2 else -1)
        if nxt < 0 or nxt >= n:
            off_end += 1
        else:
            delta = land[nxt] - land[cur]
            if delta <= 0:
                cur = nxt
                down += 1
            elif draw() % 32768 * (temp + delta) < temp * 32768:
                cur = nxt
                up_taken += 1
            else:
                up_refused += 1
            if land[cur] < best[0]:
                best = (land[cur], cur)
        path.append(cur)
        temp = temp * ratio
    low = min(land)
    return {
        "best_cost": best[0],
        "best_position": best[1],
        "final_position": cur,
        "path": path,
        "downhill_or_level_moves": down,
        "uphill_accepted": up_taken,
        "uphill_refused": up_refused,
        "off_end_rejected": off_end,
        "landscape_minimum": low,
        "best_is_minimum": best[0] == low,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }

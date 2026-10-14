"""Kriging - exact ordinary kriging over caller-supplied points, values and variogram.

Pure function over caller data. No retrieval, no network, no clock, no floats.
Input: points (2..20 distinct integer [u, v] pairs, each -1000..1000), values (one
integer -1000..1000 per point), nugget (integer 0..1000), slope (integer 1..1000) and
targets (1..10 integer [u, v] pairs, same range). Distance is the Manhattan distance
h = |du| + |dv| and the semivariogram is the linear model gamma(0) = 0 and
gamma(h) = nugget + slope * h for h > 0, so every entry is an integer. For each target the
ordinary kriging system (weights summing to 1, with a Lagrange multiplier mu) is solved
exactly. The result per target is the weights, mu, the prediction (the weighted sum of
the values) and the kriging variance sum(weight_i * gamma(target, point_i)) + mu, all as
exact Fractions in strings. Because the variogram is a metric of negative type the
system is non-singular for distinct points.

Scope: PARTIAL for the Kriging line. It does ordinary kriging with one fixed linear
variogram in Manhattan distance. It fits no variogram to data, offers no spherical,
exponential or Gaussian model (those need roots or exponentials, which are not exact),
does no universal or co-kriging, uses no search neighbourhood and gives no confidence
interval.

Not claimed: that the linear variogram suits the data, that the field is stationary, that
the prediction is accurate, that the coordinates are real, or anything about the real
world. Every claim flag in the result is False.
"""
from fractions import Fraction

MIN_N = 2
MAX_N = 20
MAX_TARGETS = 10
MAX_VALUE = 1000
MAX_PARAM = 1000
_TOP = frozenset({"points", "values", "nugget", "slope", "targets"})

NOT_CLAIMED = (
    "the linear variogram suits the data",
    "the field is stationary",
    "the prediction is accurate",
    "the coordinates are real locations",
    "real-world outcome",
)
CLAIMS = {"variogram_suitable": False, "stationary": False, "accurate": False, "coordinates_real": False, "real_world": False}


class KrigingError(ValueError):
    pass


def _int(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise KrigingError(f"{name} must be an int")
    if v < lo or v > hi:
        raise KrigingError(f"{name} out of range")
    return v


def _list(v, lo, hi, name):
    if not isinstance(v, list):
        raise KrigingError(f"{name} must be a list")
    if not lo <= len(v) <= hi:
        raise KrigingError(f"{name} length out of range")
    return v


def _pt(p):
    if not isinstance(p, list) or len(p) != 2:
        raise KrigingError("point must be a [u, v] list")
    return (_int(p[0], -MAX_VALUE, MAX_VALUE, "coordinate"), _int(p[1], -MAX_VALUE, MAX_VALUE, "coordinate"))


def _solve(a, b):
    n = len(a)
    m = [[Fraction(x) for x in row] + [Fraction(y)] for row, y in zip(a, b)]
    for c in range(n):
        # the matrix is non-singular for distinct points, so some row at or below c has a pivot
        p = next(r for r in range(c, n) if m[r][c] != 0)
        m[c], m[p] = m[p], m[c]
        piv = m[c][c]
        m[c] = [x / piv for x in m[c]]
        for r in range(n):
            if r != c and m[r][c] != 0:
                f = m[r][c]
                m[r] = [x - f * y for x, y in zip(m[r], m[c])]
    return [m[r][n] for r in range(n)]


def kriging(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise KrigingError("data keys must be exactly points, values, nugget, slope, targets")
    pts_in = _list(data["points"], MIN_N, MAX_N, "points")
    vals_in = _list(data["values"], MIN_N, MAX_N, "values")
    if len(pts_in) != len(vals_in):
        raise KrigingError("points and values must have the same length")
    tg_in = _list(data["targets"], 1, MAX_TARGETS, "targets")
    nugget = _int(data["nugget"], 0, MAX_PARAM, "nugget")
    slope = _int(data["slope"], 1, MAX_PARAM, "slope")
    pts = [_pt(p) for p in pts_in]
    if len(set(pts)) != len(pts):
        raise KrigingError("points must be distinct")
    vals = [_int(v, -MAX_VALUE, MAX_VALUE, "value") for v in vals_in]
    targets = [_pt(p) for p in tg_in]

    def gamma(p, q):
        h = abs(p[0] - q[0]) + abs(p[1] - q[1])
        return 0 if h == 0 else nugget + slope * h

    n = len(pts)
    a = [[gamma(pts[i], pts[j]) for j in range(n)] + [1] for i in range(n)] + [[1] * n + [0]]
    out = []
    for t in targets:
        g0 = [gamma(p, t) for p in pts]
        sol = _solve(a, g0 + [1])
        lam, mu = sol[:n], sol[n]
        out.append({
            "target": list(t),
            "weights": [str(w) for w in lam],
            "multiplier": str(mu),
            "prediction": str(sum(w * v for w, v in zip(lam, vals))),
            "variance": str(sum(w * g for w, g in zip(lam, g0)) + mu),
        })
    return {
        "points": n,
        "predictions": out,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }

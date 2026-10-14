"""Point Pattern Analysis - exact quadrat, nearest-neighbour and Ripley K summaries.

Pure function over caller data. No retrieval, no network, no clock, no floats.
Input: width and height (integers 1..1000, the window [0, width) x [0, height)), points
(3..50 integer [x, y] pairs inside the window, repeats allowed), nx and ny (quadrat grid,
integers 1..10 with nx * ny at least 2), radii_squared (1..5 strictly increasing integers
1..2000000, squared radii) and critical (None, or [num, den] with num 0..1000000 and den
1..1000000). The result has:
  quadrat: the counts per cell (row-major, cell = x * nx // width, y * ny // height), the
    mean count, the sample variance, the variance-to-mean ratio, the chi-square statistic
    sum((count - mean)^2 / mean), its degrees of freedom (cells - 1) and, when critical is
    given, whether the statistic exceeds num / den (strictly, exact);
  nearest_neighbour: each point's squared distance to its nearest other point (a repeated
    point gives 0) and the mean of those squared distances;
  ripley_k: for each squared radius r2 the number of ordered pairs with squared distance at
    most r2 and K = window_area * pairs / (n * (n - 1)), with no edge correction.
All values are exact Fractions in strings or integers.

Scope: PARTIAL for the Point Pattern Analysis line. It summarises one pattern in a
rectangular window. It computes no expected value under complete spatial randomness (that
needs pi and roots), no p-value, no Clark-Evans index, no edge correction, no marks, no
space-time or inhomogeneous model.

Not claimed: that the pattern is clustered, random or regular, that the window is the
right study region, that the coordinates are real, or anything about the real world. Every
claim flag in the result is False.
"""
from fractions import Fraction

MIN_N = 3
MAX_N = 50
MAX_SIDE = 1000
MAX_GRID = 10
MAX_RADII = 5
MAX_R2 = 2000000
MAX_CRIT = 1000000
_TOP = frozenset({"width", "height", "points", "nx", "ny", "radii_squared", "critical"})

NOT_CLAIMED = (
    "the pattern is clustered, random or regular",
    "the window is the right study region",
    "the coordinates are real locations",
    "real-world outcome",
)
CLAIMS = {"pattern_type": False, "window_valid": False, "coordinates_real": False, "real_world": False}


class PointPatternError(ValueError):
    pass


def _int(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise PointPatternError(f"{name} must be an int")
    if v < lo or v > hi:
        raise PointPatternError(f"{name} out of range")
    return v


def point_pattern(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise PointPatternError("data keys must be exactly width, height, points, nx, ny, radii_squared, critical")
    w = _int(data["width"], 1, MAX_SIDE, "width")
    h = _int(data["height"], 1, MAX_SIDE, "height")
    nx = _int(data["nx"], 1, MAX_GRID, "nx")
    ny = _int(data["ny"], 1, MAX_GRID, "ny")
    if nx * ny < 2:
        raise PointPatternError("grid must have at least 2 cells")
    pts_in = data["points"]
    if not isinstance(pts_in, list):
        raise PointPatternError("points must be a list")
    if not MIN_N <= len(pts_in) <= MAX_N:
        raise PointPatternError("points length out of range")
    rad_in = data["radii_squared"]
    if not isinstance(rad_in, list):
        raise PointPatternError("radii_squared must be a list")
    if not 1 <= len(rad_in) <= MAX_RADII:
        raise PointPatternError("radii_squared length out of range")
    crit = data["critical"]
    if crit is not None:
        if not isinstance(crit, list) or len(crit) != 2:
            raise PointPatternError("critical must be null or a [num, den] list")
        for c in crit:
            if isinstance(c, bool) or not isinstance(c, int):
                raise PointPatternError("critical parts must be ints")
        if not 0 <= crit[0] <= MAX_CRIT or not 1 <= crit[1] <= MAX_CRIT:
            raise PointPatternError("critical out of range")
    pts = []
    for p in pts_in:
        if not isinstance(p, list) or len(p) != 2:
            raise PointPatternError("point must be an [x, y] list")
        x = _int(p[0], 0, w - 1, "x")
        y = _int(p[1], 0, h - 1, "y")
        pts.append((x, y))
    radii = [_int(r, 1, MAX_R2, "radius squared") for r in rad_in]
    if any(b <= a for a, b in zip(radii, radii[1:])):
        raise PointPatternError("radii_squared must be strictly increasing")
    n = len(pts)
    cells = nx * ny
    counts = [0] * cells
    for x, y in pts:
        counts[(y * ny // h) * nx + (x * nx // w)] += 1
    mean = Fraction(n, cells)
    ss = sum((c - mean) ** 2 for c in counts)
    var = ss / (cells - 1)
    chi = ss / mean
    exceeds = None if crit is None else chi > Fraction(crit[0], crit[1])
    d2 = [[(a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 for b in pts] for a in pts]
    nn = [min(d2[i][j] for j in range(n) if j != i) for i in range(n)]
    area = w * h
    ripley = []
    for r2 in radii:
        pairs = sum(1 for i in range(n) for j in range(n) if i != j and d2[i][j] <= r2)
        ripley.append({"radius_squared": r2, "ordered_pairs": pairs,
                       "k": str(Fraction(area * pairs, n * (n - 1)))})
    return {
        "points": n,
        "window_area": area,
        "quadrat": {
            "counts": counts,
            "mean": str(mean),
            "variance": str(var),
            "variance_to_mean": str(var / mean),
            "chi_square": str(chi),
            "degrees_of_freedom": cells - 1,
            "exceeds_critical": exceeds,
        },
        "nearest_neighbour": {"squared_distances": nn, "mean_squared_distance": str(Fraction(sum(nn), n))},
        "ripley_k": ripley,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }

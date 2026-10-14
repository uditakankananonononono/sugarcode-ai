"""Row 279 game narrative design (PARTIAL): story-tension versus mechanic-intensity alignment.

Computes coverage, per-beat gaps and a Pearson correlation from supplied numbers only.
No story quality, fun, pacing taste or player-experience judgement is made."""
import math
from fractions import Fraction

MAX_BEATS = 200
MAX_MECHANICS = 200
MAX_LINKS = 1000
MAX_ID = 40
SCALE_MAX = 10
DEFAULT_THRESHOLD = 3
STATUS_NOTE = ("PARTIAL: arithmetic over supplied tension and intensity numbers and beat-mechanic links; "
               "no judgement of story quality, fun or player experience")


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float, Fraction)):
        raise ValueError(f"{name}: number required")
    if abs(v) > 1e9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return Fraction(v)


def _items(v, name, cap, field):
    if not isinstance(v, (list, tuple)) or not 1 <= len(v) <= cap:
        raise ValueError(f"{name}: list of 1..{cap} entries required")
    out, seen = [], set()
    for i, e in enumerate(v):
        if not isinstance(e, dict):
            raise ValueError(f"{name}[{i}]: dict required")
        k = e.get("id")
        if not isinstance(k, str) or not 1 <= len(k) <= MAX_ID:
            raise ValueError(f"{name}[{i}]: id must be a string of 1..{MAX_ID} characters")
        if k in seen:
            raise ValueError(f"{name}[{i}]: duplicate id {k!r}")
        seen.add(k)
        out.append((k, _num(e.get(field), f"{name}[{i}].{field}", 0, SCALE_MAX)))
    return out


def analyze_alignment(beats, mechanics, links, threshold=DEFAULT_THRESHOLD):
    b = _items(beats, "beats", MAX_BEATS, "tension")
    m = dict(_items(mechanics, "mechanics", MAX_MECHANICS, "intensity"))
    th = _num(threshold, "threshold", 0, SCALE_MAX)
    if not isinstance(links, (list, tuple)) or len(links) > MAX_LINKS:
        raise ValueError(f"links: list of at most {MAX_LINKS} entries required")
    bid = {k for k, _ in b}
    linked, seen = {}, set()
    for i, e in enumerate(links):
        if not isinstance(e, dict) or e.get("beat") not in bid or e.get("mechanic") not in m:
            raise ValueError(f"links[{i}]: beat and mechanic must name supplied ids")
        pair = (e["beat"], e["mechanic"])
        if pair in seen:
            raise ValueError(f"links[{i}]: duplicate link {pair!r}")
        seen.add(pair)
        linked.setdefault(e["beat"], []).append(e["mechanic"])
    rows, xs, ys = [], [], []
    for k, t in b:
        if k not in linked:
            rows.append({"beat": k, "tension": float(t), "intensity": None, "gap": None, "dissonant": None})
            continue
        inten = sum(m[x] for x in linked[k]) / len(linked[k])
        gap = t - inten
        xs.append(t)
        ys.append(inten)
        rows.append({"beat": k, "tension": float(t), "intensity": float(inten), "gap": float(gap),
                     "dissonant": abs(gap) >= th})
    n = len(xs)
    corr = None
    if n >= 2:
        mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        if sxx and syy:
            r2 = sxy * sxy / (sxx * syy)      # exact (Cauchy-Schwarz keeps it <= 1); float() of a Fraction cannot underflow the inputs
            corr = math.copysign(math.sqrt(float(r2)), sxy)
    used = {x for v in linked.values() for x in v}
    return {
        "beats": rows,
        "coverage": float(Fraction(n, len(b))),
        "mean_abs_gap": float(sum(abs(x - y) for x, y in zip(xs, ys)) / n) if n else None,
        "correlation": corr,
        "unlinked_beats": [k for k, _ in b if k not in linked],
        "unused_mechanics": [k for k in m if k not in used],
        "threshold": float(th),
        "status_note": STATUS_NOTE,
    }

"""Row 320 medical illustration (PARTIAL): label-column layout and leader-line crossing count for an annotated figure.

Labels sit in a column at x = label_x. Each label's y slot is the anchor y pushed apart by a minimum gap and kept
inside the figure height; leader lines run from anchor to slot. Reports slots, displacement and how many leader
pairs cross. Layout arithmetic only: no anatomy, no procedure, no clinical or educational-accuracy claim."""
import math

MAX_LABELS = 200
STATUS_NOTE = ("PARTIAL: label-column layout and leader-line crossing count; feasible, not displacement-optimal; "
               "no anatomical, procedural or clinical claim")


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name}: number required")
    if abs(v) > 1e9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return v


def _ccw(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _cross(p, q, r, s):
    d1, d2, d3, d4 = _ccw(r, s, p), _ccw(r, s, q), _ccw(p, q, r), _ccw(p, q, s)
    return d1 * d2 < 0 and d3 * d4 < 0


def layout_labels(anchors, height, label_x, gap):
    """anchors: list of (x, y). Returns slots in input order."""
    if not isinstance(anchors, (list, tuple)) or not 1 <= len(anchors) <= MAX_LABELS:
        raise ValueError(f"anchors: 1 to {MAX_LABELS} required")
    h = _num(height, "height", 1, 100000)
    lx = _num(label_x, "label_x", 0, 100000)
    g = _num(gap, "gap", 0, 1000)
    pts = []
    for a in anchors:
        if not isinstance(a, (list, tuple)) or len(a) != 2:
            raise ValueError("anchor: (x, y) required")
        x = _num(a[0], "x", 0, 100000)
        y = _num(a[1], "y", 0, h)
        pts.append((x, y))
    n = len(pts)
    if g * (n - 1) > h:
        raise ValueError("labels do not fit at this gap")
    order = sorted(range(n), key=lambda i: (pts[i][1], pts[i][0], i))
    slot = [0] * n
    prev = None
    for i in order:
        want = pts[i][1] if prev is None else max(pts[i][1], prev + g)
        slot[i] = want
        prev = want
    nxt = None
    for i in reversed(order):
        top = h if nxt is None else min(h, nxt - g)
        slot[i] = min(slot[i], top)
        nxt = slot[i]
    leaders = [((pts[i][0], pts[i][1]), (lx, slot[i])) for i in range(n)]
    crossings = sum(1 for i in range(n) for j in range(i + 1, n) if _cross(*leaders[i], *leaders[j]))
    return {"slots": slot, "displacement": [abs(slot[i] - pts[i][1]) for i in range(n)], "crossings": crossings,
            "status": STATUS_NOTE}

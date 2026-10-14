"""Row 282 composition principles (PARTIAL): geometry of supplied rectangles on a canvas.

Computes bounds, overlaps, visual-mass balance and rule-of-thirds proximity from integer boxes only.
No judgement of aesthetics, hierarchy, subject matter or design quality is made."""
from fractions import Fraction

MAX_ELEMENTS = 100
MAX_CANVAS = 10000
MAX_COORD = 100000
MAX_WEIGHT = 100
MAX_ID = 40
BALANCE_TOLERANCE = Fraction(1, 10)
THIRDS_TOLERANCE = Fraction(1, 20)
STATUS_NOTE = ("PARTIAL: rectangle geometry, area-weighted balance and thirds proximity over supplied integer boxes; "
               "no judgement of aesthetics, hierarchy or design quality")


def _int(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: integer required")
    if abs(v) > MAX_COORD:
        raise ValueError(f"{name}: magnitude above {MAX_COORD}")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return v


def analyze_composition(canvas_w, canvas_h, elements):
    cw = _int(canvas_w, "canvas_w", 1, MAX_CANVAS)
    ch = _int(canvas_h, "canvas_h", 1, MAX_CANVAS)
    if not isinstance(elements, (list, tuple)) or not 1 <= len(elements) <= MAX_ELEMENTS:
        raise ValueError(f"elements: list of 1..{MAX_ELEMENTS} entries required")
    els, seen = [], set()
    for i, e in enumerate(elements):
        if not isinstance(e, dict):
            raise ValueError(f"elements[{i}]: dict required")
        k = e.get("id")
        if not isinstance(k, str) or not 1 <= len(k) <= MAX_ID:
            raise ValueError(f"elements[{i}]: id must be a string of 1..{MAX_ID} characters")
        if k in seen:
            raise ValueError(f"elements[{i}]: duplicate id {k!r}")
        seen.add(k)
        x = _int(e.get("x"), f"elements[{i}].x", -MAX_COORD, MAX_COORD)
        y = _int(e.get("y"), f"elements[{i}].y", -MAX_COORD, MAX_COORD)
        w = _int(e.get("w"), f"elements[{i}].w", 1, MAX_COORD)
        h = _int(e.get("h"), f"elements[{i}].h", 1, MAX_COORD)
        wt = _int(e.get("weight", 1), f"elements[{i}].weight", 1, MAX_WEIGHT)
        els.append((k, x, y, w, h, wt))
    out_of_bounds = [k for k, x, y, w, h, _ in els if x < 0 or y < 0 or x + w > cw or y + h > ch]
    overlaps = []
    for a in range(len(els)):
        for b in range(a + 1, len(els)):
            ka, xa, ya, wa, ha, _ = els[a]
            kb, xb, yb, wb, hb, _ = els[b]
            ox = min(xa + wa, xb + wb) - max(xa, xb)
            oy = min(ya + ha, yb + hb) - max(ya, yb)
            if ox > 0 and oy > 0:
                overlaps.append({"a": ka, "b": kb, "area": ox * oy})
    mass = sum(w * h * wt for _, _, _, w, h, wt in els)
    mx = sum(Fraction(2 * x + w, 2) * w * h * wt for _, x, _, w, h, wt in els) / mass
    my = sum(Fraction(2 * y + h, 2) * w * h * wt for _, _, y, w, h, wt in els) / mass
    dx = (mx - Fraction(cw, 2)) / cw
    dy = (my - Fraction(ch, 2)) / ch
    per = []
    for k, x, y, w, h, wt in els:
        cx, cy = Fraction(2 * x + w, 2), Fraction(2 * y + h, 2)
        best = None
        for px in (Fraction(cw, 3), Fraction(2 * cw, 3)):
            for py in (Fraction(ch, 3), Fraction(2 * ch, 3)):
                ex, ey = abs(cx - px) / cw, abs(cy - py) / ch
                if best is None or ex + ey < best[0]:
                    best = (ex + ey, ex, ey)
        per.append({"id": k, "on_thirds": best[1] <= THIRDS_TOLERANCE and best[2] <= THIRDS_TOLERANCE,
                    "thirds_offset": float(best[0]),
                    "margin": min(x, y, cw - x - w, ch - y - h)})
    return {"out_of_bounds": out_of_bounds, "overlaps": overlaps,
            "centroid": [float(mx), float(my)], "balance_offset": [float(dx), float(dy)],
            "balanced": abs(dx) <= BALANCE_TOLERANCE and abs(dy) <= BALANCE_TOLERANCE,
            "elements": per, "status_note": STATUS_NOTE}

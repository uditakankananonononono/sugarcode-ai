"""Row 284 logo design (PARTIAL): raster geometry diagnostics for a supplied rectangle-based mark.

Paints rectangles on a small integer grid and reports colour count, coverage, mirror symmetry,
shape count and small-size feature survival. No judgement of memorability, originality or brand fit."""
from fractions import Fraction

MAX_GRID = 64
MIN_GRID = 4
MAX_SHAPES = 40
MAX_COLOR = 20
SIMPLE_MAX_SHAPES = 5
SIMPLE_MAX_COLORS = 3
MIN_FEATURE_PX = 2
MAX_RENDER = 4096
STATUS_NOTE = ("PARTIAL: pixel-grid diagnostics of supplied rectangles (colours, coverage, mirror symmetry, "
               "small-size feature survival); no judgement of memorability, originality or brand fit")


def _int(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: integer required")
    if abs(v) > 10 ** 6:
        raise ValueError(f"{name}: magnitude above 1000000")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return v


def analyze_logo(grid, shapes, render_px=16):
    n = _int(grid, "grid", MIN_GRID, MAX_GRID)
    rp = _int(render_px, "render_px", 1, MAX_RENDER)
    if not isinstance(shapes, (list, tuple)) or not 1 <= len(shapes) <= MAX_SHAPES:
        raise ValueError(f"shapes: list of 1..{MAX_SHAPES} entries required")
    parsed = []
    for i, s in enumerate(shapes):
        if not isinstance(s, dict):
            raise ValueError(f"shapes[{i}]: dict required")
        col = s.get("color")
        if not isinstance(col, str) or not 1 <= len(col) <= MAX_COLOR:
            raise ValueError(f"shapes[{i}]: color must be a string of 1..{MAX_COLOR} characters")
        x = _int(s.get("x"), f"shapes[{i}].x", 0, n - 1)
        y = _int(s.get("y"), f"shapes[{i}].y", 0, n - 1)
        w = _int(s.get("w"), f"shapes[{i}].w", 1, n - x)
        h = _int(s.get("h"), f"shapes[{i}].h", 1, n - y)
        parsed.append((x, y, w, h, col))
    px = [[None] * n for _ in range(n)]
    for x, y, w, h, col in parsed:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                px[yy][xx] = col
    filled = sum(1 for row in px for v in row if v is not None)
    colors = sorted({v for row in px for v in row if v is not None})
    lr = sum(1 for row in px for j in range(n) if row[j] == row[n - 1 - j])
    ud = sum(1 for i in range(n) for j in range(n) if px[i][j] == px[n - 1 - i][j])
    total = n * n
    small = [i for i, (_, _, w, h, _) in enumerate(parsed) if Fraction(min(w, h) * rp, n) < MIN_FEATURE_PX]
    return {
        "pixels": [[v for v in row] for row in px],
        "visible_colors": colors,
        "coverage": float(Fraction(filled, total)),
        "mirror_lr": float(Fraction(lr, total)),
        "mirror_ud": float(Fraction(ud, total)),
        "shape_count": len(parsed),
        "simple": len(parsed) <= SIMPLE_MAX_SHAPES and len(colors) <= SIMPLE_MAX_COLORS,
        "small_feature_shapes": small,
        "status_note": STATUS_NOTE,
    }

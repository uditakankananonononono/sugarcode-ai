"""Rendering Engine - exact software rasteriser for filled triangles on a character grid.

Pure function over caller data. No GPU, no files, no network, no clock, no floats, no
randomness. Input: width and height, ints 1..32; shapes, 0..20 dicts with exactly the
keys points (three [x, y] int pairs, each -100..100, not on one line) and color (one
character from A-Z a-z 0-9). The canvas starts as '.' everywhere.

Rule: pixel (x, y), x in 0..width-1 and y in 0..height-1, is sampled at its centre
(x + 1/2, y + 1/2). A triangle covers a pixel when the centre is inside it or on its
edge (boundary inclusive, no top-left rule). Shapes are painted in list order, so later
shapes overwrite earlier ones. The result gives the canvas as a list of row strings
(row 0 first) and, per shape, the number of pixels it covers (before overwriting) and
the final count of pixels showing each colour used (a colour shared by shapes is counted once).

Scope: PARTIAL for the Rendering Engine line. Exact flat-colour triangle rasterisation
with one sampling rule. It is not a rendering engine in the general sense: no 3D, no
shading, no textures, no anti-aliasing, no clipping beyond the canvas.

Not claimed: that the picture looks right to people, that the sampling rule matches any
graphics API, that the output is a real image file, or anything about the real world.
Every claim flag in the result is False.
"""
import string

MAX_SIDE = 32
MAX_SHAPES = 20
COORD = 100
_TOP = frozenset({"width", "height", "shapes"})
_SHAPE = frozenset({"points", "color"})
_COLORS = frozenset(string.ascii_letters + string.digits)

NOT_CLAIMED = (
    "the picture looks right to people",
    "the sampling rule matches any graphics API",
    "the output is a real image file",
    "real-world outcome",
)
CLAIMS = {"looks_right": False, "matches_graphics_api": False, "image_file": False, "real_world": False}


class RenderError(ValueError):
    pass


def _int(v, lo, hi, name):
    if type(v) is not int:
        raise RenderError(f"{name} must be an int")
    if v < lo or v > hi:
        raise RenderError(f"{name} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise RenderError("data keys must be exactly height, shapes, width")
    w = _int(data["width"], 1, MAX_SIDE, "width")
    h = _int(data["height"], 1, MAX_SIDE, "height")
    raw = data["shapes"]
    if not isinstance(raw, list) or len(raw) > MAX_SHAPES:
        raise RenderError("shapes must be a list of at most 20 shapes")
    shapes = []
    for s in raw:
        if not isinstance(s, dict) or set(s) != _SHAPE:
            raise RenderError("shape keys must be exactly color, points")
        c = s["color"]
        if not type(c) is str or c not in _COLORS or len(c) != 1:
            raise RenderError("color must be one character from A-Z a-z 0-9")
        pts = s["points"]
        if not isinstance(pts, list) or len(pts) != 3:
            raise RenderError("points must be a list of 3 [x, y] pairs")
        tri = []
        for p in pts:
            if not isinstance(p, list) or len(p) != 2:
                raise RenderError("points must be a list of 3 [x, y] pairs")
            tri.append((_int(p[0], -COORD, COORD, "x"), _int(p[1], -COORD, COORD, "y")))
        (ax, ay), (bx, by), (cx, cy) = tri
        if (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) == 0:
            raise RenderError("points must not lie on one line")
        shapes.append((tri, c))
    return w, h, shapes


def _covers(tri, x, y):
    # all coordinates doubled so the pixel centre (x + 1/2, y + 1/2) is the integer (2x+1, 2y+1)
    px, py = 2 * x + 1, 2 * y + 1
    signs = []
    for i in range(3):
        ax, ay = 2 * tri[i][0], 2 * tri[i][1]
        bx, by = 2 * tri[(i + 1) % 3][0], 2 * tri[(i + 1) % 3][1]
        signs.append((bx - ax) * (py - ay) - (by - ay) * (px - ax))
    return all(s >= 0 for s in signs) or all(s <= 0 for s in signs)


def rendering_engine(data):
    w, h, shapes = _validate(data)
    canvas = [["."] * w for _ in range(h)]
    covered = []
    for tri, c in shapes:
        n = 0
        for y in range(h):
            for x in range(w):
                if _covers(tri, x, y):
                    canvas[y][x] = c
                    n += 1
        covered.append(n)
    flat = "".join("".join(r) for r in canvas)
    return {
        "status": "completed",
        "canvas": ["".join(r) for r in canvas],
        "covered": covered,
        "shown_by_color": {c: flat.count(c) for _, c in shapes},
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }

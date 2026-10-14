import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import rendering_engine as m
from sugarcode.extra_doc.rendering_engine import RenderError, rendering_engine as run

KEYS = "data keys must be exactly height, shapes, width"


def tri(p, c="A"):
    return {"points": [list(q) for q in p], "color": c}


def d(w=4, h=4, shapes=None):
    return {"width": w, "height": h, "shapes": [tri([(0, 0), (4, 0), (0, 4)])] if shapes is None else shapes}


def bad(data, msg):
    with pytest.raises(RenderError) as e:
        run(data)
    assert str(e.value) == msg


def area(a, b, c):
    return abs(F((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]), 2))


def oracle(data):
    """Independent: a pixel centre P is covered iff area(PAB)+area(PBC)+area(PCA) == area(ABC)."""
    rows = [["."] * data["width"] for _ in range(data["height"])]
    cov = []
    for s in data["shapes"]:
        a, b, c = [tuple(p) for p in s["points"]]
        n = 0
        for y in range(data["height"]):
            for x in range(data["width"]):
                p = (F(2 * x + 1, 2), F(2 * y + 1, 2))
                if area(p, a, b) + area(p, b, c) + area(p, c, a) == area(a, b, c):
                    rows[y][x] = s["color"]
                    n += 1
        cov.append(n)
    canvas = ["".join(r) for r in rows]
    flat = "".join(canvas)
    return canvas, cov, {s["color"]: flat.count(s["color"]) for s in data["shapes"]}


def check(data):
    o = run(data)
    cv, cov, by = oracle(data)
    assert (o["canvas"], o["covered"], o["shown_by_color"]) == (cv, cov, by)
    return o


def test_hand_worked_right_triangle():
    o = run(d())
    # triangle (0,0),(4,0),(0,4); centres with x+y+1 <= 4 are inside, x+y+1 = 4 lies on the hypotenuse
    assert o["canvas"] == ["AAAA", "AAA.", "AA..", "A..."]
    assert o["covered"] == [10] and o["shown_by_color"] == {"A": 10}
    assert o["status"] == "completed"
    assert o["claims"] == {"looks_right": False, "matches_graphics_api": False, "image_file": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_orientation_does_not_matter():
    a = run(d(shapes=[tri([(0, 0), (4, 0), (0, 4)])]))
    b = run(d(shapes=[tri([(0, 4), (4, 0), (0, 0)])]))
    c = run(d(shapes=[tri([(4, 0), (0, 4), (0, 0)])]))
    assert a == b == c


def test_boundary_inclusive_and_offcanvas():
    o = check(d(2, 2, [tri([(0, 0), (2, 0), (0, 2)])]))
    assert o["canvas"] == ["AA", "A."]
    o = check(d(3, 3, [tri([(-50, -50), (100, -50), (-50, 100)])]))
    assert o["covered"] == [9]
    o = check(d(3, 3, [tri([(10, 10), (20, 10), (10, 20)])]))
    assert o["covered"] == [0] and o["canvas"] == ["..."] * 3


def test_overwrite_and_shared_colour():
    s = [tri([(0, 0), (4, 0), (0, 4)], "A"), tri([(0, 0), (4, 4), (0, 4)], "B")]
    o = check(d(shapes=s))
    assert o["covered"][0] == 10
    s2 = s + [tri([(0, 0), (1, 0), (0, 1)], "A")]
    o = check(d(shapes=s2))
    assert len(o["shown_by_color"]) == 2
    assert check(d(shapes=[]))["canvas"] == ["...."] * 4


def test_random_against_oracle():
    rng = random.Random(78)
    cols = "ABCxyz019"
    for _ in range(200):
        w, h = rng.randint(1, 9), rng.randint(1, 9)
        shapes = []
        for _ in range(rng.randint(0, 4)):
            while True:
                p = [(rng.randint(-3, 11), rng.randint(-3, 11)) for _ in range(3)]
                if (p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[1][1] - p[0][1]) * (p[2][0] - p[0][0]):
                    break
            shapes.append(tri(p, rng.choice(cols)))
        check(d(w, h, shapes))


def test_caps_and_ranges():
    run(d(32, 32, [tri([(-100, -100), (100, -100), (-100, 100)])] * 20))
    bad(d(33, 1), "width out of range")
    bad(d(0, 1), "width out of range")
    bad(d(1, 33), "height out of range")
    bad(d(1, 0), "height out of range")
    bad(d(shapes=[tri([(0, 0), (1, 0), (0, 1)])] * 21), "shapes must be a list of at most 20 shapes")
    bad(d(shapes=[tri([(0, 0), (1, 0), (0, 1)])] * 10**5), "shapes must be a list of at most 20 shapes")
    bad(d(shapes=[tri([(101, 0), (1, 0), (0, 1)])]), "x out of range")
    bad(d(shapes=[tri([(-101, 0), (1, 0), (0, 1)])]), "x out of range")
    bad(d(shapes=[tri([(0, 101), (1, 0), (0, 1)])]), "y out of range")
    bad(d(shapes=[tri([(0, -101), (1, 0), (0, 1)])]), "y out of range")
    bad(d(shapes=[tri([(0, 0), (1, 1), (2, 2)])]), "points must not lie on one line")
    bad(d(shapes=[tri([(0, 0), (0, 0), (5, 5)])]), "points must not lie on one line")


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(v):
    bad(d(w=v), "width must be an int")
    bad(d(h=v), "height must be an int")
    bad(d(shapes=[tri([(v, 0), (1, 0), (0, 1)])]), "x must be an int")
    bad(d(shapes=[tri([(0, v), (1, 0), (0, 1)])]), "y must be an int")


@pytest.mark.parametrize("c", ["", "AB", ".", " ", "_", "é", "@", "[", "`", "{", "/", ":", None, 1, True, ["A"]])
def test_bad_colour(c):
    bad(d(shapes=[tri([(0, 0), (1, 0), (0, 1)], c)]), "color must be one character from A-Z a-z 0-9")


@pytest.mark.parametrize("c", ["a", "z", "A", "Z", "0", "9"])
def test_colour_edges(c):
    assert check(d(shapes=[tri([(0, 0), (4, 0), (0, 4)], c)]))["shown_by_color"] == {c: 10}


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainers(v):
    x = d()
    x["shapes"] = v
    bad(x, "shapes must be a list of at most 20 shapes")
    bad(d(shapes=[v]), "shape keys must be exactly color, points")
    for pts in (v, [], [[0, 0]] * 2, [[0, 0]] * 4):
        bad(d(shapes=[{"points": pts, "color": "A"}]), "points must be a list of 3 [x, y] pairs")
    for p in (v, [0], [0, 0, 0]):
        bad(d(shapes=[{"points": [p, [1, 0], [0, 1]], "color": "A"}]), "points must be a list of 3 [x, y] pairs")


def test_shape_keys_exact():
    bad(d(shapes=[{"points": [[0, 0], [1, 0], [0, 1]]}]), "shape keys must be exactly color, points")
    bad(d(shapes=[{"color": "A"}]), "shape keys must be exactly color, points")
    bad(d(shapes=[{"points": [[0, 0], [1, 0], [0, 1]], "color": "A", "x": 1}]), "shape keys must be exactly color, points")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("width", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("width", "height", "shapes"):
        x = d()
        del x[k]
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    a["canvas"][0] = "zzzz"
    r = run(x)
    assert r["claims"]["real_world"] is False and r["canvas"][0] == "AAAA" and m.CLAIMS["real_world"] is False


class _SubInt(int):
    pass


class _Quirky(int):
    """int subclass with lying arithmetic and comparisons."""
    def __sub__(self, o):
        return 0

    def __add__(self, o):
        return 1

    def __mul__(self, o):
        return 0

    def __gt__(self, o):
        return False

    def __lt__(self, o):
        return False


def _int_paths(x, path=()):
    if type(x) is int:
        yield path
    elif isinstance(x, dict):
        for k in x:
            yield from _int_paths(x[k], path + (k,))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _int_paths(v, path + (i,))


def _put(x, path, val):
    y = copy.deepcopy(x)
    t = y
    for k in path[:-1]:
        t = t[k]
    t[path[-1]] = val
    return y


def test_int_subclasses_refused_in_every_int_slot():
    base = d()
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(RenderError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x


class _SubStr(str):
    pass


class _LyingStr(str):
    """str subclass that hashes like 1 and equals 1."""
    def __hash__(self):
        return 1

    def __eq__(self, o):
        return o == 1 or str.__eq__(self, o)


def _variants(x):
    """Yield every copy of x with one str leaf or one dict key replaced by bytes or a str subclass."""
    import copy as _c
    def walk(node, path):
        if type(node) is str:
            yield path, "leaf"
        elif isinstance(node, dict):
            for k in node:
                if type(k) is str:
                    yield path + (k,), "key"
                yield from walk(node[k], path + (k,))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, path + (i,))
    for path, kind in walk(x, ()):
        for mk in (lambda s: s.encode(), _SubStr, _LyingStr):
            if kind == "key" and mk is _SubStr:
                continue   # a plain str subclass hashes and compares like its key: indistinguishable as a dict key
            y = _c.deepcopy(x)
            t = y
            for k in path[:-1]:
                t = t[k]
            last = path[-1]
            if kind == "leaf":
                t[last] = mk(t[last])
            else:
                t2 = {}
                for k, v in t.items():
                    t2[mk(k) if k == last else k] = v
                if len(path) == 1:
                    y = t2
                else:
                    u = y
                    for k in path[:-2]:
                        u = u[k]
                    u[path[-2]] = t2
            yield y


def test_nonexact_str_refused_in_every_str_slot_and_key():
    base = d()
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(RenderError):
            run(y)
    assert n >= 4

import itertools
import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc import composition_principles as c

A = c.analyze_composition


def E(i, x, y, w, h, wt=1):
    return {"id": i, "x": x, "y": y, "w": w, "h": h, "weight": wt}


def test_constants():
    assert (c.MAX_ELEMENTS, c.MAX_CANVAS, c.MAX_COORD, c.MAX_WEIGHT, c.MAX_ID) == (100, 10000, 100000, 100, 40)
    assert (c.BALANCE_TOLERANCE, c.THIRDS_TOLERANCE) == (Fraction(1, 10), Fraction(1, 20))
    assert c.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal():
    # canvas 90x60; A 0,0 30x20 (mass 600, centre 15,10); B 60,40 30x20 (mass 1200 with weight 2, centre 75,50); C 20,10 20x20 overlaps A
    r = A(90, 60, [E("A", 0, 0, 30, 20), E("B", 60, 40, 30, 20, 2), E("C", 20, 10, 20, 20)])
    assert r["out_of_bounds"] == []
    assert r["overlaps"] == [{"a": "A", "b": "C", "area": 100}]          # x 20..30 (10) by y 10..20 (10)
    # mass A 600, B 1200, C 400 -> total 2200 ; mx = (15*600 + 75*1200 + 30*400)/2200 = 111000/2200 ; my = (10*600+50*1200+20*400)/2200 = 74000/2200
    assert r["centroid"] == [pytest.approx(111000 / 2200), pytest.approx(74000 / 2200)]
    assert r["balance_offset"] == [pytest.approx((111000 / 2200 - 45) / 90), pytest.approx((74000 / 2200 - 30) / 60)]
    assert r["balanced"] is True                                           # offsets 0.0606 and 0.0606, both within 0.1
    # thirds points x 30,60 ; y 20,40. A centre (15,10): nearest (30,20) -> 15/90 + 10/60
    a = r["elements"][0]
    assert a["thirds_offset"] == pytest.approx(15 / 90 + 10 / 60) and a["on_thirds"] is False and a["margin"] == 0
    b = r["elements"][1]
    assert b["thirds_offset"] == pytest.approx(15 / 90 + 10 / 60) and b["margin"] == 0
    assert r["elements"][2]["margin"] == 10                              # left 20, top 10, right 90-40=50, bottom 60-30=30


def test_on_thirds_and_balance_boundaries():
    # canvas 100x100; thirds at 33.33 and 66.67. 20x20 box centred exactly on (100/3, 100/3) needs x=100/3-10 not integer; use canvas 90
    r = A(90, 90, [E("t", 20, 20, 20, 20)])                  # centre (30,30) = a thirds point
    assert r["elements"][0]["on_thirds"] is True and r["elements"][0]["thirds_offset"] == 0.0
    # tolerance 1/20 of 90 = 4.5 on each axis: centre 34.5 inside, 34.6 impossible (integers) -> use halves via odd width
    assert A(90, 90, [E("t", 24, 20, 21, 20)])["elements"][0]["on_thirds"] is True     # centre x 34.5, offset exactly 4.5
    assert A(90, 90, [E("t", 25, 20, 21, 20)])["elements"][0]["on_thirds"] is False    # centre x 35.5
    assert A(90, 90, [E("t", 20, 24, 20, 21)])["elements"][0]["on_thirds"] is True     # y axis
    assert A(90, 90, [E("t", 20, 25, 20, 21)])["elements"][0]["on_thirds"] is False
    # balance: offset exactly 0.1 is balanced. canvas 100x100, one box 20x20 centre at x=60 => dx=0.1
    assert A(100, 100, [E("b", 50, 40, 20, 20)])["balanced"] is True
    assert A(100, 100, [E("b", 51, 40, 20, 20)])["balanced"] is False
    assert A(100, 100, [E("b", 40, 50, 20, 20)])["balanced"] is True
    assert A(100, 100, [E("b", 40, 51, 20, 20)])["balanced"] is False
    assert A(100, 100, [E("b", 30, 40, 20, 20)])["balanced"] is True       # dx = -0.1
    assert A(100, 100, [E("b", 29, 40, 20, 20)])["balanced"] is False
    assert A(100, 100, [E("b", 40, 30, 20, 20)])["balanced"] is True
    assert A(100, 100, [E("b", 40, 29, 20, 20)])["balanced"] is False
    assert A(100, 100, [E("b", 40, 40, 20, 20)])["balance_offset"] == [0.0, 0.0]


def test_nearest_thirds_point_picks_each_quadrant():
    # canvas 90x90, points (30,30) (30,60) (60,30) (60,60)
    for cx, cy, want in [(30, 30, 0.0), (60, 60, 0.0), (30, 60, 0.0), (60, 30, 0.0)]:
        assert A(90, 90, [E("t", cx - 5, cy - 5, 10, 10)])["elements"][0]["thirds_offset"] == want
    # centre (50,40): distances to (60,30): 10/90+10/90 ; to (30,30): 20/90+10/90 -> min 20/90
    assert A(90, 90, [E("t", 45, 35, 10, 10)])["elements"][0]["thirds_offset"] == pytest.approx(20 / 90)
    # non-square canvas, centre (45,45) of 90x60: points x30/60 y20/40 -> |45-30|/90 + |45-40|/60 = 1/6+1/12
    assert A(90, 60, [E("t", 40, 40, 10, 10)])["elements"][0]["thirds_offset"] == pytest.approx(0.25)


def test_bounds_and_margin():
    r = A(100, 50, [E("in", 0, 0, 100, 50), E("l", -1, 0, 10, 10), E("t", 0, -1, 10, 10), E("r", 91, 0, 10, 10),
                    E("b", 0, 41, 10, 10), E("ok", 10, 10, 10, 10)])
    assert r["out_of_bounds"] == ["l", "t", "r", "b"]
    m = {e["id"]: e["margin"] for e in r["elements"]}
    assert m == {"in": 0, "l": -1, "t": -1, "r": -1, "b": -1, "ok": 10}
    assert A(100, 50, [E("a", 5, 7, 10, 10)])["elements"][0]["margin"] == 5
    assert A(100, 50, [E("a", 20, 7, 10, 10)])["elements"][0]["margin"] == 7
    assert A(100, 50, [E("a", 70, 20, 10, 10)])["elements"][0]["margin"] == 20
    assert A(100, 50, [E("a", 20, 30, 10, 10)])["elements"][0]["margin"] == 10


def test_overlaps_match_pixel_raster_oracle():
    rng = random.Random(282)
    for _ in range(60):
        n = rng.randint(2, 5)
        els = [E(f"e{i}", rng.randint(-3, 8), rng.randint(-3, 8), rng.randint(1, 6), rng.randint(1, 6)) for i in range(n)]
        r = A(12, 12, els)
        pix = [{(px, py) for px in range(e["x"], e["x"] + e["w"]) for py in range(e["y"], e["y"] + e["h"])} for e in els]
        want = [{"a": els[a]["id"], "b": els[b]["id"], "area": len(pix[a] & pix[b])}
                for a, b in itertools.combinations(range(n), 2) if pix[a] & pix[b]]
        assert r["overlaps"] == want
        oob = [e["id"] for e, p in zip(els, pix) if any(not (0 <= px < 12 and 0 <= py < 12) for px, py in p)]
        assert r["out_of_bounds"] == oob
        mass = sum(e["w"] * e["h"] for e in els)
        mx = sum(Fraction(2 * e["x"] + e["w"], 2) * e["w"] * e["h"] for e in els) / mass
        assert r["centroid"][0] == pytest.approx(float(mx), abs=1e-12)


def test_touching_edges_do_not_overlap():
    assert A(100, 100, [E("a", 0, 0, 10, 10), E("b", 10, 0, 10, 10), E("c", 0, 10, 10, 10)])["overlaps"] == []
    assert A(100, 100, [E("a", 0, 0, 10, 10), E("b", 9, 9, 10, 10)])["overlaps"] == [{"a": "a", "b": "b", "area": 1}]


def test_weight_defaults_and_scales_mass():
    r1 = A(100, 100, [{"id": "a", "x": 0, "y": 0, "w": 10, "h": 10}, E("b", 90, 0, 10, 10)])
    assert r1["centroid"][0] == pytest.approx(50.0)
    r2 = A(100, 100, [E("a", 0, 0, 10, 10, 3), E("b", 90, 0, 10, 10, 1)])
    assert r2["centroid"] == [pytest.approx((5 * 300 + 95 * 100) / 400), pytest.approx(5.0)]


def test_validation():
    ok = [E("a", 0, 0, 10, 10)]
    for args, m in [((True, 10, ok), "canvas_w"), ((0, 10, ok), r"canvas_w: must be within \[1, 10000\]"),
                    ((10001, 10, ok), r"canvas_w: must be within"), ((10, 1.5, ok), "canvas_h: integer"),
                    ((10, 0, ok), "canvas_h"), ((10, 10001, ok), "canvas_h: must be within"),
                    ((10, 10, []), "1..100"), ((10, 10, "x"), "1..100"), ((10, 10, [5]), r"elements\[0\]: dict")]:
        with pytest.raises(ValueError, match=m):
            A(*args)
    bads = [({"id": "", "x": 0, "y": 0, "w": 1, "h": 1}, "id must"), ({"id": "a" * 41, "x": 0, "y": 0, "w": 1, "h": 1}, "id must"),
            ({"id": "a", "x": True, "y": 0, "w": 1, "h": 1}, r"\.x: integer"), ({"id": "a", "x": 0.5, "y": 0, "w": 1, "h": 1}, r"\.x: integer"),
            ({"id": "a", "x": 0, "y": "0", "w": 1, "h": 1}, r"\.y: integer"), ({"id": "a", "x": 0, "y": 0, "w": 0, "h": 1}, r"\.w: must be within"),
            ({"id": "a", "x": 0, "y": 0, "w": 1, "h": 0}, r"\.h: must be within"), ({"id": "a", "x": 0, "y": 0, "w": 1, "h": 1, "weight": 0}, r"weight: must be within"),
            ({"id": "a", "x": 0, "y": 0, "w": 1, "h": 1, "weight": 101}, r"weight: must be within"),
            ({"id": "a", "x": 0, "y": 0, "w": 1, "h": 1, "weight": 1.5}, r"weight: integer"),
            ({"id": "a", "x": 100001, "y": 0, "w": 1, "h": 1}, "magnitude above 100000"),
            ({"id": "a", "x": -100001, "y": 0, "w": 1, "h": 1}, "magnitude above 100000"),
            ({"id": "a", "x": 0, "y": 0, "w": 100001, "h": 1}, "magnitude above 100000"),
            ({"id": "a", "x": 0, "y": 0, "w": 1, "h": 1, "weight": 10 ** 12}, "magnitude above 100000")]
    for e, m in bads:
        with pytest.raises(ValueError, match=m):
            A(10, 10, [e])
    with pytest.raises(ValueError, match="duplicate id"):
        A(10, 10, [E("a", 0, 0, 1, 1), E("a", 1, 1, 1, 1)])
    assert A(10000, 10000, [E("a" * 40, -100000, 100000, 100000, 100000, 100)])["elements"][0]["margin"] == -190000
    many = [E(f"e{i}", 0, 0, 1, 1) for i in range(101)]
    with pytest.raises(ValueError, match="1..100"):
        A(10, 10, many)
    assert len(A(10, 10, many[:100])["elements"]) == 100


def test_minimum_canvas_accepted():
    r = A(1, 1, [E("a", 0, 0, 1, 1)])
    assert r["out_of_bounds"] == [] and r["centroid"] == [0.5, 0.5] and r["balanced"] is True
    assert A(10000, 10000, [E("a", 0, 0, 1, 1)])["elements"][0]["margin"] == 0

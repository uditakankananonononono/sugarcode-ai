import random
import pytest
from sugarcode.extra_doc import logo_design as g

A = g.analyze_logo


def S(x, y, w, h, c="k"):
    return {"x": x, "y": y, "w": w, "h": h, "color": c}


def test_constants():
    assert (g.MAX_GRID, g.MIN_GRID, g.MAX_SHAPES, g.MAX_COLOR, g.SIMPLE_MAX_SHAPES, g.SIMPLE_MAX_COLORS,
            g.MIN_FEATURE_PX, g.MAX_RENDER) == (64, 4, 40, 20, 5, 3, 2, 4096)
    assert g.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal_4x4():
    # 4x4: black 2x2 block top-left, red 1x1 at (3,3), then white 1x1 painted over (0,0)
    r = A(4, [S(0, 0, 2, 2, "k"), S(3, 3, 1, 1, "r"), S(0, 0, 1, 1, "w")])
    assert r["pixels"] == [["w", "k", None, None], ["k", "k", None, None], [None] * 4, [None, None, None, "r"]]
    assert r["visible_colors"] == ["k", "r", "w"]
    assert r["coverage"] == 5 / 16                    # w, k, k, k, r
    # mirror_lr: rows pair (j, 3-j): row0 w/None no, k/None no -> 0 ; row1 k/None no ; row2 all None match (4) ; row3 None/r no, None/None yes x2 -> 2 ... count by hand
    # row0: j0 w vs None no, j1 k vs None no, j2 None vs k no, j3 None vs w no = 0 ; row1: 0 ; row2: 4 ; row3: j0 None vs r no, j1 None vs None yes, j2 yes, j3 no = 2 -> 6
    assert r["mirror_lr"] == 6 / 16
    # mirror_ud: columns pair (i, 3-i): col0: w vs None no, k vs None no, None vs k no, None vs w no =0 ; col1: k/None.. 0? rows (0,3): k vs None no,(1,2): k vs None no,(2,1) no,(3,0) no =0
    # col2: all None -> 4 ; col3: (0,3) None vs r no, (1,2) None vs None yes, (2,1) yes, (3,0) no = 2 -> 6
    assert r["mirror_ud"] == 6 / 16
    assert r["shape_count"] == 3 and r["simple"] is True


def test_symmetric_mark_scores_one():
    r = A(8, [S(0, 0, 8, 8, "a"), S(2, 2, 4, 4, "b")])
    assert r["mirror_lr"] == 1.0 and r["mirror_ud"] == 1.0 and r["coverage"] == 1.0
    r = A(8, [S(0, 0, 3, 8, "a")])
    assert r["mirror_lr"] == 0.25 and r["mirror_ud"] == 1.0 and r["coverage"] == 3 / 8


def test_random_matches_dict_painter_oracle():
    rng = random.Random(284)
    for _ in range(60):
        n = rng.randint(4, 10)
        shapes = []
        for _ in range(rng.randint(1, 6)):
            x, y = rng.randrange(n), rng.randrange(n)
            shapes.append(S(x, y, rng.randint(1, n - x), rng.randint(1, n - y), rng.choice("abc")))
        r = A(n, shapes)
        d = {}
        for s in shapes:
            for (px, py) in [(a, b) for a in range(s["x"], s["x"] + s["w"]) for b in range(s["y"], s["y"] + s["h"])]:
                d[(px, py)] = s["color"]
        assert r["pixels"] == [[d.get((x, y)) for x in range(n)] for y in range(n)]
        assert r["coverage"] == len(d) / n ** 2
        assert r["visible_colors"] == sorted(set(d.values()))
        assert r["mirror_lr"] == sum(d.get((x, y)) == d.get((n - 1 - x, y)) for x in range(n) for y in range(n)) / n ** 2
        assert r["mirror_ud"] == sum(d.get((x, y)) == d.get((x, n - 1 - y)) for x in range(n) for y in range(n)) / n ** 2


def test_simplicity_boundaries():
    five = [S(i, 0, 1, 1, "a") for i in range(5)]
    assert A(8, five)["simple"] is True and A(8, five + [S(5, 0, 1, 1, "a")])["simple"] is False
    three = [S(0, 0, 1, 1, "a"), S(1, 0, 1, 1, "b"), S(2, 0, 1, 1, "c")]
    assert A(8, three)["simple"] is True
    assert A(8, three + [S(3, 0, 1, 1, "d")])["simple"] is False
    # a colour fully painted over is not visible, so it does not count
    assert A(8, [S(0, 0, 1, 1, "x"), S(0, 0, 1, 1, "y")] + three[1:])["visible_colors"] == ["b", "c", "y"]


def test_small_feature_boundary_at_render_size():
    # grid 8, render 16: scale 2 px per cell. a 1-cell-wide shape is 2px -> survives (limit < 2); render 15 -> 1.875 -> small
    sh = [S(0, 0, 1, 5), S(2, 0, 3, 3)]
    assert A(8, sh, 16)["small_feature_shapes"] == []
    assert A(8, sh, 15)["small_feature_shapes"] == [0]
    assert A(8, sh, 1)["small_feature_shapes"] == [0, 1]
    assert A(8, sh)["small_feature_shapes"] == []                  # default render_px 16
    assert A(8, [S(0, 0, 4, 1)], 16)["small_feature_shapes"] == []   # min(w,h) uses the smaller side
    assert A(8, [S(0, 0, 1, 4)], 15)["small_feature_shapes"] == [0]


def test_validation():
    ok = [S(0, 0, 1, 1)]
    for gr, m in [(3, r"grid: must be within \[4, 64\]"), (65, "grid: must be within"), (True, "integer"), (4.0, "integer"),
                  (10 ** 7, "magnitude above 1000000")]:
        with pytest.raises(ValueError, match=m):
            A(gr, ok)
    assert A(4, ok)["shape_count"] == 1 and len(A(64, ok)["pixels"]) == 64
    for rp, m in [(0, r"render_px: must be within \[1, 4096\]"), (4097, "render_px: must be within"), (True, "integer")]:
        with pytest.raises(ValueError, match=m):
            A(8, ok, rp)
    assert A(8, ok, 4096)["shape_count"] == 1 and A(8, ok, 1)["shape_count"] == 1
    for sh, m in [([], "1..40"), ("x", "1..40"), ([5], r"shapes\[0\]: dict"),
                  ([{"x": 0, "y": 0, "w": 1, "h": 1}], "color must be"), ([S(0, 0, 1, 1, "")], "color must be"),
                  ([S(0, 0, 1, 1, "c" * 21)], "color must be"), ([S(0, 0, 1, 1, 5)], "color must be"),
                  ([S(-1, 0, 1, 1)], r"\.x: must be within \[0, 7\]"), ([S(8, 0, 1, 1)], r"\.x: must be within"),
                  ([S(0, 8, 1, 1)], r"\.y: must be within"), ([S(0, 0, 0, 1)], r"\.w: must be within \[1, 8\]"),
                  ([S(1, 0, 8, 1)], r"\.w: must be within \[1, 7\]"), ([S(0, 1, 1, 8)], r"\.h: must be within \[1, 7\]"),
                  ([S(0, 0, 1, 0)], r"\.h: must be within"), ([S(0.5, 0, 1, 1)], r"\.x: integer"),
                  ([S(0, 0, 1, 1)] * 0 + [S(True, 0, 1, 1)], r"\.x: integer")]:
        with pytest.raises(ValueError, match=m):
            A(8, sh)
    assert A(8, [S(7, 7, 1, 1, "c" * 20)])["visible_colors"] == ["c" * 20]
    assert A(8, [S(0, 0, 8, 8)])["coverage"] == 1.0
    many = [S(0, 0, 1, 1)] * 41
    with pytest.raises(ValueError, match="1..40"):
        A(8, many)
    assert A(8, many[:40])["shape_count"] == 40


def test_default_render_px_is_sixteen_exactly():
    # grid 17, 2-cell shape: 2*16/17 = 1.88 < 2 (small) but at render 17 it would be exactly 2 (survives)
    assert A(17, [S(0, 0, 2, 2)])["small_feature_shapes"] == [0]
    assert A(17, [S(0, 0, 2, 2)], 17)["small_feature_shapes"] == []
    assert A(17, [S(0, 0, 2, 2)], 16) == A(17, [S(0, 0, 2, 2)])


def test_magnitude_cap_boundary():
    with pytest.raises(ValueError, match=r"grid: must be within"):
        A(10 ** 6, [S(0, 0, 1, 1)])
    with pytest.raises(ValueError, match="magnitude above 1000000"):
        A(10 ** 6 + 1, [S(0, 0, 1, 1)])
    with pytest.raises(ValueError, match="magnitude above 1000000"):
        A(-(10 ** 6) - 1, [S(0, 0, 1, 1)])
    with pytest.raises(ValueError, match=r"grid: must be within"):
        A(-(10 ** 6), [S(0, 0, 1, 1)])

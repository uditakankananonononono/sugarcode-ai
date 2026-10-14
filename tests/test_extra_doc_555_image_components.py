import inspect
import random

import pytest
from sugarcode.extra_doc import image_components as ic

C = ic.components


def sb(r):
    return [(x["size"], x["bbox"]) for x in r["components"]]


def test_constants_signature():
    assert ic.MAX_SIDE == 50
    assert ic.STATUS_NOTE.startswith("PARTIAL") and "no object recognition" in ic.STATUS_NOTE
    sig = inspect.signature(C)
    assert list(sig.parameters) == ["image", "connectivity"] and sig.parameters["connectivity"].default == 4


def test_hand_literals():
    img = [[1, 1, 0, 0, 1],
           [0, 1, 0, 0, 1],
           [0, 0, 1, 0, 0],
           [1, 0, 0, 1, 1]]
    r = C(img)
    assert sb(r) == [(3, (0, 0, 1, 1)), (2, (0, 4, 1, 4)), (1, (2, 2, 2, 2)), (1, (3, 0, 3, 0)), (2, (3, 3, 3, 4))]
    assert (r["count"], r["rows"], r["cols"], r["status_note"]) == (5, 4, 5, ic.STATUS_NOTE)
    r8 = C(img, 8)                      # diagonal (1,1)-(2,2) joins the first blob with (2,2); (2,2)-(3,3) joins the last
    assert C([[0, 0], [0, 0]])["components"] == [] and C([[0]])["count"] == 0
    assert sb(C([[1]])) == [(1, (0, 0, 0, 0))]
    assert sb(C([[1, 0], [0, 1]])) == [(1, (0, 0, 0, 0)), (1, (1, 1, 1, 1))]
    assert sb(C([[1, 0], [0, 1]], 8)) == [(2, (0, 0, 1, 1))]
    assert sb(C([[1, 1, 1]])) == [(3, (0, 0, 0, 2))] and sb(C([[1], [1], [1]])) == [(3, (0, 0, 2, 0))]
    assert sb(C([[0, 1], [1, 0]], 8)) == [(2, (0, 0, 1, 1))]
    u = [[1, 0, 1], [1, 1, 1]]                               # U shape: one blob with both columns
    assert sb(C(u)) == [(5, (0, 0, 1, 2))]
    assert sb(C([[1, 1], [1, 1]])) == [(4, (0, 0, 1, 1))]
    assert sb(C(((1, 0), (1, 0)))) == [(2, (0, 0, 1, 0))]


def uf_oracle(g, conn):
    h, w = len(g), len(g[0])
    parent = {(r, c): (r, c) for r in range(h) for c in range(w) if g[r][c]}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for (r, c) in list(parent):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dr, dc) == (0, 0) or (conn == 4 and dr and dc):
                    continue
                n = (r + dr, c + dc)
                if n in parent:
                    parent[find((r, c))] = find(n)
    groups = {}
    for p in parent:
        groups.setdefault(find(p), []).append(p)
    out = []
    for cells in groups.values():
        rs, cs = [p[0] for p in cells], [p[1] for p in cells]
        out.append((min(cells), len(cells), (min(rs), min(cs), max(rs), max(cs))))
    out.sort()
    return [(s, b) for _, s, b in out]


def test_oracle_union_find():
    rnd = random.Random(555)
    for _ in range(400):
        h, w = rnd.randint(1, 7), rnd.randint(1, 7)
        g = [[1 if rnd.random() < 0.45 else 0 for _ in range(w)] for _ in range(h)]
        for conn in (4, 8):
            assert sb(C(g, conn)) == uf_oracle(g, conn), (g, conn)


def test_caps_both_sides():
    assert C([[1] * 50] * 50)["components"][0]["size"] == 2500
    assert C([[1] * 50] * 50)["components"][0]["bbox"] == (0, 0, 49, 49)
    with pytest.raises(ValueError, match=r"^image: 1 to 50 rows required$"):
        C([[1]] * 51)
    with pytest.raises(ValueError, match=r"^image: 1 to 50 rows required$"):
        C([])
    with pytest.raises(ValueError, match=r"^image\[0\]: 1 to 50 cells required$"):
        C([[1] * 51])
    with pytest.raises(ValueError, match=r"^image\[0\]: 1 to 50 cells required$"):
        C([[]])
    assert C([[1] * 50])["cols"] == 50


def test_shape_and_type_refusals():
    for bad in ("ab", None, 5, {0: [1]}):
        with pytest.raises(ValueError, match=r"^image: list of rows required$"):
            C(bad)
    for bad in ("1", None, 1, {1: 1}):
        with pytest.raises(ValueError, match=r"^image\[1\]: list required$"):
            C([[1], bad])
    with pytest.raises(ValueError, match=r"^image\[1\]: 2 cells required$"):
        C([[1, 0], [1]])
    with pytest.raises(ValueError, match=r"^image\[2\]: 2 cells required$"):
        C([[1, 0], [1, 0], [1, 0, 1]])
    for bad in (True, False, 1.0, "1", None):
        with pytest.raises(ValueError, match=r"^image\[1\]\[0\]: integer required$"):
            C([[1], [bad]])
    for bad in (2, -1, 10**30):
        with pytest.raises(ValueError, match=r"^image\[0\]\[1\]: must be 0 or 1$"):
            C([[0, bad]])
    for bad in (True, 4.0, "4", None):
        with pytest.raises(ValueError, match=r"^connectivity: integer required$"):
            C([[1]], bad)
    for bad in (0, 1, 3, 5, 6, 7, 9, -4):
        with pytest.raises(ValueError, match=r"^connectivity: must be 4 or 8$"):
            C([[1]], bad)
    with pytest.raises(ValueError, match=r"^connectivity: integer required$"):
        C("bad", True)
    with pytest.raises(ValueError, match=r"^connectivity: must be 4 or 8$"):
        C("bad", 3)

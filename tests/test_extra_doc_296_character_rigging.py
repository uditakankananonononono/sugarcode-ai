import cmath
import math
import random
import pytest
from sugarcode.extra_doc import character_rigging as c

R = c.solve_rig


def B(i, parent, length, angle, **kw):
    d = {"id": i, "parent": parent, "length": length, "angle_deg": angle}
    d.update(kw)
    return d


def test_constants():
    assert (c.MAX_BONES, c.MAX_ID, c.MAX_LENGTH, c.MAX_ANGLE) == (64, 40, 10000, 360) and c.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal_right_angles():
    # root points +x (angle 0) length 2; child turns +90 (world 90) length 3 ; grandchild turns +90 (world 180) length 1
    r = R([B("root", None, 2, 0), B("mid", "root", 3, 90), B("tip", "mid", 1, 90)])
    assert [b["start"] for b in r["bones"]] == [[0.0, 0.0], [2.0, 0.0], [2.0, 3.0]]
    assert [b["tail"] for b in r["bones"]] == [[2.0, 0.0], [2.0, 3.0], [1.0, 3.0]]
    assert [b["world_deg"] for b in r["bones"]] == [0.0, 90.0, 180.0]
    assert [b["depth"] for b in r["bones"]] == [0, 1, 2]
    assert r["root"] == "root" and r["leaves"] == ["tip"] and r["max_depth"] == 2
    assert r["max_reach"] == pytest.approx(math.hypot(2, 3), abs=1e-9)    # the mid tail is the farthest
    assert r["all_within_limits"] is True


def test_diagonal_and_branching():
    r = R([B("a", None, 10, 45), B("l", "a", 5, 45), B("r", "a", 5, -45)])
    assert r["bones"][0]["tail"] == [7.071067812, 7.071067812]
    assert r["bones"][1]["tail"] == [7.071067812, 12.071067812] and r["bones"][1]["world_deg"] == 90.0
    assert r["leaves"] == ["l", "r"]
    assert r["bones"][2]["world_deg"] == 0.0 and r["bones"][2]["tail"] == [12.071067812, 7.071067812]


def test_random_trees_match_path_walk_complex_oracle():
    rng = random.Random(296)
    for _ in range(60):
        n = rng.randint(1, 10)
        bones = []
        for i in range(n):
            parent = None if i == 0 else f"b{rng.randrange(i)}"
            bones.append(B(f"b{i}", parent, rng.choice([1, 2.5, 4]), rng.choice([-90, -30, 0, 45, 120, 200])))
        # shuffle input order: the hierarchy must not depend on order
        shuffled = bones[:]
        rng.shuffle(shuffled)
        r = R(shuffled)
        byid = {b["id"]: b for b in bones}
        for row in r["bones"]:
            chain, k = [], row["id"]
            while k is not None:
                chain.append(byid[k]); k = byid[k]["parent"]
            chain.reverse()
            pos, ang = 0j, 0.0
            for b in chain:
                ang += b["angle_deg"]
                start = pos
                pos = pos + cmath.rect(b["length"], math.radians(ang))
            assert row["tail"] == [round(pos.real, 9) + 0.0, round(pos.imag, 9) + 0.0]
            assert row["start"] == [round(start.real, 9) + 0.0, round(start.imag, 9) + 0.0]
            assert row["depth"] == len(chain) - 1 and row["world_deg"] == pytest.approx(ang)
        assert [b["id"] for b in r["bones"]] == [b["id"] for b in shuffled]
        assert r["max_reach"] == pytest.approx(max(abs(complex(*b["tail"])) for b in r["bones"]), abs=1e-8)


def test_limits():
    r = R([B("a", None, 1, 0), B("b", "a", 1, 90, min_deg=0, max_deg=90), B("c", "b", 1, -10, min_deg=-5), B("d", "c", 1, 100, max_deg=99)])
    assert [x["within_limits"] for x in r["bones"]] == [True, True, False, False] and r["all_within_limits"] is False
    r = R([B("a", None, 1, 0), B("b", "a", 1, -5, min_deg=-5, max_deg=-5)])
    assert r["all_within_limits"] is True


def test_negative_zero_is_normalised():
    r = R([B("a", None, 1, 90)])
    assert r["bones"][0]["tail"] == [0.0, 1.0] and str(r["bones"][0]["tail"][0]) == "0.0"
    r = R([B("a", None, 1, 180)])
    assert str(r["bones"][0]["tail"][1]) == "0.0"


def test_hierarchy_errors():
    with pytest.raises(ValueError, match="exactly one root.*found 0"):
        R([B("a", "b", 1, 0), B("b", "a", 1, 0)])
    with pytest.raises(ValueError, match="exactly one root.*found 2"):
        R([B("a", None, 1, 0), B("b", None, 1, 0)])
    with pytest.raises(ValueError, match="unknown parent 'zz'"):
        R([B("a", None, 1, 0), B("b", "zz", 1, 0)])
    with pytest.raises(ValueError, match="cycle in hierarchy"):
        R([B("r", None, 1, 0), B("a", "b", 1, 0), B("b", "a", 1, 0)])
    with pytest.raises(ValueError, match="cycle in hierarchy"):
        R([B("r", None, 1, 0), B("a", "a", 1, 0)])
    with pytest.raises(ValueError, match="duplicate id 'a'"):
        R([B("a", None, 1, 0), B("a", "a", 1, 0)])


def test_validation():
    ok = B("a", None, 1, 0)
    for bones, m in [([], "1..64"), ("x", "1..64"), ([5], r"bones\[0\]: dict"), ([B("", None, 1, 0)], "id must"),
                     ([B("x" * 41, None, 1, 0)], "id must"), ([B("a", 5, 1, 0)], "parent must be a bone id"),
                     ([B("a", None, 0.0009, 0)], r"length: must be within"), ([B("a", None, 10001, 0)], r"length: must be within"),
                     ([B("a", None, True, 0)], "number required"), ([B("a", None, 1, "0")], "number required"),
                     ([B("a", None, 1, 361)], r"angle_deg: must be within"), ([B("a", None, 1, -361)], r"angle_deg: must be within"),
                     ([B("a", None, 1, float("nan"))], "finite"), ([B("a", None, 1, 1e10)], "magnitude above 1e9"),
                     ([B("a", None, 1, 0, min_deg=10, max_deg=5)], "min_deg above max_deg"),
                     ([B("a", None, 1, 0, min_deg=-361)], "min_deg: must be within"), ([B("a", None, 1, 0, max_deg=361)], "max_deg: must be within")]:
        with pytest.raises(ValueError, match=m):
            R(bones)
    assert R([B("x" * 40, None, 10000, 360)])["bones"][0]["world_deg"] == 360.0
    assert R([B("a", None, 0.001, -360)])["bones"][0]["world_deg"] == -360.0
    many = [ok] + [B(f"b{i}", "a", 1, 0) for i in range(63)]
    assert len(R(many)["bones"]) == 64
    with pytest.raises(ValueError, match="1..64"):
        R(many + [B("extra", "a", 1, 0)])


def test_parent_field_and_negative_zero_and_cap_edges():
    r = R([B("root", None, 2, 0), B("mid", "root", 3, 90), B("tip", "mid", 1, 90)])
    assert [b["parent"] for b in r["bones"]] == [None, "root", "mid"]
    for ang in (270, -90):
        t = R([B("a", None, 1, ang)])["bones"][0]["tail"]
        assert t == [0.0, -1.0] and str(t[0]) == "0.0"                   # cos(270 deg) is -1.8e-16, rounds to -0.0, normalised to 0.0
    with pytest.raises(ValueError, match=r"angle_deg: must be within"):
        R([B("a", None, 1, 1e9)])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        R([B("a", None, 1, 1e9 + 1000)])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        R([B("a", None, 1e9 + 1000, 0)])

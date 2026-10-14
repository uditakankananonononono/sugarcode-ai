import copy
import itertools
import random

import pytest

from sugarcode.extra_doc.game_design335 import compose


def item(i, text, cx, fun, *tags):
    return {"id": i, "text": text, "complexity": cx, "fun": fun, "tags": list(tags)}


def pools():
    return ([item("g1", "reach the tower.", 2, 10, "quest"), item("g2", "collect ten gems.", 1, 5, "hoard")],
            [item("a1", "jumping.", 3, 7, "move"), item("a2", "throwing.", 2, 9, "aim")],
            [item("c1", "gaps.", 2, 6, "move"), item("c2", "targets.", 1, 4, "aim")],
            [item("r1", "a new cape.", 1, 3, "quest"), item("r2", "a bonus level.", 2, 8, "hoard")])


def test_hand_case_and_exact_output():
    g, a, c, r = pools()
    out = compose(g, a, c, r, 40)
    # compatible combos: (a1,c1) or (a2,c2) with (g1,r1) or (g2,r2); fun: a1+c1=13, a2+c2=13 -> tie -> lowest ids a1,c1
    # (g1,r1)=13, (g2,r2)=13 -> tie -> g1,r1. total 26
    assert out == {
        "status": "designed", "feasible_count": 4,
        "design": {"goal": "g1", "action": "a1", "challenge": "c1", "reward": "r1",
                   "total_fun_weight": 26, "total_complexity": 8},
        "brief": "Goal: reach the tower. Players act by jumping. Challenge: gaps. Reward: a new cape.",
        "loop": ["goal: reach the tower.", "act: jumping.", "challenge: gaps.", "reward: a new cape."],
        "playtest_verified": False, "review_required": True, "external_effects": []}


def test_budget_boundary_n_and_n_plus_1():
    g, a, c, r = pools()
    # cheapest compatible combination: g2(1)+a2(2)+c2(1)+r2(2)=6; g1(2)+a2(2)+c2(1)+r1(1)=6
    assert compose(g, a, c, r, 6)["feasible_count"] == 2
    assert compose(g, a, c, r, 5) == {"status": "no_compatible_design", "feasible_count": 0, "design": None, "brief": "",
                                      "loop": [], "playtest_verified": False, "external_effects": []}
    assert compose(g, a, c, r, 0)["status"] == "no_compatible_design"


def test_incompatible_tags_close_to_empty():
    g, a, c, r = pools()
    c = [item("c1", "gaps.", 0, 1, "other")]
    assert compose(g, a, c, r, 40)["status"] == "no_compatible_design"
    g, a, c, r = pools()
    r = [item("r1", "x.", 0, 1, "other")]
    assert compose(g, a, c, r, 40)["feasible_count"] == 0


def test_independent_brute_force_oracle():
    rnd = random.Random(335)
    tags = ["t0", "t1", "t2"]
    for _ in range(500):
        ps = []
        for p in range(4):
            n = rnd.randint(1, 4)
            ps.append([item(f"p{p}i{k}", f"text {p}{k}.", rnd.randint(0, 10), rnd.randint(0, 100),
                            *rnd.sample(tags, rnd.randint(1, 2))) for k in range(n)])
        budget = rnd.randint(0, 40)
        out = compose(*copy.deepcopy(ps), budget)
        feas = []
        for combo in itertools.product(*ps):
            if sum(x["complexity"] for x in combo) > budget:
                continue
            if not set(combo[1]["tags"]) & set(combo[2]["tags"]) or not set(combo[0]["tags"]) & set(combo[3]["tags"]):
                continue
            feas.append((-sum(x["fun"] for x in combo), tuple(x["id"] for x in combo)))
        if not feas:
            assert out["status"] == "no_compatible_design" and out["feasible_count"] == 0
            continue
        best = min(feas)
        assert out["feasible_count"] == len(feas)
        assert out["design"]["total_fun_weight"] == -best[0]
        assert (out["design"]["goal"], out["design"]["action"], out["design"]["challenge"], out["design"]["reward"]) == best[1]


def test_caps_types_and_exact_messages():
    g, a, c, r = pools()
    big = [item(f"x{i}", "t.", 0, 0, "move") for i in range(5)]
    assert compose(big, a, c, r, 40)["status"] in ("designed", "no_compatible_design")   # 5 allowed
    with pytest.raises(ValueError, match=r"^goals: list of 1\.\.5 items required$"):
        compose(big + [item("x5", "t.", 0, 0, "move")], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^actions: list of 1\.\.5 items required$"):
        compose(g, [], c, r, 40)
    with pytest.raises(ValueError, match=r"^challenges: list of 1\.\.5 items required$"):
        compose(g, a, tuple(c), r, 40)
    with pytest.raises(ValueError, match=r"^max_complexity: integer in \[0, 40\] required$"):
        compose(g, a, c, r, 41)
    with pytest.raises(ValueError, match=r"^max_complexity: integer in \[0, 40\] required$"):
        compose(g, a, c, r, -1)
    for bad in (True, 1.0, "3", None):
        with pytest.raises(ValueError, match=r"^max_complexity: integer in \[0, 40\] required$"):
            compose(g, a, c, r, bad)
    ok = item("g", "t.", 10, 100, "quest")
    compose([ok], a, c, r, 40)
    for field, over in (("complexity", 11), ("fun", 101)):
        bad = dict(ok, **{field: over})
        with pytest.raises(ValueError, match=rf"^goals\[0\]\.{field}: integer in \[0, {10 if field == 'complexity' else 100}\] required$"):
            compose([bad], a, c, r, 40)
        for t in (True, 1.0):
            with pytest.raises(ValueError, match=rf"^goals\[0\]\.{field}: integer in"):
                compose([dict(ok, **{field: t})], a, c, r, 40)


def test_item_schema_text_and_ids():
    g, a, c, r = pools()
    base = g[0]
    with pytest.raises(ValueError, match=r"^goals\[0\]: exact keys id, text, complexity, fun, tags required$"):
        compose([dict(base, extra=1)], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]: exact keys"):
        compose([{k: v for k, v in base.items() if k != "fun"}], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]: exact keys"):
        compose(["x"], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[1\]: duplicate id$"):
        compose([base, dict(base)], a, c, r, 40)
    compose([dict(base, id="i" * 30)], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]\.id: text of 1\.\.30 characters required$"):
        compose([dict(base, id="i" * 31)], a, c, r, 40)
    compose([dict(base, text="t" * 80)], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]\.text: text of 1\.\.80 characters required$"):
        compose([dict(base, text="t" * 81)], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]\.text: trimmed visible text required$"):
        compose([dict(base, text=" t")], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]\.text: trimmed visible text required$"):
        compose([dict(base, text="t\x00")], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]\.id: text of 1\.\.30"):
        compose([dict(base, id=5)], a, c, r, 40)
    compose([dict(base, tags=["a", "b", "c", "d"])], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]\.tags: list of 1\.\.4 tags required$"):
        compose([dict(base, tags=["a", "b", "c", "d", "e"])], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]\.tags: list of 1\.\.4 tags required$"):
        compose([dict(base, tags=[])], a, c, r, 40)
    with pytest.raises(ValueError, match=r"^goals\[0\]\.tags: duplicate tag$"):
        compose([dict(base, tags=["a", "a"])], a, c, r, 40)


def test_no_mutation_and_tie_order():
    g, a, c, r = pools()
    before = copy.deepcopy((g, a, c, r))
    compose(g, a, c, r, 40)
    assert (g, a, c, r) == before
    # identical fun everywhere: the lowest ids win
    same = [[item(f"{p}{k}", "t.", 0, 5, "x") for k in "ba"] for p in "wxyz"]
    d = compose(*same, 0)["design"]
    assert (d["goal"], d["action"], d["challenge"], d["reward"]) == ("wa", "xa", "ya", "za")

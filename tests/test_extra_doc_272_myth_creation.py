"""Row 272 myth creation: oracle = hand-derived literals (sha256sum of '<seed>:<kind>:<name>') plus an independent
property checker (dependency order, balance, coverage)."""
import itertools
import random
import pytest
from sugarcode.extra_doc import myth_creation as m

C = m.create_myth


def test_hand_derived_literal_story():
    # sha256 prefixes: order night ac621255 < tides caeae331 < fire e3b348af (fire waits for night);
    # agent Ura 7b0fe8dd < Mele 937609e6, so Ura, Mele, Ura take steps 1, 2, 3.
    # act index = digest mod 6: night 2, tides 0, fire 3; motive: night 5, tides 0, fire 0.
    r = C(["tides", "fire", "night"], ["Ura", "Mele"], 1, {"fire": ["night"]})
    assert r["order"] == ["night", "tides", "fire"]
    assert [(s["agent"], s["act"], s["motive"]) for s in r["story"]] == [
        ("Ura", "tore from the dark", "in grief"), ("Mele", "shaped", "out of loneliness"),
        ("Ura", "wove", "out of loneliness")]
    assert r["narrative"] == ("Ura tore from the dark night in grief. Mele shaped tides out of loneliness. "
                              "Ura wove fire out of loneliness, once night existed.")
    assert r["agent_load"] == {"Ura": 2, "Mele": 1} and r["load_spread"] == 1 and r["seed"] == 1
    assert r["story"][2]["after"] == ["night"] and r["story"][0]["step"] == 1 and r["story"][2]["step"] == 3
    assert r["input_fingerprint"] == "9722e12afbc767201652e8108cd6ac1ddab9bc30160755903b883fffe53c63e9"
    assert r["status_note"].startswith("PARTIAL:")


def test_vocab_sizes_are_pinned():
    assert len(m.ACTS) == 6 and len(m.MOTIVES) == 6 and m.ACTS[3] == "wove" and m.MOTIVES[5] == "in grief"


def check(r, ph, ag, deps):
    # independent checker
    assert sorted(r["order"]) == sorted(ph) and len(set(r["order"])) == len(ph)
    pos = {p: i for i, p in enumerate(r["order"])}
    for p, pre in (deps or {}).items():
        for q in pre:
            assert pos[q] < pos[p]
    assert sum(r["agent_load"].values()) == len(ph) and r["load_spread"] == max(r["agent_load"].values()) - min(r["agent_load"].values())
    assert r["load_spread"] <= 1 or len(ag) > len(ph) and r["load_spread"] <= 1
    for i, s in enumerate(r["story"]):
        assert s["phenomenon"] == r["order"][i] and s["step"] == i + 1 and s["agent"] in ag


def test_property_random_instances():
    rnd = random.Random(2026)
    for trial in range(60):
        n = rnd.randint(1, 9); k = rnd.randint(1, 5)
        ph = [f"p{i}" for i in range(n)]; ag = [f"a{j}" for j in range(k)]
        deps = {ph[j]: [ph[i] for i in range(j) if rnd.random() < 0.3] for j in range(n)}   # acyclic by index
        r = C(ph, ag, rnd.randint(0, 10 ** 6), deps)
        check(r, ph, ag, deps)
        assert r == C(ph, ag, r["seed"], deps)            # deterministic


def test_every_topological_order_reachable_by_some_seed_and_seed_changes_things():
    ph = ["x", "y", "z"]
    seen = {tuple(C(ph, ["a"], s)["order"]) for s in range(200)}
    assert seen == set(itertools.permutations(ph))
    assert C(ph, ["a", "b"], 1)["input_fingerprint"] != C(ph, ["a", "b"], 2)["input_fingerprint"]


def test_chain_forces_order_regardless_of_seed():
    for s in (0, 1, 2, 99):
        assert C(["c", "b", "a"], ["g"], s, {"c": ["b"], "b": ["a"]})["order"] == ["a", "b", "c"]


def test_more_agents_than_phenomena_and_balance():
    r = C(["p"], ["a", "b", "c"], 5)
    assert sorted(r["agent_load"].values()) == [0, 0, 1] and r["load_spread"] == 1
    r = C(["p1", "p2", "p3", "p4"], ["a", "b"], 5)
    assert r["agent_load"] == {"a": 2, "b": 2} and r["load_spread"] == 0


def test_normalisation_and_duplicates():
    assert C([" tides "], [" Ura"], 0)["order"] == ["tides"]
    with pytest.raises(ValueError, match="phenomena: names must be unique"):
        C(["a", " a"], ["g"])
    with pytest.raises(ValueError, match="agents: names must be unique"):
        C(["a"], ["g", "g "])


def test_dependency_errors():
    with pytest.raises(ValueError, match="cycle detected"):
        C(["a", "b"], ["g"], 0, {"a": ["b"], "b": ["a"]})
    with pytest.raises(ValueError, match="cannot precede itself"):
        C(["a"], ["g"], 0, {"a": ["a"]})
    with pytest.raises(ValueError, match="unknown phenomenon"):
        C(["a"], ["g"], 0, {"z": []})
    with pytest.raises(ValueError, match="unknown prerequisite"):
        C(["a"], ["g"], 0, {"a": ["z"]})
    with pytest.raises(ValueError, match="list required"):
        C(["a"], ["g"], 0, {"a": "b"})
    with pytest.raises(ValueError, match="dependencies: dict"):
        C(["a"], ["g"], 0, [["a"]])
    with pytest.raises(ValueError, match="unknown phenomenon"):
        C(["a"], ["g"], 0, {1: []})
    with pytest.raises(ValueError, match="unknown prerequisite"):
        C(["a"], ["g"], 0, {"a": [1]})
    assert C(["a", "b"], ["g"], 0, {"b": ["a", "a"]})["order"] == ["a", "b"]    # duplicate prerequisite ok


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, -1, 2 ** 63])
def test_seed_validation(bad):
    with pytest.raises(ValueError, match="seed: int in"):
        C(["a"], ["g"], bad)


def test_seed_edges_and_caps():
    C(["a"], ["g"], 0); C(["a"], ["g"], 2 ** 63 - 1)
    ph30 = [f"p{i}" for i in range(30)]; ag12 = [f"a{i}" for i in range(12)]
    r = C(ph30, ag12, 3)
    assert len(r["order"]) == 30 and r["load_spread"] <= 1
    with pytest.raises(ValueError, match="phenomena: list of 1..30"):
        C(ph30 + ["x"], ["g"])
    with pytest.raises(ValueError, match="agents: list of 1..12"):
        C(["a"], ag12 + ["x"])
    for bad in ([], "abc", None, [1], [""], ["  "], ["x" * 49]):
        with pytest.raises(ValueError, match="phenomena"):
            C(bad, ["g"])
        with pytest.raises(ValueError, match="agents"):
            C(["a"], bad)
    C(["x" * 48], ["y" * 48])


def test_default_seed_is_zero():
    d = C(["a", "b", "c"], ["g"])
    assert d["seed"] == 0 and d == C(["a", "b", "c"], ["g"], 0) and d != C(["a", "b", "c"], ["g"], 1)

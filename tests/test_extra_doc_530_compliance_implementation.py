from fractions import Fraction as Fr
import pytest
from sugarcode.extra_doc import compliance_implementation as ci

COV = ci.coverage
REQS = [("R1", "encrypt at rest"), ("R2", "access reviews"), ("R3", "backups")]
CTLS = [("C1", "kms", ["R1"]), ("C2", "iam suite", ["R1", "R2"]), ("C3", "docs", [])]


def test_constants():
    assert (ci.MAX_REQUIREMENTS, ci.MAX_CONTROLS, ci.MAX_ID, ci.MAX_TITLE, ci.MAX_REFS) == (100, 200, 20, 80, 50)
    assert ci.STATUS_NOTE.startswith("PARTIAL") and "no judgment of whether any control" in ci.STATUS_NOTE


def test_hand_literals():
    r = COV(REQS, CTLS)
    assert [x["controls"] for x in r["requirements"]] == [["C1", "C2"], ["C2"], []]
    assert r["uncovered"] == ["R3"] and r["orphan_controls"] == ["C3"]
    assert r["covered_share"] == Fr(2, 3) and r["max_controls_per_requirement"] == 2
    r = COV(REQS, [])
    assert r["uncovered"] == ["R1", "R2", "R3"] and r["covered_share"] == 0 and r["max_controls_per_requirement"] == 0
    r = COV([("R1", "a")], [("C1", "x", ["R1"]), ("C2", "y", ["R1"])])
    assert r["covered_share"] == 1 and r["max_controls_per_requirement"] == 2 and r["orphan_controls"] == []
    r = COV([("R1", "a"), ("R2", "b"), ("R3", "c"), ("R4", "d")],
            [("C1", "x", ["R2", "R4"]), ("C2", "y", ["R1", "R2", "R4"])])
    assert [x["controls"] for x in r["requirements"]] == [["C2"], ["C1", "C2"], [], ["C1", "C2"]]
    assert r["covered_share"] == Fr(3, 4)


def test_oracle_random():
    import random
    rnd = random.Random(530)
    for _ in range(400):
        nr = rnd.randint(1, 12)
        reqs = [(f"R{i}", f"t{i}") for i in range(nr)]
        ctls = []
        for j in range(rnd.randint(0, 10)):
            refs = rnd.sample([r[0] for r in reqs], rnd.randint(0, min(4, nr)))
            rnd.shuffle(refs)
            ctls.append((f"C{j}", f"u{j}", refs))
        r = COV(reqs, ctls)
        hits = {rid: [cid for cid, _, refs in ctls if rid in refs] for rid, _ in reqs}
        assert [(x["rid"], x["title"], x["controls"]) for x in r["requirements"]] == \
               [(rid, t, hits[rid]) for rid, t in reqs]
        assert r["uncovered"] == [rid for rid, _ in reqs if not hits[rid]]
        assert r["orphan_controls"] == [cid for cid, _, refs in ctls if not refs]
        assert r["covered_share"] == Fr(sum(1 for v in hits.values() if v), nr)
        assert r["max_controls_per_requirement"] == max(len(v) for v in hits.values())


def test_requirement_validation():
    for bad in ("abc", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"^requirements: list required$"):
            COV(bad, [])
    with pytest.raises(ValueError, match=r"^requirements: 1 to 100 entries required$"):
        COV([], [])
    many = [(f"R{i}", "t") for i in range(101)]
    with pytest.raises(ValueError, match=r"^requirements: 1 to 100 entries required$"):
        COV(many, [])
    assert COV(many[:100], [])["covered_share"] == 0
    ok = ("R0", "t")
    for bad in ("abc", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"^requirements\[1\]: \(rid, title\) required$"):
            COV([ok, bad], [])
    for bad in (("R1",), ("R1", "t", 1), ()):
        with pytest.raises(ValueError, match=r"^requirements\[1\]: 2 entries required$"):
            COV([ok, bad], [])
    for bad in ("", None, 3, ["R1"], "x" * 21):
        with pytest.raises(ValueError, match=r"^requirements\[1\] id: non-empty string up to 20 characters required$"):
            COV([ok, (bad, "t")], [])
    assert COV([ok, ("x" * 20, "t")], [])["requirements"][1]["rid"] == "x" * 20
    with pytest.raises(ValueError, match=r"^requirements\[2\]: duplicate id R0$"):
        COV([ok, ("R9", "t"), ("R0", "u")], [])
    for bad in ("", "  ", None, 3, ["t"], "x" * 81):
        with pytest.raises(ValueError, match=r"^requirements\[1\] title: non-empty string up to 80 characters required$"):
            COV([ok, ("R1", bad)], [])
    assert COV([ok, ("R1", "x" * 80)], [])["requirements"][1]["title"] == "x" * 80


def test_control_validation():
    reqs = [("R0", "t")]
    for bad in ("abc", None, 5):
        with pytest.raises(ValueError, match=r"^controls: list required$"):
            COV(reqs, bad)
    assert COV(reqs, [])["requirements"][0]["controls"] == []          # zero controls allowed
    many = [(f"C{i}", "t", []) for i in range(201)]
    with pytest.raises(ValueError, match=r"^controls: 0 to 200 entries required$"):
        COV(reqs, many)
    assert len(COV(reqs, many[:200])["orphan_controls"]) == 200
    ok = ("C0", "t", ["R0"])
    for bad in ("abc", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"^controls\[1\]: \(cid, title, rids\) required$"):
            COV(reqs, [ok, bad])
    for bad in (("C1", "t"), ("C1", "t", [], 1), ()):
        with pytest.raises(ValueError, match=r"^controls\[1\]: 3 entries required$"):
            COV(reqs, [ok, bad])
    for bad in ("", None, 3, ["C1"], "x" * 21):
        with pytest.raises(ValueError, match=r"^controls\[1\] id: non-empty string up to 20 characters required$"):
            COV(reqs, [ok, (bad, "t", [])])
    with pytest.raises(ValueError, match=r"^controls\[2\]: duplicate id C0$"):
        COV(reqs, [ok, ("C9", "t", []), ("C0", "u", [])])
    for bad in ("", "  ", None, 3, ["t"], "x" * 81):
        with pytest.raises(ValueError, match=r"^controls\[1\] title: non-empty string up to 80 characters required$"):
            COV(reqs, [ok, ("C1", bad, [])])
    for bad in ("R0", None, 5, {"R0": 1}):
        with pytest.raises(ValueError, match=r"^controls\[1\] rids: list required$"):
            COV(reqs, [ok, ("C1", "t", bad)])
    with pytest.raises(ValueError, match=r"^controls\[1\] rids: at most 50 entries allowed$"):
        COV(reqs, [ok, ("C1", "t", [f"R{i}" for i in range(51)])])
    with pytest.raises(ValueError, match=r"^controls\[1\] rids: duplicates not allowed$"):
        COV(reqs, [ok, ("C1", "t", ["R0", "R0"])])
    for bad in ("", None, 3, ["R0"], "x" * 21):
        with pytest.raises(ValueError, match=r"^controls\[1\] rids\[1\]: non-empty string up to 20 characters required$"):
            COV(reqs, [ok, ("C1", "t", ["R0", bad])])
    r50 = [("R0", "t")] + [(f"R{i}", "t") for i in range(1, 50)]
    assert COV(r50, [("C1", "t", [r[0] for r in r50])])["covered_share"] == 1     # 50 refs allowed
    assert COV([("x" * 20, "t")], [("C1", "t", ["x" * 20])])["uncovered"] == []     # a 20-char ref is allowed
    with pytest.raises(ValueError, match=r"^controls\[1\] rids: unknown requirement R9$"):
        COV(reqs, [ok, ("C1", "t", ["R9"])])
    r = COV(reqs, [ok, ["C1", "t", ["R0"]]])
    assert r["requirements"][0]["controls"] == ["C0", "C1"]           # list rows accepted

import inspect
import random

import pytest
from sugarcode.extra_doc import ci_pipeline as ci

P = ci.plan


def test_constants_signature():
    assert (ci.MAX_JOBS, ci.MAX_NAME, ci.MAX_NEEDS) == (100, 30, 20)
    assert ci.STATUS_NOTE.startswith("PARTIAL") and "nothing is built or run" in ci.STATUS_NOTE
    assert list(inspect.signature(P).parameters) == ["jobs"]


def test_hand_literals():
    jobs = [("deploy", ["test", "lint"]), ("test", ["build"]), ("lint", []), ("build", []), ("docs", ["lint"])]
    r = P(jobs)
    assert r["stages"] == [["build", "lint"], ["docs", "test"], ["deploy"]]
    assert r["ok"] is True and r["stuck"] == [] and r["status_note"] == ci.STATUS_NOTE
    assert P([("a", [])])["stages"] == [["a"]]
    assert P([("b", []), ("a", []), ("c", [])])["stages"] == [["a", "b", "c"]]          # order is by name, not input
    assert P([("c", ["b"]), ("b", ["a"]), ("a", [])])["stages"] == [["a"], ["b"], ["c"]]
    # diamond: d needs b and c, which each need a ; d lands in stage 3, not 2
    assert P([("d", ["b", "c"]), ("b", ["a"]), ("c", ["a"]), ("a", [])])["stages"] == [["a"], ["b", "c"], ["d"]]
    # long chain next to a short one: z needs both a deep and a shallow job, so it waits for the deep one
    r = P([("z", ["s", "c3"]), ("c3", ["c2"]), ("c2", ["c1"]), ("c1", []), ("s", [])])
    assert r["stages"] == [["c1", "s"], ["c2"], ["c3"], ["z"]]
    r = P([("a", ["b"]), ("b", ["a"]), ("c", ["a"]), ("d", [])])
    assert (r["ok"], r["stages"], r["stuck"]) == (False, [["d"]], ["a", "b", "c"])
    r = P([("a", ["a"])])
    assert (r["ok"], r["stages"], r["stuck"]) == (False, [], ["a"])
    assert P((("x", ()), ("y", ("x",))))["stages"] == [["x"], ["y"]]


def oracle(jobs):
    deps = {n: set(d) for n, d in jobs}
    reach = {n: set(d) for n, d in jobs}                  # transitive closure by repeated expansion
    changed = True
    while changed:
        changed = False
        for n in reach:
            new = set().union(*[reach[m] for m in reach[n]]) - reach[n] if reach[n] else set()
            if new:
                reach[n] |= new
                changed = True
    cyc = {n for n in reach if n in reach[n]}
    stuck = sorted(n for n in reach if n in cyc or reach[n] & cyc)
    depth = {}

    def d(n):
        if n not in depth:
            depth[n] = 1 + max((d(m) for m in deps[n]), default=0)
        return depth[n]
    stages = {}
    for n in deps:
        if n not in stuck:
            stages.setdefault(d(n), []).append(n)
    return [sorted(stages[k]) for k in sorted(stages)], stuck


def test_oracle_closure_and_depth():
    rnd = random.Random(610)
    for _ in range(400):
        n = rnd.randint(1, 8)
        names = [f"j{i}" for i in range(n)]
        rnd.shuffle(names)
        jobs = [(nm, rnd.sample(names, rnd.randint(0, min(3, n)))) for nm in names]
        r = P(jobs)
        want_stages, want_stuck = oracle(jobs)
        assert (r["stages"], r["stuck"], r["ok"]) == (want_stages, want_stuck, not want_stuck), jobs


def test_caps_both_sides():
    chain = [(f"n{i}", [f"n{i - 1}"] if i else []) for i in range(100)]
    assert len(P(chain)["stages"]) == 100
    with pytest.raises(ValueError, match=r"^jobs: 1 to 100 entries required$"):
        P(chain + [("extra", [])])
    with pytest.raises(ValueError, match=r"^jobs: 1 to 100 entries required$"):
        P([])
    assert P([("a" * 30, [])])["stages"] == [["a" * 30]]
    with pytest.raises(ValueError, match=r"^jobs\[0\] name: non-empty string up to 30 characters required$"):
        P([("a" * 31, [])])
    base = [(f"d{i}", []) for i in range(21)]
    ok = P(base + [("top", [f"d{i}" for i in range(20)])])
    assert ok["stages"][1] == ["top"]
    with pytest.raises(ValueError, match=r"^jobs\[21\] needs: at most 20 entries$"):
        P(base + [("top", [f"d{i}" for i in range(21)])])


def test_shape_and_type_refusals():
    for bad in ("ab", None, 5, {"a": []}):
        with pytest.raises(ValueError, match=r"^jobs: list required$"):
            P(bad)
    for bad in ("ab", None, 3):
        with pytest.raises(ValueError, match=r"^jobs\[0\]: \(name, needs\) required$"):
            P([bad])
    for bad in [("a",), ("a", [], 1), ()]:
        with pytest.raises(ValueError, match=r"^jobs\[1\]: 2 entries required$"):
            P([("ok", []), bad])
    for bad in ("", None, 5, True, b"a", ["a"]):
        with pytest.raises(ValueError, match=r"^jobs\[0\] name: non-empty string"):
            P([(bad, [])])
    for bad in ("ab", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"^jobs\[0\] needs: list required$"):
            P([("a", bad)])
    for bad in (1, None, ["a"], True):
        with pytest.raises(ValueError, match=r"^jobs\[0\] needs: names must be strings$"):
            P([("a", [bad])])
    with pytest.raises(ValueError, match=r"^jobs\[1\] name: duplicate$"):
        P([("a", []), ("a", [])])
    with pytest.raises(ValueError, match=r"^jobs\[1\] needs: duplicate entry$"):
        P([("a", []), ("b", ["a", "a"])])
    with pytest.raises(ValueError, match=r"^jobs\[0\] needs: unknown job$"):
        P([("a", ["ghost"])])
    with pytest.raises(ValueError, match=r"^jobs\[1\] needs: unknown job$"):
        P([("a", []), ("b", ["a", "ghost"])])
    with pytest.raises(ValueError, match=r"^jobs\[0\] needs: names must be strings$"):
        P([("a", [5, 5])])                                   # type check before duplicate check

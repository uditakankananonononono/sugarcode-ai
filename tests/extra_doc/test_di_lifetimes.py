import re
import pytest
from sugarcode.extra_doc import di_lifetimes as dl

C = dl.check
NC = ("a dependency injection container", "object resolution", "thread safety",
      "design quality", "runtime behaviour")
NM = "name of a-z, 0-9, _ (1 to 30, starting with a letter) required"
LT = "'singleton', 'scoped' or 'transient' required"
TAB = [("cache", "singleton", ["repo", "clock"]), ("repo", "scoped", ["clock"]), ("clock", "transient", [])]


class Li(list):
    pass


class Tu(tuple):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        C(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def test_constants():
    assert (dl.MAX_SERVICES, dl.MAX_DEPS) == (32, 8) and dl.RANK == {"singleton": 2, "scoped": 1, "transient": 0}
    assert dl.NOT_CLAIMED == NC


def test_hand_literals():
    r = C(TAB)
    assert r["violations"] == [("cache", "repo"), ("cache", "clock"), ("repo", "clock")]
    assert r["lifetimes_consistent"] is False
    ok = [("a", "transient", ["b", "c"]), ("b", "scoped", ["c"]), ("c", "singleton", [])]
    assert C(ok)["violations"] == [] and C(ok)["lifetimes_consistent"] is True
    same = [("a", "scoped", ["b"]), ("b", "scoped", [])]
    assert C(same)["violations"] == []                      # equal rank is allowed
    assert C([("a", "singleton", ["b"]), ("b", "scoped", [])])["violations"] == [("a", "b")]
    assert C([("a", "scoped", ["b"]), ("b", "transient", [])])["violations"] == [("a", "b")]
    assert C([("a", "singleton", ["b"]), ("b", "transient", [])])["violations"] == [("a", "b")]


def test_shape_and_untouched():
    t = [("a", "singleton", []), ("b", "scoped", ["a"])]
    r = C(t)
    assert t == [("a", "singleton", []), ("b", "scoped", ["a"])]
    assert r == {"violations": [], "lifetimes_consistent": True, "di_validated": False, "not_claimed": NC}


def test_independent_oracle():
    import itertools
    order = ["transient", "scoped", "singleton"]
    for lts in itertools.product(order, repeat=3):
        for mask in range(8):
            names = ["a", "b", "c"]
            deps_by = {0: ["b", "c"], 1: ["c"], 2: []}
            table = [(n, lts[i], [d for k, d in enumerate(deps_by[i]) if mask >> k & 1]) for i, n in enumerate(names)]
            want = []
            for n, lt, deps in table:
                for d in deps:
                    if order.index(lts[names.index(d)]) < order.index(lt):
                        want.append((n, d))
            assert C(table)["violations"] == want


def test_caps_accepted():
    names = [f"s{i}" for i in range(32)]
    table = [(n, "transient", [x for x in names[:8] if x != n]) for n in names]
    assert C(table)["lifetimes_consistent"] is True
    big = [("a" * 30, "singleton", []), ("b", "singleton", ["a" * 30])]
    assert C(big)["violations"] == []
    deps = [f"d{i}" for i in range(8)]
    t = [(d, "transient", []) for d in deps] + [("top", "singleton", list(deps))]
    assert len(C(t)["violations"]) == 8


BAD = [None, 5, "", "A", "1a", "_a", "a-b", "a\n", "\u00e9", "a\u00e9", "\uff41", "a" * 31, St("a"), b"a"]


@pytest.mark.parametrize("bad", BAD)
def test_name_refusals(bad):
    refuse(f"services[0] name: {NM}", [(bad, "scoped", [])])
    refuse(f"services[1] name: {NM}", [("a", "scoped", []), (bad, "scoped", [])])


@pytest.mark.parametrize("bad", [None, 1, "", "Singleton", "SCOPED", "scoped ", "singleton\n", "tr\u0430nsient",
                                 St("scoped"), b"scoped", "perm"])
def test_lifetime_refusals(bad):
    refuse(f"services[0] lifetime: {LT}", [("a", bad, [])])
    refuse(f"services[1] lifetime: {LT}", [("a", "scoped", []), ("b", bad, [])])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([]), ("a",)])
def test_dependencies_shape(bad):
    refuse("services[0] dependencies: list of 0 to 8 required", [("a", "scoped", bad)])
    refuse("services[1] dependencies: list of 0 to 8 required", [("a", "scoped", []), ("b", "scoped", bad)])


def test_dependencies_cap():
    names = [f"d{i}" for i in range(9)]
    refuse("services[0] dependencies: list of 0 to 8 required", [("top", "scoped", names)] + [(n, "scoped", []) for n in names])


@pytest.mark.parametrize("bad", [[], ("a", "scoped"), ("a", "scoped", [], 1), Tu(("a", "scoped", [])),
                                 ["a", "scoped", []], None, "abc"])
def test_row_shape(bad):
    refuse("services[0]: (name, lifetime, dependencies) tuple required", [bad])
    refuse("services[1]: (name, lifetime, dependencies) tuple required", [("a", "scoped", []), bad])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([("a", "scoped", [])]), [], [(f"s{i}", "scoped", []) for i in range(33)]])
def test_services_shape(bad):
    refuse("services: list of 1 to 32 required", bad)


@pytest.mark.parametrize("bad", [None, 5, "missing", "A", "\u00e9", St("b"), b"b", ["b"]])
def test_dependency_name_refusals(bad):
    t = [("a", "scoped", [bad]), ("b", "scoped", [])]
    refuse("services[0] dependencies[0]: name of a service in the table required", t)
    t = [("a", "scoped", ["b", bad]), ("b", "scoped", [])]
    refuse("services[0] dependencies[1]: name of a service in the table required", t)
    t = [("b", "scoped", []), ("a", "scoped", ["b", bad])]
    refuse("services[1] dependencies[1]: name of a service in the table required", t)


def test_self_distinct_and_order():
    refuse("services[0] dependencies[0]: a service cannot depend on itself", [("a", "scoped", ["a"])])
    refuse("services[1] dependencies[1]: a service cannot depend on itself",
           [("b", "scoped", []), ("a", "scoped", ["b", "a"])])
    refuse("services[0] dependencies: names must be distinct", [("a", "scoped", ["b", "b"]), ("b", "scoped", [])])
    refuse("services: names must be distinct", [("a", "scoped", []), ("a", "scoped", [])])
    refuse("services: names must be distinct", [("a", "scoped", ["zz"]), ("a", "scoped", [])])
    refuse("services[0] dependencies[0]: name of a service in the table required", [("a", "scoped", ["zz", "zz"])])
    refuse("services: list of 1 to 32 required", None)

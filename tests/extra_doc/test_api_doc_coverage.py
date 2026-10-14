import re
import pytest
from sugarcode.extra_doc import api_doc_coverage as ad

C = ad.compare
NC = ("accuracy of the documentation", "clarity or wording", "completeness beyond parameter names",
      "an API specification", "runtime behaviour")
NM = "name of a-z, 0-9, _ (1 to 30, starting with a letter) required"
EP = [("list_users", ["limit", "offset"]), ("get_user", ["id"]), ("ping", [])]
DOC = [("get_user", ["id", "verbose"]), ("list_users", ["limit"]), ("old_call", ["x"])]


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
    assert (ad.MAX_ENDPOINTS, ad.MAX_PARAMS) == (32, 8) and ad.NOT_CLAIMED == NC


def test_hand_literals():
    r = C(EP, DOC)
    assert r["endpoints"] == [
        {"endpoint": "list_users", "undocumented_params": ["offset"], "stale_doc_params": []},
        {"endpoint": "get_user", "undocumented_params": [], "stale_doc_params": ["verbose"]}]
    assert r["endpoints_without_docs"] == ["ping"]
    assert r["docs_without_endpoint"] == ["old_call"]
    r = C([("a", ["x", "y", "z"])], [("a", ["z", "q", "x"])])
    assert r["endpoints"] == [{"endpoint": "a", "undocumented_params": ["y"], "stale_doc_params": ["q"]}]
    assert C([("a", [])], [("a", [])])["endpoints"] == [{"endpoint": "a", "undocumented_params": [],
                                                         "stale_doc_params": []}]
    assert C([("a", ["p"])], [])["endpoints_without_docs"] == ["a"]


def test_shape_and_untouched():
    ep, dc = [("a", ["x"])], [("a", ["x"])]
    r = C(ep, dc)
    assert ep == [("a", ["x"])] and dc == [("a", ["x"])]
    assert r == {"endpoints": [{"endpoint": "a", "undocumented_params": [], "stale_doc_params": []}],
                 "endpoints_without_docs": [], "docs_without_endpoint": [],
                 "documentation_validated": False, "not_claimed": NC}


def test_independent_oracle():
    import random
    rnd = random.Random(704)
    pool = ["p", "q", "r", "s", "t"]
    for _ in range(200):
        names = rnd.sample(["a", "b", "c", "d", "e"], rnd.randint(1, 5))
        eps = [(n, rnd.sample(pool, rnd.randint(0, 5))) for n in names]
        dnames = rnd.sample(["a", "b", "c", "d", "e", "f"], rnd.randint(0, 6))
        dcs = [(n, rnd.sample(pool, rnd.randint(0, 5))) for n in dnames]
        r = C(eps, dcs)
        want_rows = []
        for n, ps in eps:
            for dn, dps in dcs:
                if dn == n:
                    want_rows.append({"endpoint": n, "undocumented_params": [p for p in ps if p not in dps],
                                      "stale_doc_params": [p for p in dps if p not in ps]})
        assert r["endpoints"] == want_rows
        assert r["endpoints_without_docs"] == [n for n, _ in eps if n not in dnames]
        assert r["docs_without_endpoint"] == [n for n in dnames if n not in names]


def test_caps_accepted():
    ps = [f"p{i}" for i in range(8)]
    eps = [(f"e{i}", list(ps)) for i in range(32)]
    r = C(eps, [(f"e{i}", []) for i in range(32)])
    assert len(r["endpoints"]) == 32 and r["endpoints"][31]["undocumented_params"] == ps
    assert C([("a" * 30, ["b" * 30])], [("a" * 30, ["b" * 30])])["endpoints"][0]["undocumented_params"] == []
    assert C([("a", [])], [(f"d{i}", []) for i in range(32)])["docs_without_endpoint"][-1] == "d31"


BAD = [None, 5, "", "A", "1a", "_a", "a-b", "a\n", "\u00e9", "a\u00e9", "\uff41", "a" * 31, St("a"), b"a"]


@pytest.mark.parametrize("bad", BAD)
def test_name_refusals(bad):
    for label, mk in (("endpoints", lambda row: C([row], [])), ("docs", lambda row: C([("a", [])], [row]))):
        with pytest.raises(ValueError) as e:
            mk((bad, []))
        assert str(e.value) == f"{label}[0] name: {NM}"
        with pytest.raises(ValueError) as e:
            mk(("ok", [bad]))
        assert str(e.value) == f"{label}[0] params[0]: {NM}"
        with pytest.raises(ValueError) as e:
            mk(("ok", ["p", bad]))
        assert str(e.value) == f"{label}[0] params[1]: {NM}"
    refuse(f"endpoints[1] name: {NM}", [("a", []), (bad, [])], [])
    refuse(f"docs[1] name: {NM}", [("a", [])], [("a", []), (bad, [])])


@pytest.mark.parametrize("bad", [(), None, "ab", Li(["x"]), ("x",)])
def test_params_shape(bad):
    refuse("endpoints[0] params: list of 0 to 8 required", [("a", bad)], [])
    refuse("endpoints[1] params: list of 0 to 8 required", [("a", []), ("b", bad)], [])
    refuse("docs[1] params: list of 0 to 8 required", [("a", [])], [("a", []), ("a2", bad)])


def test_params_cap_and_distinct():
    nine = [f"p{i}" for i in range(9)]
    refuse("endpoints[0] params: list of 0 to 8 required", [("a", nine)], [])
    refuse("docs[0] params: list of 0 to 8 required", [("a", [])], [("a", nine)])
    refuse("endpoints[0] params: names must be distinct", [("a", ["x", "x"])], [])
    refuse("docs[0] params: names must be distinct", [("a", [])], [("a", ["x", "x"])])


@pytest.mark.parametrize("bad", [[], ("a",), ("a", [], 1), Tu(("a", [])), ["a", []], None, "ab"])
def test_row_shape(bad):
    refuse("endpoints[0]: (name, params) tuple required", [bad], [])
    refuse("endpoints[1]: (name, params) tuple required", [("a", []), bad], [])
    refuse("docs[0]: (name, params) tuple required", [("a", [])], [bad])
    refuse("docs[1]: (name, params) tuple required", [("a", [])], [("a", []), bad])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([("a", [])]), [], [(f"e{i}", []) for i in range(33)]])
def test_endpoints_shape(bad):
    refuse("endpoints: list of 1 to 32 required", bad, [])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([]), [(f"e{i}", []) for i in range(33)]])
def test_docs_shape(bad):
    refuse("docs: list of 0 to 32 required", [("a", [])], bad)


def test_distinct_and_order():
    refuse("endpoints: names must be distinct", [("a", []), ("a", [])], [])
    refuse("docs: names must be distinct", [("a", [])], [("b", []), ("b", [])])
    refuse("endpoints: names must be distinct", [("a", []), ("a", [])], None)
    refuse("endpoints: list of 1 to 32 required", None, None)
    refuse("docs: list of 0 to 32 required", [("a", [])], None)

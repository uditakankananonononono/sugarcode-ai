import inspect
import random

import pytest
from sugarcode.extra_doc import gateway_routes as gr

R = gr.route
TABLE = [("/", ["GET"], "web"), ("/api", ["GET", "POST"], "api"), ("/api/users", ["GET"], "users"),
         ("/admin", ["DELETE", "PUT"], "admin")]


def st(r):
    return (r["status"], r["target"], r["prefix"], r["allowed"])


def test_constants_signature():
    assert (gr.MAX_ROUTES, gr.MAX_PREFIX, gr.MAX_TARGET, gr.MAX_PATH) == (50, 60, 30, 200)
    assert gr.METHODS == ("GET", "POST", "PUT", "PATCH", "DELETE")
    assert gr.STATUS_NOTE.startswith("PARTIAL") and "nothing is forwarded" in gr.STATUS_NOTE
    assert list(inspect.signature(R).parameters) == ["routes", "method", "path"]


def test_hand_literals():
    assert st(R(TABLE, "GET", "/api/users/7")) == (200, "users", "/api/users", None)       # longest prefix
    assert st(R(TABLE, "POST", "/api/users/7")) == (200, "api", "/api", None)              # falls back to a shorter prefix that allows it
    assert st(R(TABLE, "GET", "/api")) == (200, "api", "/api", None)                       # exact match
    assert st(R(TABLE, "GET", "/apix")) == (200, "web", "/", None)                         # not a segment match
    assert st(R(TABLE, "GET", "/")) == (200, "web", "/", None)
    assert st(R(TABLE, "PATCH", "/api/users")) == (405, None, None, ["GET", "POST"])       # union over / and /api and /api/users
    assert st(R(TABLE, "GET", "/admin/x")) == (200, "web", "/", None)                      # admin denies GET, root allows it
    assert st(R(TABLE, "POST", "/admin")) == (405, None, None, ["DELETE", "GET", "PUT"])
    only = [("/api", ["GET"], "api")]
    assert st(R(only, "GET", "/other")) == (404, None, None, None)
    assert st(R(only, "POST", "/api/x")) == (405, None, None, ["GET"])
    assert st(R(only, "GET", "/api/")) == (200, "api", "/api", None)                       # trailing slash continues after "/"
    assert st(R(only, "GET", "/api//x")) == (200, "api", "/api", None)
    assert st(R(only, "GET", "/API")) == (404, None, None, None)                           # case sensitive
    assert R(only, "GET", "/api")["status_note"] == gr.STATUS_NOTE
    assert st(R((("/a", ("GET",), "t"),), "GET", "/a")) == (200, "t", "/a", None)


def oracle(routes, method, path):
    segs = [x for x in path.split("/")[1:]]
    cands = []
    for prefix, methods, target in routes:
        ps = [] if prefix == "/" else prefix.split("/")[1:]
        if segs[:len(ps)] == ps:
            cands.append((len(ps), prefix, methods, target))
    cands.sort(key=lambda c: -c[0])
    for _, prefix, methods, target in cands:
        if method in methods:
            return (200, target, prefix, None)
    if cands:
        return (405, None, None, sorted({m for c in cands for m in c[2]}))
    return (404, None, None, None)


def test_oracle_segment_matching():
    rnd = random.Random(616)
    parts = ["a", "b", "ab", ""]
    meths = list(gr.METHODS)
    for _ in range(600):
        prefixes = set()
        for _ in range(rnd.randint(1, 4)):
            n = rnd.randint(0, 3)
            ps = [rnd.choice(["a", "b", "ab"]) for _ in range(n)]
            prefixes.add("/" + "/".join(ps) if ps else "/")
        routes = [(p, rnd.sample(meths, rnd.randint(1, 3)), f"t{i}") for i, p in enumerate(sorted(prefixes))]
        path = "/" + "/".join(rnd.choice(parts) for _ in range(rnd.randint(0, 4)))
        m = rnd.choice(meths)
        assert st(R(routes, m, path)) == oracle(routes, m, path), (routes, m, path)


def test_caps_both_sides():
    big = [(f"/p{i}", ["GET"], "t") for i in range(50)]
    assert R(big, "GET", "/p49")["status"] == 200
    with pytest.raises(ValueError, match=r"^routes: 1 to 50 entries required$"):
        R(big + [("/p50", ["GET"], "t")], "GET", "/")
    with pytest.raises(ValueError, match=r"^routes: 1 to 50 entries required$"):
        R([], "GET", "/")
    long_prefix = "/" + "a" * 59
    assert R([(long_prefix, ["GET"], "t")], "GET", long_prefix)["status"] == 200
    with pytest.raises(ValueError, match=r"^routes\[0\] prefix: must start with /"):
        R([("/" + "a" * 60, ["GET"], "t")], "GET", "/")
    assert R([("/a", ["GET"], "t" * 30)], "GET", "/a")["target"] == "t" * 30
    with pytest.raises(ValueError, match=r"^routes\[0\] target: non-empty string up to 30 characters required$"):
        R([("/a", ["GET"], "t" * 31)], "GET", "/a")
    with pytest.raises(ValueError, match=r"^routes\[0\] target: non-empty string up to 30 characters required$"):
        R([("/a", ["GET"], "")], "GET", "/a")
    p200 = "/" + "a" * 199
    assert R([("/", ["GET"], "t")], "GET", p200)["status"] == 200
    with pytest.raises(ValueError, match=r"^path: must start with / and be at most 200 characters$"):
        R([("/", ["GET"], "t")], "GET", p200 + "a")
    assert R([("/", list(gr.METHODS), "t")], "GET", "/")["status"] == 200
    with pytest.raises(ValueError, match=r"^routes\[0\] methods: list of 1 to 5 entries required$"):
        R([("/", list(gr.METHODS) + ["GET"], "t")], "GET", "/")
    with pytest.raises(ValueError, match=r"^routes\[0\] methods: list of 1 to 5 entries required$"):
        R([("/", [], "t")], "GET", "/")


def test_validation_messages_and_types():
    ok = [("/", ["GET"], "t")]
    for bad in ("get", "OPTIONS", ""):
        with pytest.raises(ValueError, match=r"^method: must be one of GET, POST, PUT, PATCH, DELETE$"):
            R(ok, bad, "/")
    for bad in (None, 5, b"GET", ["GET"]):
        with pytest.raises(ValueError, match=r"^method: string required$"):
            R(ok, bad, "/")
        with pytest.raises(ValueError, match=r"^path: string required$"):
            R(ok, "GET", bad)
    for bad in ("", "api", " /"):
        with pytest.raises(ValueError, match=r"^path: must start with /"):
            R(ok, "GET", bad)
    for bad in ("ab", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"^routes: list required$"):
            R(bad, "GET", "/")
    for bad in ("ab", None, 3):
        with pytest.raises(ValueError, match=r"^routes\[0\]: \(prefix, methods, target\) required$"):
            R([bad], "GET", "/")
    for bad in [("/a", ["GET"]), ("/a", ["GET"], "t", 1), ()]:
        with pytest.raises(ValueError, match=r"^routes\[1\]: 3 entries required$"):
            R(ok + [bad], "GET", "/")
    for bad in (None, 5, "", "a", "/a/", "/a b", "/a\tb", "//x/", b"/a"):
        if bad == "//x/":
            bad = "/x/"
        with pytest.raises(ValueError, match=r"^routes\[0\] prefix: must start with /"):
            R([(bad, ["GET"], "t")], "GET", "/")
    for bad in (None, "GET", 5):
        with pytest.raises(ValueError, match=r"^routes\[0\] methods: list of 1 to 5 entries required$"):
            R([("/", bad, "t")], "GET", "/")
    for bad in ("get", "HEAD", 5, None, ["GET"]):
        with pytest.raises(ValueError, match=r"^routes\[0\] methods: each must be one of"):
            R([("/", [bad], "t")], "GET", "/")
    with pytest.raises(ValueError, match=r"^routes\[0\] methods: duplicate entry$"):
        R([("/", ["GET", "GET"], "t")], "GET", "/")
    with pytest.raises(ValueError, match=r"^routes\[1\] prefix: duplicate$"):
        R([("/a", ["GET"], "t"), ("/a", ["POST"], "u")], "GET", "/")
    for bad in (None, 5, b"t", ["t"]):
        with pytest.raises(ValueError, match=r"^routes\[0\] target: non-empty string"):
            R([("/", ["GET"], bad)], "GET", "/")
    with pytest.raises(ValueError, match=r"^method: string required$"):
        R("bad", None, None)                                  # method is checked first
    with pytest.raises(ValueError, match=r"^path: string required$"):
        R("bad", "GET", None)
    with pytest.raises(ValueError, match=r"^routes: list required$"):
        R("bad", "GET", "/")


# ---- exact-type hardening (v2): subclasses of str, list and tuple are refused at every slot ----
class S(str):
    pass


class LyingS(str):
    """Equal to and hashing like 'GET' whatever its text."""
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    __hash__ = str.__hash__


class L(list):
    pass


class T(tuple):
    pass


GOOD = ("/a", ["GET"], "t")
M_ROUTES = r"^routes: list required$"


def _bad(msg, *args):
    with pytest.raises(ValueError, match=msg):
        R(*args)


def test_exact_builtin_acceptance_for_list_and_tuple_shapes():
    assert st(R([("/a", ["GET", "POST"], "t")], "POST", "/a")) == (200, "t", "/a", None)
    assert st(R((("/a", ("GET", "POST"), "t"),), "POST", "/a")) == (200, "t", "/a", None)
    assert st(R((["/a", ("GET",), "t"],), "GET", "/a")) == (200, "t", "/a", None)
    assert st(R([("/a", ["GET"], "t"), ["/b", ("POST", "GET"), "u"]], "PUT", "/b")) == (405, None, None, ["GET", "POST"])


def test_str_subclass_method_and_path_refused_before_membership():
    _bad(r"^method: string required$", [GOOD], S("GET"), "/a")
    _bad(r"^method: string required$", [GOOD], LyingS("zzz"), "/a")
    _bad(r"^method: string required$", [GOOD], LyingS("GET"), "/a")
    _bad(r"^path: string required$", [GOOD], "GET", S("/a"))
    _bad(r"^path: string required$", [GOOD], "GET", LyingS("zzz"))


def test_routes_list_and_tuple_subclass_refused():
    for K in (L, T):
        _bad(M_ROUTES, K([GOOD]), "GET", "/a")
    _bad(M_ROUTES, L(), "GET", "/a")
    _bad(M_ROUTES, T(), "GET", "/a")
    _bad(M_ROUTES, L([GOOD] * 51), "GET", "/a")          # subclass refused before the size cap


def test_row_list_and_tuple_subclass_refused_first_and_later():
    for K in (L, T):
        row = K(GOOD)
        _bad(r"^routes\[0\]: \(prefix, methods, target\) required$", [row], "GET", "/a")
        _bad(r"^routes\[1\]: \(prefix, methods, target\) required$", [("/b", ["GET"], "u"), row], "GET", "/a")
        _bad(r"^routes\[0\]: \(prefix, methods, target\) required$", [K(("/a", ["GET"])), GOOD], "GET", "/a")


def test_methods_list_and_tuple_subclass_refused_first_and_later():
    for K in (L, T):
        _bad(r"^routes\[0\] methods: list of 1 to 5 entries required$", [("/a", K(["GET"]), "t")], "GET", "/a")
        _bad(r"^routes\[1\] methods: list of 1 to 5 entries required$", [("/b", ["GET"], "u"), ("/a", K(["GET"]), "t")], "GET", "/a")
        _bad(r"^routes\[0\] methods: list of 1 to 5 entries required$", [("/a", K(), "t")], "GET", "/a")


def test_methods_element_str_subclass_refused_first_and_later_and_lying_eq():
    msg = r"^routes\[0\] methods: each must be one of GET, POST, PUT, PATCH, DELETE$"
    for bad in (S("GET"), LyingS("GET"), LyingS("zzz")):
        _bad(msg, [("/a", [bad], "t")], "GET", "/a")
        _bad(msg, [("/a", ["GET", bad], "t")], "GET", "/a")
        _bad(msg, [("/a", ("POST", bad), "t")], "POST", "/a")
    # a lying object may not pass the duplicate check or the membership check as a plain name
    _bad(msg, [("/a", [LyingS("GET"), LyingS("GET")], "t")], "GET", "/a")


def test_prefix_and_target_str_subclass_refused_first_and_later():
    pm = r"^routes\[%d\] prefix: must start with /, have no whitespace or trailing / and be at most 60 characters$"
    tm = r"^routes\[%d\] target: non-empty string up to 30 characters required$"
    for bad in (S("/a"), LyingS("/a"), LyingS("zzz")):
        _bad(pm % 0, [(bad, ["GET"], "t")], "GET", "/a")
        _bad(pm % 1, [("/b", ["GET"], "u"), (bad, ["GET"], "t")], "GET", "/a")
    for bad in (S("t"), LyingS("t"), LyingS("")):
        _bad(tm % 0, [("/a", ["GET"], bad)], "GET", "/a")
        _bad(tm % 1, [("/b", ["GET"], "u"), ("/a", ["GET"], bad)], "GET", "/a")


def test_prefix_boundaries_and_full_messages():
    pm = r"^routes\[0\] prefix: must start with /, have no whitespace or trailing / and be at most 60 characters$"
    assert st(R([("/", ["GET"], "t")], "GET", "/x")) == (200, "t", "/", None)
    assert st(R([("/" + "a" * 59, ["GET"], "t")], "GET", "/" + "a" * 59)) == (200, "t", "/" + "a" * 59, None)
    for bad in ("/" + "a" * 60, "/a/", "//", "/a b", "/a\u00a0b", "/a\nb", "a", ""):
        _bad(pm, [(bad, ["GET"], "t")], "GET", "/a")
    assert R([("/a/b", ["GET"], "t")], "GET", "/a/b")["status"] == 200


def test_full_anchored_messages_for_remaining_validation_paths():
    _bad(r"^routes\[0\]: 3 entries required$", [("/a", ["GET"])], "GET", "/a")
    _bad(r"^routes\[0\] methods: duplicate entry$", [("/a", ("GET", "GET"), "t")], "GET", "/a")
    _bad(r"^routes\[2\] prefix: duplicate$", [("/a", ["GET"], "t"), ("/b", ["GET"], "t"), ("/a", ["GET"], "t")], "GET", "/a")
    _bad(r"^routes\[0\] methods: each must be one of GET, POST, PUT, PATCH, DELETE$", [("/a", ["get"], "t")], "GET", "/a")
    _bad(r"^routes: 1 to 50 entries required$", [], "GET", "/a")
    _bad(r"^routes: 1 to 50 entries required$", [GOOD] * 51, "GET", "/a")
    assert st(R([(f"/p{i}", ["GET"], "t") for i in range(50)], "GET", "/p0")) == (200, "t", "/p0", None)


def test_validation_order_method_path_routes_then_rows():
    _bad(r"^method: string required$", S("GET"), S("GET"), S("/"))
    _bad(r"^path: string required$", S("x"), "GET", S("/"))
    _bad(r"^path: must start with / and be at most 200 characters$", S("x"), "GET", "x")
    _bad(M_ROUTES, S("x"), "GET", "/")


def test_405_union_and_result_shape_with_tuples():
    r = R((("/a", ("POST", "GET"), "t"), ("/", ["PUT"], "u")), "DELETE", "/a/x")
    assert r == {"status": 405, "target": None, "prefix": None, "allowed": ["GET", "POST", "PUT"],
                 "status_note": gr.STATUS_NOTE}
    assert set(R(TABLE, "GET", "/")) == {"status", "target", "prefix", "allowed", "status_note"}

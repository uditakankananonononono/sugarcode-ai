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

import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import bayes_update as m
from sugarcode.extra_doc.bayes_update import UpdateError, bayes_update as run

KEYS = "data keys must be exactly hypotheses, observations"


def H(prior, like):
    return {"prior": list(prior), "likelihood": {k: list(v) for k, v in like.items()}}


def d(obs=("h",), hyps=None):
    hyps = hyps or {"fair": H((1, 2), {"h": (1, 2), "t": (1, 2)}), "biased": H((1, 2), {"h": (9, 10), "t": (1, 10)})}
    return {"hypotheses": hyps, "observations": list(obs)}


def bad(data, msg):
    with pytest.raises(UpdateError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(data):
    """Independent: batch posterior = prior * product of likelihoods, normalised once at the end."""
    hs = data["hypotheses"]
    res = []
    for k in range(1, len(data["observations"]) + 1):
        w = {}
        for h, b in hs.items():
            v = F(*b["prior"])
            for s in data["observations"][:k]:
                v *= F(*b["likelihood"][s])
            w[h] = v
        t = sum(w.values())
        res.append({h: w[h] / t for h in sorted(w)})
    return res


def check(data):
    o = run(data)
    ex = oracle(data)
    assert [{h: F(v) for h, v in step.items()} for step in o["history"]] == ex
    assert {h: F(v) for h, v in o["posterior"].items()} == ex[-1]
    best = sorted(ex[-1], key=lambda h: (-ex[-1][h], h))[0]
    assert o["top"] == best
    return o


def test_hand_worked():
    o = run(d(("h",)))
    # fair 1/4, biased 9/20 -> total 14/20: fair 5/14, biased 9/14
    assert o["posterior"] == {"biased": "9/14", "fair": "5/14"} and o["top"] == "biased"
    o = run(d(("h", "h", "t")))
    assert len(o["history"]) == 3
    # weights fair 1/16, biased 1/2*0.81*0.1 = 81/2000 -> 125/2000 vs 81/2000
    assert o["posterior"] == {"biased": "81/206", "fair": "125/206"} and o["top"] == "fair"
    assert o["status"] == "completed"
    assert o["claims"] == {"inputs_right": False, "independent_in_reality": False, "top_is_true": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d(("h", "h", "t")))


def test_ties_and_zero_prior():
    hy = {"b": H((1, 2), {"x": (1, 1)}), "a": H((1, 2), {"x": (1, 1)})}
    o = check(d(("x",), hy))
    assert o["top"] == "a" and o["posterior"] == {"a": "1/2", "b": "1/2"}
    hy = {"a": H((0, 1), {"x": (1, 2), "y": (1, 2)}), "b": H((1, 1), {"x": (1, 2), "y": (1, 2)})}
    o = check(d(("x", "y"), hy))
    assert o["posterior"] == {"a": "0", "b": "1"} and o["top"] == "b"
    hy = {"a": H((1, 2), {"x": (1, 1), "y": (0, 1)}), "b": H((1, 2), {"x": (0, 1), "y": (1, 1)})}
    assert check(d(("x",), hy))["posterior"] == {"a": "1", "b": "0"}
    bad(d(("x", "y"), hy), "evidence has probability zero under every hypothesis")


def test_random():
    rng = random.Random(881)
    for _ in range(300):
        nh, ns = rng.randint(2, 4), rng.randint(1, 3)
        syms = ["s", "t", "u"][:ns]

        def split(n, k, den):
            cuts = sorted(rng.randint(0, n) for _ in range(k - 1))
            parts = [b - a for a, b in zip([0] + cuts, cuts + [n])]
            return [(p, den) for p in parts]
        pri = split(20, nh, 20)
        hy = {}
        for i in range(nh):
            lk = split(10, ns, 10)
            hy[f"h{chr(97 + i)}"] = H(pri[i], dict(zip(syms, lk)))
        obs = [rng.choice(syms) for _ in range(rng.randint(1, 5))]
        try:
            check(d(obs, hy))
        except UpdateError as e:
            assert str(e) == "evidence has probability zero under every hypothesis"


def test_validation():
    ok = d()
    bad(d(hyps={"a": H((1, 1), {"h": (1, 1)})}), "hypotheses must be a dict of 2..6 hypotheses")
    seven = {f"h{chr(97 + i)}": H((0, 1), {"h": (1, 1)}) for i in range(7)}
    bad(d(hyps=seven), "hypotheses must be a dict of 2..6 hypotheses")
    six = {f"h{chr(97 + i)}": H((0, 1), {"h": (1, 1)}) for i in range(6)}
    six["ha"] = H((1, 1), {"h": (1, 1)})
    run(d(hyps=six))
    bad(d(hyps={"a": H((1, 2), {"h": (1, 1)}), "b": H((1, 3), {"h": (1, 1)})}), "priors must sum to 1")
    bad(d(hyps={"a": H((1, 2), {"h": (1, 3)}), "b": H((1, 2), {"h": (1, 1)})}), "likelihoods must sum to 1")
    bad(d(hyps={"a": H((1, 2), {"h": (1, 1)}), "b": H((1, 2), {"t": (1, 1)})}), "every hypothesis must give likelihoods for the same symbols")
    bad(d(hyps={"a": H((1, 2), {"h": (1, 1)}), "b": H((1, 2), {"h": (1, 1), "t": (0, 1)})}), "every hypothesis must give likelihoods for the same symbols")
    bad(d(("zz",)), "observation must be a known symbol")
    bad(d((1,)), "observation must be a known symbol")
    bad(d(()), "observations must be a list of 1..10 symbols")
    bad(d(("h",) * 11), "observations must be a list of 1..10 symbols")
    run(d(("h",) * 10))
    bad(d(("h",) * 10**5), "observations must be a list of 1..10 symbols")
    sev = {chr(97 + i): (0, 1) for i in range(7)}
    sev["a"] = (1, 1)
    bad(d(hyps={"x": H((1, 2), sev), "y": H((1, 2), sev)}), "likelihood must be a dict of 1..6 symbols")
    bad(d(hyps={"x": H((1, 2), {}), "y": H((1, 2), {})}), "likelihood must be a dict of 1..6 symbols")
    run(d(("a",), hyps={"x": H((1, 2), {chr(97 + i): (1 if i == 0 else 0, 1) for i in range(6)}), "y": H((1, 2), {chr(97 + i): (1 if i == 0 else 0, 1) for i in range(6)})}))
    bad(d(hyps={"A": H((1, 2), {"h": (1, 1)}), "b": H((1, 2), {"h": (1, 1)})}), "hypothesis name must be 1..12 characters from a-z and _")
    bad(d(hyps={"a": H((1, 2), {"H": (1, 1)}), "b": H((1, 2), {"H": (1, 1)})}), "symbol must be 1..12 characters from a-z and _")
    for body in ({"prior": (1, 2)}, {"likelihood": {"h": (1, 1)}}, {"prior": (1, 2), "likelihood": {"h": (1, 1)}, "x": 1}):
        bad(d(hyps={"a": body, "b": H((1, 2), {"h": (1, 1)})}), "hypothesis keys must be exactly likelihood, prior")
    bad(d(hyps={"a": 1, "b": 1}), "hypothesis keys must be exactly likelihood, prior")


@pytest.mark.parametrize("p", [[1], [1, 2, 3], None, "ab", 1, {}])
def test_pair_shape(p):
    x = d()
    x["hypotheses"]["fair"]["prior"] = p
    bad(x, "prior must be a [num, den] pair")
    x = d()
    x["hypotheses"]["fair"]["likelihood"]["h"] = p
    bad(x, "likelihood must be a [num, den] pair")


@pytest.mark.parametrize("v", [True, False, 1.0, 0.5, None, "1", [1], {}])
def test_pair_ints(v):
    x = d()
    x["hypotheses"]["fair"]["prior"] = [v, 2]
    bad(x, "prior must be a [num, den] pair of ints")
    x = d()
    x["hypotheses"]["fair"]["prior"] = [1, v]
    bad(x, "prior must be a [num, den] pair of ints")


def test_pair_ranges():
    for pr in ([-1, 2], [3, 2], [1, 0], [0, 0], [0, -1], [1, 101], [1, -2], [101, 100]):
        x = d()
        x["hypotheses"]["fair"]["prior"] = pr
        bad(x, "prior out of range")
    for pr in ([-1, 2], [3, 2], [1, 0], [1, 101]):
        x = d()
        x["hypotheses"]["fair"]["likelihood"]["h"] = pr
        bad(x, "likelihood out of range")
    x = d()
    x["hypotheses"]["fair"]["prior"] = [50, 100]
    x["hypotheses"]["biased"]["prior"] = [50, 100]
    run(x)
    x["hypotheses"]["fair"]["prior"] = [0, 1]
    x["hypotheses"]["biased"]["prior"] = [1, 1]
    run(x)


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", [], ("a",)])
def test_noncontainers(v):
    x = d()
    x["hypotheses"] = v
    bad(x, "hypotheses must be a dict of 2..6 hypotheses")
    x = d()
    x["observations"] = v
    bad(x, "observations must be a list of 1..10 symbols")
    x = d()
    x["hypotheses"]["fair"]["likelihood"] = v
    bad(x, "likelihood must be a dict of 1..6 symbols")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("hypotheses", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("hypotheses", "observations"):
        x = d()
        del x[k]
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d(("h", "t"))
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    a["history"][0]["fair"] = "x"
    a["posterior"]["fair"] = "x"
    r = run(x)
    assert r["claims"]["real_world"] is False and r["history"][0]["fair"] != "x" and r["posterior"]["fair"] != "x"
    assert m.CLAIMS["real_world"] is False


class SubInt(int):
    pass


class Quirky(int):
    """int subclass with lying arithmetic: must be refused before any Fraction is built."""
    def __mul__(self, other):
        return 0

    def __truediv__(self, other):
        return 0


def test_int_subclasses_refused_in_every_slot():
    for v in (SubInt(1), Quirky(1)):
        for slot in (0, 1):
            x = d()
            x["hypotheses"]["fair"]["prior"] = [v, 2] if slot == 0 else [1, v]
            bad(x, "prior must be a [num, den] pair of ints")
            x = d()
            x["hypotheses"]["fair"]["likelihood"]["h"] = [v, 2] if slot == 0 else [1, v]
            bad(x, "likelihood must be a [num, den] pair of ints")


class _SubStr(str):
    pass


class _LyingStr(str):
    """str subclass that hashes like 1 and equals 1."""
    def __hash__(self):
        return 1

    def __eq__(self, o):
        return o == 1 or str.__eq__(self, o)


def _variants(x):
    """Yield every copy of x with one str leaf or one dict key replaced by bytes or a str subclass."""
    import copy as _c
    def walk(node, path):
        if type(node) is str:
            yield path, "leaf"
        elif isinstance(node, dict):
            for k in node:
                if type(k) is str:
                    yield path + (k,), "key"
                yield from walk(node[k], path + (k,))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, path + (i,))
    for path, kind in walk(x, ()):
        for mk in (lambda s: s.encode(), _SubStr, _LyingStr):
            if kind == "key" and mk is _SubStr:
                continue   # a plain str subclass hashes and compares like its key: indistinguishable as a dict key
            y = _c.deepcopy(x)
            t = y
            for k in path[:-1]:
                t = t[k]
            last = path[-1]
            if kind == "leaf":
                t[last] = mk(t[last])
            else:
                t2 = {}
                for k, v in t.items():
                    t2[mk(k) if k == last else k] = v
                if len(path) == 1:
                    y = t2
                else:
                    u = y
                    for k in path[:-2]:
                        u = u[k]
                    u[path[-2]] = t2
            yield y


def test_nonexact_str_refused_in_every_str_slot_and_key():
    base = d(("h", "t"))
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(UpdateError):
            run(y)
    assert n >= 4


class _EqOne(str):
    def __hash__(self):
        return 1

    def __eq__(self, o):
        return o == 1 or str.__eq__(self, o)


def test_explicit_nonstr_and_subclass_pins():
    NM = "hypothesis name must be 1..12 characters from a-z and _"
    SY = "symbol must be 1..12 characters from a-z and _"
    ok = {"a": H((1, 2), {"h": (1, 1)}), "b": H((1, 2), {"h": (1, 1)})}
    bad({"hypotheses": {b"a": ok["a"], "b": ok["b"]}, "observations": ["h"]}, NM)
    bad({"hypotheses": {"a": ok["a"], "b": ok["b"], 1: ok["b"]}, "observations": ["h"]}, NM)
    bad({"hypotheses": {"a": H((1, 2), {b"h": (1, 1)}), "b": H((1, 2), {b"h": (1, 1)})}, "observations": [b"h"]}, SY)
    s = _EqOne("h")
    bad({"hypotheses": {"a": H((1, 2), {s: (1, 1)}), "b": H((1, 2), {s: (1, 1)})}, "observations": [1]}, SY)
    bad({"hypotheses": {"a": H((1, 2), {"h": (1, 1)}), "b": H((1, 2), {"h": (1, 1)})}, "observations": [_EqOne("h")]},
        "observation must be a known symbol")
    bad({"hypotheses": {"a": H((1, 2), {"h": (1, 1)}), "b": H((1, 2), {"h": (1, 1)})}, "observations": [b"h"]},
        "observation must be a known symbol")

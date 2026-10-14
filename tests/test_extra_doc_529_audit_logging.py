import pytest
from sugarcode.extra_doc import audit_logging as al

C, V = al.chain, al.verify
EV = [(1, 100, "login"), (2, 100, "read"), (3, 250, "logout")]
D1 = "22f39ea53c5c5bc852abd8ab6b3a919b7fa703964d6b5a6d07e3445666eb6af7"
D2 = "087afe4850fd641f22473ff43426bf3173e6372bc73f953a576a5de188ba75a8"
D3 = "d6880186e78e1743efaebe9f8be3afa0020d35fde5b38748e2fe71ec3915d778"


def test_constants():
    assert al.GENESIS == "0" * 64
    assert (al.MAX_ENTRIES, al.MAX_ACTION, al.MAX_TS) == (1000, 60, 10**12)
    assert al.STATUS_NOTE.startswith("PARTIAL") and "no judgment of whether" in al.STATUS_NOTE


def test_hand_literals():
    r = C(EV)
    assert [e["digest"] for e in r["events"]] == [D1, D2, D3]       # digests computed by hand from the docstring spec
    assert r["head"] == D3
    rows = [(1, 100, "login", D1), (2, 100, "read", D2), (3, 250, "logout", D3)]
    assert V(rows) == {"ok": True, "checked": 3, "first_bad": None, "status_note": al.STATUS_NOTE}
    bad = [rows[0], (2, 100, "read", "f" * 64), rows[2]]             # tampered middle digest
    assert V(bad)["first_bad"] == 1 and V(bad)["ok"] is False
    bad = [rows[0], rows[1], (3, 250, "logout", "0" * 63 + "1")]     # tampered last digest
    assert V(bad)["first_bad"] == 2
    bad = [(1, 100, "login", D2), rows[1], rows[2]]                  # first row wrong: chain root broken
    assert V(bad)["first_bad"] == 0
    assert C([(1, 0, "x")])["events"][0]["ts"] == 0


def test_oracle_random():
    import hashlib
    import random
    rnd = random.Random(529)
    for _ in range(300):
        n = rnd.randint(1, 10)
        ts = 0
        evs = []
        for i in range(1, n + 1):
            ts += rnd.choice([0, 1, 7, 100, rnd.randint(0, 500)])
            evs.append((i, ts, rnd.choice(["a", "login user", "x" * 60, "read", "delete 3"])))
        r = C(evs)
        prev = "0" * 64
        rows = []
        for (seq, t, act), out in zip(evs, r["events"]):
            exp = hashlib.sha256("|".join([prev, str(seq), str(t), act]).encode()).hexdigest()
            assert out == {"seq": seq, "ts": t, "action": act, "digest": exp}
            rows.append((seq, t, act, exp))
            prev = exp
        assert r["head"] == prev
        v = V(rows)
        assert v["ok"] is True and v["first_bad"] is None and v["checked"] == n
        if n >= 2:
            k = rnd.randrange(n)
            tampered = rows[:]
            s, t, act, d = tampered[k]
            tampered[k] = (s, t, act, "0123456789abcdef" * 4 if d != "0123456789abcdef" * 4 else "f" * 64)
            v = V(tampered)
            assert v["ok"] is False and v["first_bad"] == k


def test_validation():
    for fn, label in ((C, "events"), (V, "rows")):
        for bad in ("abc", None, 5, {"a": 1}):
            with pytest.raises(ValueError, match=rf"{label}: list required"):
                fn(bad)
        with pytest.raises(ValueError, match=rf"{label}: 1 to 1000 entries required"):
            fn([])
        with pytest.raises(ValueError, match=rf"{label}: 1 to 1000 entries required"):
            fn([(1, 0, "a")] * 1001 if fn is C else [(1, 0, "a", "0" * 64)] * 1001)
    ok3 = [(1, 0, "a")]; ok4 = [(1, 0, "a", D1)]
    for bad in ("abc", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"events\[1\]: \(seq, ts, action\) required"):
            C([ok3[0], bad])
        with pytest.raises(ValueError, match=r"rows\[1\]: \(seq, ts, action, digest\) required"):
            V([ok4[0], bad])
    for bad, want in (((1, 0), "3"), ((1, 0, "a", "x"), "3"), ((), "3")):
        with pytest.raises(ValueError, match=r"events\[1\]: 3 entries required"):
            C([ok3[0], bad])
    for bad in ((1, 0, "a"), (1, 0, "a", "x", 1), ()):
        with pytest.raises(ValueError, match=r"rows\[1\]: 4 entries required"):
            V([ok4[0], bad])
    with pytest.raises(ValueError, match=r"events\[0\] seq: must be 1"):
        C([(2, 0, "a")])
    for bad in ((0, 0, "a"), (-1, 0, "a"), (1001, 0, "a")):
        with pytest.raises(ValueError, match=r"events\[0\] seq: must be within 1 to 1000"):
            C([bad])
    with pytest.raises(ValueError, match=r"events\[1\] seq: must be 2"):
        C([ok3[0], (3, 0, "b")])
    with pytest.raises(ValueError, match=r"events\[1\] ts: must not decrease"):
        C([ok3[0], (2, 0, "b")]) if False else C([(1, 5, "a"), (2, 4, "b")])
    with pytest.raises(ValueError, match=r"rows\[1\] ts: must not decrease"):
        V([(1, 5, "a", D1), (2, 4, "b", "0" * 64)])
    for i, nm, lo, hi, extra in ((0, "seq", 1, 1000, None), (1, "ts", 0, 10**12, None)):
        for bad in (True, 1.0, "1", None):
            row = [1, 0, "a"]; row[i] = bad
            with pytest.raises(ValueError, match=rf"events\[0\] {nm}: integer required"):
                C([tuple(row)])
        for bad in (lo - 1, hi + 1):
            row = [1, 0, "a"]; row[i] = bad
            with pytest.raises(ValueError, match=rf"events\[0\] {nm}:"):
                C([tuple(row)])
    for bad in ("", None, 3, ["a"], "x" * 61):
        with pytest.raises(ValueError, match=r"events\[1\] action: non-empty string up to 60 characters required"):
            C([ok3[0], (2, 0, bad)])
    assert C([ok3[0], (2, 0, "x" * 60)])["checked" if False else "events"][1]["action"] == "x" * 60
    for bad in ("0" * 63, "0" * 65, "G" * 64, "A" * 64, 5, None, ["0" * 64]):
        with pytest.raises(ValueError, match=r"rows\[1\] digest: 64 lowercase hex characters required"):
            V([ok4[0], (2, 0, "a", bad)])
    assert V([ok4[0], (2, 0, "a", "f" * 64)])["ok"] is False
    assert C([[1, 0, "a"]])["head"] == C([(1, 0, "a")])["head"]       # list rows accepted


def test_upper_bounds_green():
    assert C([(1, 10**12, "a")])["events"][0]["ts"] == 10**12          # ts at its cap
    n = 1000
    evs = [(i + 1, 10**12, "a") for i in range(n)]
    r = C(evs)
    assert len(r["events"]) == n and r["events"][-1]["seq"] == n      # 1000 entries, seq at its cap
    rows = [(e["seq"], e["ts"], e["action"], e["digest"]) for e in r["events"]]
    assert V(rows)["ok"] is True


def test_v2_lone_surrogate_refused_in_chain_and_verify():
    import hashlib
    for bad in ("\ud800", "\udfff", "a\udc00b", "ok\ud83d"):
        with pytest.raises(ValueError, match=r"^events\[0\] action: lone surrogate characters are not allowed$"):
            C([(1, 0, bad)])
        with pytest.raises(ValueError, match=r"^events\[1\] action: lone surrogate characters are not allowed$"):
            C([(1, 0, "fine"), (2, 0, bad)])
        with pytest.raises(ValueError, match=r"^rows\[0\] action: lone surrogate characters are not allowed$"):
            V([(1, 0, bad, "0" * 64)])
    for ok in ("\ud7ff", "\ue000", "\U0001f600", "caf\u00e9"):      # just outside the surrogate range, and astral
        want = hashlib.sha256(("0" * 64 + "|1|0|" + ok).encode("utf-8")).hexdigest()
        assert C([(1, 0, ok)])["events"][0]["digest"] == want
        assert V([(1, 0, ok, want)])["ok"] is True
    # length is checked before the surrogate rule, type before both
    with pytest.raises(ValueError, match=r"action: non-empty string up to 60 characters required$"):
        C([(1, 0, "\ud800" * 61)])
    with pytest.raises(ValueError, match=r"action: non-empty string up to 60 characters required$"):
        C([(1, 0, 5)])


def test_v2_verify_reports_only_digest_mismatch_as_first_bad():
    rows = [(1, 100, "login", D1), (2, 100, "read", "f" * 64), (3, 250, "logout", D3)]
    assert V(rows)["first_bad"] == 1                                     # tampered digest: reported by index
    # tampered row 1 followed by a malformed row: the whole call raises instead of reporting first_bad
    with pytest.raises(ValueError, match=r"^rows\[2\] seq: must be 3$"):
        V([rows[0], rows[1], (9, 250, "logout", D3)])
    with pytest.raises(ValueError, match=r"^rows\[2\] ts: must not decrease$"):
        V([rows[0], rows[1], (3, 50, "logout", D3)])
    with pytest.raises(ValueError, match=r"^rows\[2\] digest: 64 lowercase hex characters required$"):
        V([rows[0], rows[1], (3, 250, "logout", "XYZ")])
    assert "Only a digest mismatch is reported as first_bad" in " ".join(al.__doc__.split())
    assert "lone surrogate" in al.__doc__

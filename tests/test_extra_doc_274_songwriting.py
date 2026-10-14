import itertools
import random
import pytest
from sugarcode.extra_doc import songwriting as s

W = s.write_song


def B(word, stress, rhyme):
    return {"word": word, "stress": stress, "rhyme": rhyme}


BANK = [B("moon", "10", "oon"), B("tune", "10", "oon"), B("soon", "10", "oon"), B("light", "1", "ight"),
        B("night", "1", "ight"), B("sight", "1", "ight"), B("the", "0", "x"), B("a", "0", "y"),
        B("over", "10", "ver"), B("river", "10", "iv"), B("away", "01", "ay"), B("today", "01", "ay"),
        B("delight", "01", "ight"), B("tonight", "01", "ight"), B("and", "0", "z"), B("sing", "1", "ing"),
        B("ring", "1", "ing"), B("wing", "1", "ing"), B("bring", "1", "ing"), B("song", "1", "ong"),
        B("flower", "10", "ower"), B("power", "10", "ower"), B("glory", "100", "ory"), B("story", "100", "ory"),
        B("sadly", "100", "adly"), B("madly", "100", "adly")]


def check(sec, bank, pattern, scheme):
    info = {b["word"]: (b["stress"], b["rhyme"]) for b in bank}
    ends = {}
    for ln, L in zip(sec["lines"], scheme):
        ws = ln.split()
        assert "".join(info[w][0] for w in ws) == pattern
        assert all(x != y for x, y in zip(ws, ws[1:]))
        ends.setdefault(L, []).append(ws[-1])
    keyof = {}
    for L, e in ends.items():
        assert len({info[w][1] for w in e}) == 1 and len(set(e)) == len(e)
        keyof[L] = info[e[0]][1]
    assert len(set(keyof.values())) == len(keyof)


def test_constants():
    assert s.METERS == {"iambic4": "01010101", "trochaic4": "10101010", "anapestic3": "001001001", "dactylic2": "100100"}
    assert s.SECTIONS == {"verse": "ABAB", "chorus": "AABB", "bridge": "ABBA"}
    assert (s.MAX_BANK, s.MAX_WORD, s.MAX_SECTIONS, s.NODE_LIMIT, s.MAX_SEED) == (200, 20, 12, 100000, 2 ** 63 - 1)
    assert s.STATUS_NOTE.startswith("PARTIAL")


@pytest.mark.parametrize("meter", sorted(s.METERS))
@pytest.mark.parametrize("seed", [0, 1, 7])
def test_song_satisfies_all_constraints(meter, seed):
    r = W(["verse", "chorus", "verse", "chorus", "bridge", "chorus"], BANK, meter, seed)
    for sec in r["sections"]:
        check(sec, BANK, s.METERS[meter], s.SECTIONS[sec["section"]])
        assert len(sec["lines"]) == 4
    ch = [x["lines"] for x in r["sections"] if x["section"] == "chorus"]
    assert ch[0] == ch[1] == ch[2]
    assert r["text"] == "\n\n".join("\n".join(x["lines"]) for x in r["sections"])
    assert r["meter_pattern"] == s.METERS[meter] and r["seed"] == seed


def test_verses_get_their_own_search_order():
    r = W(["verse", "verse"], BANK, "iambic4", 0)
    assert r["sections"][0]["lines"] != r["sections"][1]["lines"]


def test_hand_literal_tiny():
    # words x(1) y(0) z(1) ... iambic "01010101" hand-built: only "u v" pairs: u=0, v=1 so each line is "u v u v u v u v" with
    # distinct neighbours; the line end word must be v. Two end words with the same key are needed for A and B groups.
    bank = [B("u", "0", "k1"), B("v", "1", "r"), B("w", "1", "r")]
    # AABB needs end words of 2 keys: only key r among line-ending words -> infeasible
    with pytest.raises(ValueError, match="no chorus satisfies"):
        W(["chorus"], bank, "iambic4", 0)
    bank = [B("u", "0", "k1"), B("v", "1", "r"), B("w", "1", "r"), B("p", "1", "q"), B("q", "1", "q")]
    r = W(["chorus"], bank, "iambic4", 0)
    for ln in r["sections"][0]["lines"]:
        ws = ln.split()
        assert len(ws) == 8 and ws[0::2] == ["u"] * 4 and all(x in "vwpq" for x in ws[1::2])
    ends = [ln.split()[-1] for ln in r["sections"][0]["lines"]]
    assert ends[0] != ends[1] and ends[2] != ends[3]
    assert {ends[0], ends[1]} == {"v", "w"} or {ends[0], ends[1]} == {"p", "q"}


def test_seeded_literal_sha256sum():
    # bank u(0) v(1) w(1) p(1) q(1); chorus tag "chorus", seed 0, line 0: highest-priority end word = lowest sha256 of "0:chorus:0:<w>"
    bank = [B("u", "0", "k1"), B("v", "1", "r"), B("w", "1", "r"), B("p", "1", "q"), B("q", "1", "q")]
    r = W(["chorus"], bank, "iambic4", 0)
    # hand trace with sha256sum: line 0 ranks q,v,w,p; line 1 v,p,q,w; line 2 v,w,p,q; line 3 p,w,q,v
    assert r["sections"][0]["lines"] == ["u q u q u q u q", "u v u v u v u p", "u v u v u v u v", "u p u p u p u w"]


def test_validation():
    ok = ["verse"]
    for bad, m in [([], "structure"), (["refrain"], r"structure\[0\]"), ("verse", "structure"), ([5], "structure"),
                   (["verse"] * 13, "structure")]:
        with pytest.raises(ValueError, match=m):
            W(bad, BANK)
    with pytest.raises(ValueError, match="meter"):
        W(ok, BANK, "free")
    with pytest.raises(ValueError, match="meter"):
        W(ok, BANK, 3)
    for sd in [True, -1, 2 ** 63, 1.0, "1"]:
        with pytest.raises(ValueError, match="seed"):
            W(ok, BANK, "iambic4", sd)
    assert W(ok, BANK, "iambic4", 2 ** 63 - 1)["seed"] == 2 ** 63 - 1
    assert W(["verse"] * 12, BANK)["structure"] == ["verse"] * 12
    with pytest.raises(ValueError, match="2..200"):
        W(ok, [B("a", "0", "x")])
    with pytest.raises(ValueError, match="2..200"):
        W(ok, "nope")
    many = [B("w" + chr(97 + i // 26) + chr(97 + i % 26), "1", "x") for i in range(201)]
    with pytest.raises(ValueError, match="2..200"):
        W(ok, many)
    for e, m in [(5, r"bank\[0\]: dict"), ({"word": 3, "stress": "1", "rhyme": "x"}, r"bank\[0\]: dict"),
                 (B("", "1", "x"), "1..20 letters"), (B("a" * 21, "1", "x"), "1..20 letters"),
                 (B("a1", "1", "x"), "1..20 letters"), (B("a", "", "x"), "stress"), (B("a", "12", "x"), "stress"),
                 (B("a", "01010", "x"), "stress"), (B("a", 1, "x"), "stress"), (B("a", "1", " "), "rhyme"),
                 (B("a", "1", 3), "rhyme")]:
        with pytest.raises(ValueError, match=m):
            W(ok, [e, B("b", "1", "y")])
    with pytest.raises(ValueError, match="duplicate word 'a'"):
        W(ok, [B("a", "1", "x"), B("A", "1", "y")])
    good = [B("a" * 20, "1", "x"), B("b", "1", "y")]
    assert s._bank(good)[0][0] == "a" * 20


def test_four_syllable_word_and_cap():
    bank = [B("abcd", "0101", "k"), B("efgh", "0101", "k"), B("zz", "0101", "m"), B("yy", "0101", "m")]
    r = W(["verse"], bank, "iambic4", 0)
    check(r["sections"][0], bank, "01010101", "ABAB")


def test_infeasible_raises():
    with pytest.raises(ValueError, match="no verse satisfies"):
        W(["verse"], [B("a", "10", "k"), B("b", "10", "k")], "iambic4", 0)   # stress never matches
    with pytest.raises(ValueError, match="no bridge satisfies"):
        W(["bridge"], [B("u", "0", "k"), B("v", "1", "k"), B("w", "1", "k")], "iambic4", 0)  # ABBA needs 2 keys


def _tilings(bank, pattern):
    res = []
    def go(rest, ws):
        if not rest:
            res.append(tuple(ws)); return
        for w, st, _ in bank:
            if rest.startswith(st) and not (ws and ws[-1] == w):
                go(rest[len(st):], ws + [w])
    go(pattern, [])
    return res


def brute_feasible(bank, pattern, scheme):
    info = {w: r for w, _, r in bank}
    ends = {}
    for t in _tilings(bank, pattern):
        ends.setdefault(t[-1], 0)
    ends = list(ends)
    letters = sorted(set(scheme))
    for combo in itertools.product(ends, repeat=len(scheme)):
        ok = True
        keys = {}
        for L, e in zip(scheme, combo):
            keys.setdefault(L, set()).add(info[e])
        if any(len(v) != 1 for v in keys.values()):
            continue
        if len({next(iter(v)) for v in keys.values()}) != len(keys):
            continue
        for L in letters:
            es = [e for e, l in zip(combo, scheme) if l == L]
            if len(set(es)) != len(es):
                ok = False
        if ok:
            return True
    return False


def test_random_tiny_banks_match_brute_force():
    rng = random.Random(274)
    names = ["aa", "bb", "cc", "dd", "ee", "ff", "gg", "hh"]
    hits = [0, 0]
    for _ in range(60):
        n = rng.randint(3, 8)
        bank = [B(names[i], rng.choice(["0", "1", "01"]), rng.choice("pq")) for i in range(n)]
        tup = [(b["word"], b["stress"], b["rhyme"]) for b in bank]
        for kind in ("verse", "chorus", "bridge"):
            want = brute_feasible(tup, "01010101", s.SECTIONS[kind])
            try:
                r = W([kind], bank, "iambic4", 1)
                got = True
                check(r["sections"][0], bank, "01010101", s.SECTIONS[kind])
            except ValueError as e:
                assert "no " + kind in str(e)
                got = False
            assert got == want
            hits[want] += 1
    assert hits[0] > 5 and hits[1] > 5


def test_search_limit(monkeypatch):
    monkeypatch.setattr(s, "NODE_LIMIT", 5)
    with pytest.raises(ValueError, match="search limit"):
        W(["verse"], BANK, "iambic4", 0)


UV = [B("u", "0", "k1"), B("v", "1", "r"), B("w", "1", "r"), B("p", "1", "q"), B("q", "1", "q")]


def test_verse_literals_hand_traced_with_sha256sum():
    # tags verse1 / verse2 (the 2nd verse has its own search order); ranks from sha256sum of "0:<tag>:<line>:<word>"
    r = W(["verse", "verse"], UV, "iambic4", 0)
    assert r["sections"][0]["lines"] == ["u q u q u q u q", "u w u w u w u w", "u v u v u v u p", "u q u q u q u v"]
    assert r["sections"][1]["lines"] == ["u q u q u q u q", "u v u v u v u v", "u v u v u v u p", "u w u w u w u w"]
    assert W(["verse"], UV) == W(["verse"], UV, "iambic4", 0)
    assert W(["verse"], UV)["meter"] == "iambic4"


def test_node_limit_boundary_hand_counted(monkeypatch):
    # verse1 above never backtracks: each line is one fill chain over rest lengths 7..0 = 8 nodes, 4 lines = 32
    monkeypatch.setattr(s, "NODE_LIMIT", 32)
    assert len(W(["verse"], UV, "iambic4", 0)["sections"][0]["lines"]) == 4
    monkeypatch.setattr(s, "NODE_LIMIT", 31)
    with pytest.raises(ValueError, match="search limit"):
        W(["verse"], UV, "iambic4", 0)


def test_bank_size_edges():
    with pytest.raises(ValueError, match="no verse satisfies"):
        W(["verse"], [B("u", "0", "k"), B("v", "1", "k")], "iambic4", 0)     # exactly 2 entries is accepted
    big = [B("w" + chr(97 + i // 26) + chr(97 + i % 26), "1", "x") for i in range(200)]
    with pytest.raises(ValueError, match="no verse satisfies"):
        W(["verse"], big, "iambic4", 0)                                         # exactly 200 entries is accepted

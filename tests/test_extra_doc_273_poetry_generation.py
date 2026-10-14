"""Row 273 poetry generation: oracle = independent validator + brute-force feasibility on tiny lexicons + hand literals."""
import itertools
import random
import pytest
from sugarcode.extra_doc import poetry_generation as p

G = p.generate_verse


def E(word, syl, rhyme=None):
    d = {"word": word, "syllables": syl}
    if rhyme:
        d["rhyme"] = rhyme
    return d


def valid(res, lex, form):
    """Independent validator of every constraint the module promises."""
    targets, scheme = p.FORMS[form]
    info = {e["word"]: (e["syllables"], e.get("rhyme", p.rhyme_key(e["word"]))) for e in lex}
    lines = [l.split(" ") for l in res["lines"]]
    assert len(lines) == len(targets)
    for ln, t in zip(lines, targets):
        assert sum(info[w][0] for w in ln) == t
        assert all(a != b for a, b in zip(ln, ln[1:]))
    by_letter = {}
    for ln, L in zip(lines, scheme):
        by_letter.setdefault(L, []).append(ln[-1])
    seen_keys = {}
    for L, ends in by_letter.items():
        assert len(set(ends)) == len(ends)
        ks = {info[w][1] for w in ends}
        assert len(ks) == 1
        k = ks.pop()
        assert k not in seen_keys
        seen_keys[k] = L
    assert res["syllables_per_line"] == list(targets) and res["target_syllables"] == list(targets)
    assert res["text"] == "\n".join(res["lines"]) and res["rhyme_groups"] == by_letter


def feasible_line(lexinfo, target, end, memo=None):
    """Brute force: exists a word sequence ending with `end`, summing to target, no consecutive repeats."""
    def rec(remaining, last):
        if remaining == 0:
            return True
        return any(s <= remaining and w != last and rec(remaining - s, w) for w, s in lexinfo)
    s_end = dict(lexinfo)[end]
    if s_end > target:
        return False
    if s_end == target:
        return True
    rest = target - s_end
    # sequence = body + [end]; body must not end in `end` and must sum to rest
    def body(remaining, last):
        if remaining == 0:
            return last != end
        return any(s <= remaining and w != last and body(remaining - s, w) for w, s in lexinfo)
    return body(rest, None)


def brute_feasible_haiku(lex):
    info = [(e["word"], e["syllables"]) for e in lex]
    keyof = {e["word"]: e["rhyme"] for e in lex}
    ends = [[w for w, _ in info if feasible_line(info, t, w)] for t in (5, 7, 5)]
    for a, b, c in itertools.product(*ends):
        if len({keyof[a], keyof[b], keyof[c]}) == 3:
            return True
    return False


def test_estimators_hand_literals():
    syl = {"night": 1, "love": 1, "above": 2, "tree": 1, "table": 2, "little": 2, "the": 1, "fire": 1, "beautiful": 3,
           "make": 1, "time": 1, "rhyme": 1, "me": 1, "river": 2, "a": 1}
    for w, n in syl.items():
        assert p.estimate_syllables(w) == n, w
    assert p.estimate_syllables("poetry") == 2          # known heuristic error: "oe" counts as one vowel group
    assert p.estimate_syllables("123") == 0 and p.estimate_syllables("") == 0
    assert (p.rhyme_key("night"), p.rhyme_key("light")) == ("ight", "ight")
    assert p.rhyme_key("love") == p.rhyme_key("above") == "ov"
    assert p.rhyme_key("tree") == p.rhyme_key("free") == "ee"
    assert p.rhyme_key("Moon!") == "oon" and p.rhyme_key("rhythm") == "ythm" and p.rhyme_key("") == ""
    assert p.rhyme_key("sky") == "y"


def test_form_specs():
    assert p.FORMS["haiku"] == ((5, 7, 5), "ABC") and p.FORMS["limerick"] == ((9, 9, 6, 6, 9), "AABBA")
    assert p.FORMS["quatrain"] == ((8, 8, 8, 8), "ABAB") and p.FORMS["couplet"] == ((10, 10), "AA")
    assert p.FORMS["sonnet"][0] == (10,) * 14 and p.FORMS["sonnet"][1] == "ABABCDCDEFEFGG"


LEX = [E("moon", 1, "oon"), E("soon", 1, "oon"), E("june", 1, "oon"), E("river", 2, "iver"), E("silver", 2, "iver"),
       E("night", 1, "ight"), E("light", 1, "ight"), E("sleeping", 2, "eep"), E("quietly", 3, "ly"),
       E("dream", 1, "eam"), E("cream", 1, "eam"), E("falls", 1, "alls"), E("calls", 1, "alls"), E("sea", 1, "ea"),
       E("above", 2, "ov"), E("love", 1, "ov"), E("while", 1, "ile"), E("smile", 1, "ile")]


@pytest.mark.parametrize("form", ["haiku", "couplet", "limerick", "quatrain", "sonnet"])
@pytest.mark.parametrize("seed", [0, 1, 7])
def test_every_form_satisfies_all_constraints(form, seed):
    r = G(form, LEX, seed)
    valid(r, LEX, form)
    assert r == G(form, LEX, seed) and r["form"] == form and r["seed"] == seed
    assert r["status_note"].startswith("PARTIAL:")


def test_seed_changes_output_and_default_seed_zero():
    outs = {G("quatrain", LEX, s)["text"] for s in range(12)}
    assert len(outs) > 3
    assert G("haiku", LEX) == G("haiku", LEX, 0)


def test_heuristic_fallback_when_no_syllables_given():
    words = ["moon", "soon", "river", "silver", "night", "light", "dream", "cream", "falls", "calls", "sea", "love"]
    r = G("couplet", words, 4)
    lex = [{"word": w, "syllables": p.estimate_syllables(w)} for w in words]
    valid(r, lex, "couplet")


def test_infeasible_cases_raise():
    with pytest.raises(ValueError, match="no verse satisfies"):
        G("couplet", [E("a", 5, "x"), E("b", 5, "y")], 0)        # AA ends need one shared key
    with pytest.raises(ValueError, match="no verse satisfies"):
        G("couplet", [E("a", 5, "x"), E("b", 6, "x")], 0)        # 10 = 5+5 would repeat a; 6 does not fit
    with pytest.raises(ValueError, match="no verse satisfies"):
        G("haiku", [E("aa", 1, "k"), E("bb", 1, "k")], 0)
    with pytest.raises(ValueError, match="no verse satisfies"):
        G("couplet", [E("aa", 3, "k"), E("bb", 3, "j")], 0)      # AA needs two end words with the same key
    with pytest.raises(ValueError, match="no verse satisfies"):
        G("haiku", [E("only", 6, "o"), E("two", 6, "t")], 0)     # no combination sums to 5


def test_hand_verified_tiny_couplet():
    # two words per key; line sums to 10 using only 5-syllable words: x x? consecutive repeat banned
    lex = [E("alpha", 5, "a"), E("gamma", 5, "a")]
    r = G("couplet", lex, 0)
    assert sorted(l for l in r["lines"]) == ["alpha gamma", "gamma alpha"]
    assert r["rhyme_groups"]["A"] == sorted(r["rhyme_groups"]["A"], key=lambda w: r["rhyme_groups"]["A"].index(w))
    assert set(r["rhyme_groups"]["A"]) == {"alpha", "gamma"} and r["rhyme_keys"] == {"A": "a"}
    valid(r, lex, "couplet")


def test_random_tiny_haiku_feasibility_matches_brute_force():
    rnd = random.Random(99)
    agree = 0
    for _ in range(80):
        n = rnd.randint(3, 6)
        lex = [E(f"w{chr(97 + i)}", rnd.randint(1, 3), rnd.choice(["r1", "r2", "r3"])) for i in range(n)]
        want = brute_feasible_haiku(lex)
        try:
            r = G("haiku", lex, rnd.randint(0, 50))
            got = True
            valid(r, lex, "haiku")
        except ValueError as e:
            assert "no verse satisfies" in str(e)
            got = False
        assert got == want
        agree += want
    assert 5 < agree < 75          # both outcomes occur, so the comparison is not vacuous


def test_no_consecutive_repeats_and_distinct_rhyme_words():
    lex = [E("a", 1, "k"), E("b", 1, "k"), E("c", 1, "j"), E("d", 1, "j"), E("e", 1, "m")]
    r = G("quatrain", lex, 5)
    valid(r, lex, "quatrain")
    for ln in r["lines"]:
        w = ln.split(" ")
        assert all(x != y for x, y in zip(w, w[1:]))


def test_validation():
    with pytest.raises(ValueError, match="form: one of"):
        G("ode", LEX); 
    with pytest.raises(ValueError, match="form: one of"):
        G(None, LEX)
    for bad in (True, 1.0, "1", None, -1, 2 ** 63):
        with pytest.raises(ValueError, match="seed: int in"):
            G("haiku", LEX, bad)
    G("haiku", LEX, 2 ** 63 - 1)
    for bad in ([], [E("a", 1)], "abc", None, [5, 6], [{"w": "a"}, {"word": "b"}], [E("a", 1), E("A ", 1)],
                [E("a1", 1), E("b", 1)], [E("", 1), E("b", 1)], [E("x" * 25, 1), E("b", 1)]):
        with pytest.raises(ValueError, match="lexicon"):
            G("haiku", bad)
    for syl in (0, 7, True, 1.5, "1", None):
        with pytest.raises(ValueError, match="syllables must be an int in"):
            G("haiku", [E("a", syl) if syl is not None else {"word": "a", "syllables": None}, E("b", 1)])
    for rh in ("", "  ", 5):
        with pytest.raises(ValueError, match="rhyme must be a non-empty string"):
            G("haiku", [{"word": "a", "rhyme": rh}, E("b", 1)])
    with pytest.raises(ValueError, match="lexicon: list of 2..400"):
        G("haiku", [E(f"w{'a' * (i % 5)}{chr(97 + i % 26)}{chr(97 + i // 26)}", 1) for i in range(401)])
    G("haiku", ["moon", "soon", "light", "night", "river"][:5])       # plain strings accepted
    G("haiku", [E("x" * 24, 1, "q"), E("It's", 1, "r"), E("moon", 5, "s"), E("light", 2, "z"), E("night", 1, "z")], 1)


def test_search_limit(monkeypatch):
    monkeypatch.setattr(p, "NODE_LIMIT", 5)
    with pytest.raises(ValueError, match="search limit"):
        G("sonnet", LEX, 0)


LEX16 = ["moon", "soon", "tune", "night", "light", "sight", "bright", "dream", "stream", "gleam",
         "over", "under", "river", "silver", "a", "the"]


def test_seeded_literal_hand_checked_with_sha256sum():
    # sha256sum of "3:0:<word>" ranks "the" first, "3:1:<word>" ranks "light" then "moon" first; hand-traced greedy fill
    r = G("haiku", LEX16, 3)
    assert r["lines"] == ["the stream the stream the", "light moon light moon light moon light",
                          "sight moon sight bright moon"]
    assert r["rhyme_keys"] == {"A": "th", "B": "ight", "C": "oon"}
    assert r["syllables_per_line"] == [5, 7, 5] and r["seed"] == 3


def test_more_estimator_pins():
    assert p.rhyme_key("be") == "e" and p.rhyme_key("the") == "th" and p.rhyme_key("cake") == "ak"
    assert p.estimate_syllables("the") == 1 and p.estimate_syllables("able") == 2
    assert p.estimate_syllables("cake") == 1 and p.estimate_syllables("me") == 1
    assert p.estimate_syllables("eke") == 1 and p.estimate_syllables("e") == 1 and p.estimate_syllables("ae") == 1 and p.estimate_syllables("ke") == 1
    assert p.estimate_syllables("tree") == 1 and p.estimate_syllables("bye") == 1


def test_constants_and_lexicon_caps():
    assert (p.MAX_LEXICON, p.MAX_WORD, p.NODE_LIMIT, p.MAX_SEED) == (400, 24, 200000, 2 ** 63 - 1)
    ok = [E("a" * 24, 1, "x"), E("b", 1, "x")]
    with pytest.raises(ValueError, match="1..24 letters"):
        G("couplet", [E("a" * 25, 1, "x"), E("b", 1, "x")], 0)
    with pytest.raises(ValueError, match="1..24 letters"):
        G("couplet", [E("", 1, "x"), E("b", 1, "x")], 0)
    with pytest.raises(ValueError, match="1..24 letters"):
        G("couplet", [E("a1", 1, "x"), E("b", 1, "x")], 0)
    with pytest.raises(ValueError, match="2..400"):
        G("couplet", [E("a", 1, "x")], 0)
    with pytest.raises(ValueError, match="2..400"):
        G("couplet", [E("w" + chr(97 + i // 26) + chr(97 + i % 26), 1, "x") for i in range(401)], 0)
    big = [E("w" + chr(97 + i // 26) + chr(97 + i % 26), 1, "x") for i in range(400)]
    assert G("couplet", big, 0)["form"] == "couplet"
    assert G("couplet", ok, 0)["form"] == "couplet"     # 24-letter word accepted
    assert G("couplet", ok, 2 ** 63 - 1)["seed"] == 2 ** 63 - 1
    with pytest.raises(ValueError, match="seed"):
        G("couplet", ok, 2 ** 63)
    with pytest.raises(ValueError, match="seed"):
        G("couplet", ok, -1)


def test_one_syllable_words_fill_ten_word_lines():
    r = G("couplet", [E("x", 1, "k"), E("y", 1, "k")], 0)
    assert all(len(l.split()) == 10 for l in r["lines"])
    assert all(l.split()[i] != l.split()[i + 1] for l in r["lines"] for i in range(9))
    assert sorted(g[-1] for g in [l.split() for l in r["lines"]]) == ["x", "y"]


def test_node_limit_boundary_hand_counted(monkeypatch):
    # couplet, words a(5) b(5) same key, seed 1. sha256 ranks: line 0 and line 1 both try a before b.
    # line 0: solve(end a)=1, fill(5)=1, fill([a],0) rejected (ends in end word)=1, fill([b],0)=1 -> 4 nodes
    # line 1: end a is a duplicate end (skipped uncounted), end b: solve=1, fill(5)=1, fill([a],0)=1 -> 3 nodes. Total 7.
    lex = [E("a", 5, "p"), E("b", 5, "p")]
    monkeypatch.setattr(p, "NODE_LIMIT", 7)
    assert G("couplet", lex, 1)["lines"] == ["b a", "a b"]
    monkeypatch.setattr(p, "NODE_LIMIT", 6)
    with pytest.raises(ValueError, match="search limit"):
        G("couplet", lex, 1)


def test_duplicate_spelling_has_exact_lexicon_refusal():
    entries = [
        {'word': 'echo', 'syllables': 5, 'rhyme': 'same'},
        {'word': 'echo', 'syllables': 5, 'rhyme': 'same'},
    ]
    with pytest.raises(ValueError) as error:
        p.generate_verse('couplet', entries)
    assert str(error.value) == "lexicon[1]: duplicate word 'echo'"

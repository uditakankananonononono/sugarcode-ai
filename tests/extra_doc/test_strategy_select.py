import re
import pytest
from sugarcode.extra_doc import strategy_select as ss

C = ss.choose
NC = ("an implementation of the pattern", "algorithm performance", "which strategy is best",
      "design quality", "runtime behaviour")
NM = "name of a-z, 0-9, _ (1 to 30, starting with a letter) required"
TAB = [("small", 10), ("mid", 100), ("big", 1000)]


class I(int):
    pass


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
    assert (ss.MAX_TABLE, ss.MAX_SIZES, ss.MAX_SIZE) == (16, 100, 10 ** 9) and ss.NOT_CLAIMED == NC


def test_hand_literals():
    r = C(TAB, [0, 10, 11, 100, 101, 1000, 1001])
    assert r["chosen"] == ["small", "small", "mid", "mid", "big", "big", None]
    assert r["counts"] == [2, 2, 2] and r["unmatched"] == 1
    assert C([("only", 0)], [0, 1])["chosen"] == ["only", None]
    assert C([("a", 5)], [5])["chosen"] == ["a"] and C([("a", 5)], [6])["chosen"] == [None]
    assert C([("a", 10 ** 9)], [10 ** 9])["chosen"] == ["a"]


def test_shape_and_untouched():
    t, s = list(TAB), [5]
    r = C(t, s)
    assert t == TAB and s == [5]
    assert r == {"chosen": ["small"], "counts": [1, 0, 0], "unmatched": 0,
                 "strategy_validated": False, "not_claimed": NC}


def test_independent_oracle():
    import random
    rnd = random.Random(664)
    for _ in range(150):
        cuts = sorted(rnd.sample(range(0, 60), rnd.randint(1, 6)))
        table = [(f"s{i}", c) for i, c in enumerate(cuts)]
        sizes = [rnd.randint(0, 65) for _ in range(rnd.randint(1, 20))]
        r = C(table, sizes)
        for s, got in zip(sizes, r["chosen"]):
            fits = [n for n, c in table if c >= s]
            assert got == (fits[0] if fits else None)       # lowest-threshold fit is the first in ascending order
        assert sum(r["counts"]) + r["unmatched"] == len(sizes)
        for k, (n, _) in enumerate(table):
            assert r["counts"][k] == r["chosen"].count(n)


def test_caps_accepted():
    table = [(f"s{i}", i) for i in range(16)]
    assert C(table, [15] * 100)["counts"][15] == 100
    assert C([("a" * 30, 0)], [0])["chosen"] == ["a" * 30]


BAD = [None, 5, "", "A", "1a", "_a", "a-b", "a\n", "\u00e9", "a\u00e9", "\uff41", "a" * 31, St("a"), b"a"]


@pytest.mark.parametrize("bad", BAD)
def test_name_refusals(bad):
    refuse(f"table[0] name: {NM}", [(bad, 1)], [0])
    refuse(f"table[1] name: {NM}", [("a", 1), (bad, 2)], [0])


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, I(1), -1, 10 ** 9 + 1])
def test_max_size_refusals(bad):
    refuse("table[0] max_size: whole number 0 to 1000000000 required", [("a", bad)], [0])
    refuse("table[1] max_size: whole number 0 to 1000000000 required", [("a", 1), ("b", bad)], [0])


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, I(1), -1, 10 ** 9 + 1])
def test_size_refusals(bad):
    refuse("sizes[0]: whole number 0 to 1000000000 required", TAB, [bad, 1])
    refuse("sizes[1]: whole number 0 to 1000000000 required", TAB, [1, bad])


@pytest.mark.parametrize("bad", [[], ("a",), ("a", 1, 2), Tu(("a", 1)), ["a", 1], None, "ab"])
def test_row_shape(bad):
    refuse("table[0]: (name, max_size) tuple required", [bad], [0])
    refuse("table[1]: (name, max_size) tuple required", [("a", 1), bad], [0])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([("a", 1)]), [], [("a", i) for i in range(17)]])
def test_table_shape(bad):
    refuse("table: list of 1 to 16 required", bad, [0])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([1]), [], [1] * 101])
def test_sizes_shape(bad):
    refuse("sizes: list of 1 to 100 required", TAB, bad)


def test_distinct_and_increasing():
    refuse("table: names must be distinct", [("a", 1), ("a", 2)], [0])
    refuse("table: max_size must be strictly increasing", [("a", 2), ("b", 2)], [0])
    refuse("table: max_size must be strictly increasing", [("a", 3), ("b", 2)], [0])
    refuse("table: max_size must be strictly increasing", [("a", 1), ("b", 5), ("c", 4)], [0])
    assert C([("a", 1), ("b", 2)], [0])["chosen"] == ["a"]


def test_check_order():
    refuse("table: list of 1 to 16 required", None, None)
    refuse("table: names must be distinct", [("a", 5), ("a", 1)], None)
    refuse("table: max_size must be strictly increasing", [("a", 5), ("b", 1)], None)
    refuse("sizes: list of 1 to 100 required", TAB, None)

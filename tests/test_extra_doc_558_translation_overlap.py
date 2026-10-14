import inspect
import random
from collections import Counter
from fractions import Fraction as F

import pytest
from sugarcode.extra_doc import translation_overlap as to

O = to.overlap


def test_constants_signature():
    assert (to.MAX_CHARS, to.MAX_WORDS) == (2000, 200)
    assert to.STATUS_NOTE.startswith("PARTIAL") and "no translation" in to.STATUS_NOTE
    assert list(inspect.signature(O).parameters) == ["reference", "candidate"]


def test_hand_literals():
    r = O("the cat is on the mat", "the the the the the the the")
    assert r["precision_1"] == F(2, 7)                      # "the" clipped to its 2 uses in the reference
    assert r["precision_2"] == F(0) and r["length_ratio"] == F(7, 6)
    assert r["status_note"] == to.STATUS_NOTE
    r = O("the cat sat on the mat", "the cat sat on the mat")
    assert (r["precision_1"], r["precision_2"], r["length_ratio"]) == (F(1), F(1), F(1))
    r = O("the cat sat on the mat", "a cat sat on a mat")
    assert (r["precision_1"], r["precision_2"]) == (F(4, 6), F(2, 5))        # bigrams cat sat, sat on hit; on a, a mat, a cat miss
    assert O("a b c d", "d c b a")["precision_1"] == F(1) and O("a b c d", "d c b a")["precision_2"] == F(0)
    r = O("a b c", "A")
    assert r["precision_1"] == F(1) and r["precision_2"] is None and r["length_ratio"] == F(1, 3)
    assert O("a b", "x y")["precision_1"] == F(0)
    assert O("Hello, world", "hello world")["precision_1"] == F(1, 2)       # punctuation stays on the word
    assert O("a a b", "a a a b")["precision_1"] == F(3, 4) and O("a a b", "a a a b")["precision_2"] == F(2, 3)
    assert O("a b a b", "a b a b a b")["precision_2"] == F(3, 5)             # ab x3 clipped to 2, ba x2 clipped to 1 -> 3/5


def test_oracle_counter():
    rnd = random.Random(558)
    for _ in range(400):
        ref = [rnd.choice("abcd") for _ in range(rnd.randint(1, 9))]
        cand = [rnd.choice("abcdA") for _ in range(rnd.randint(1, 9))]
        r = O(" ".join(ref), " ".join(cand))
        c = [x.lower() for x in cand]
        for n, key in ((1, "precision_1"), (2, "precision_2")):
            cg = Counter(zip(*[c[i:] for i in range(n)]))
            rg = Counter(zip(*[ref[i:] for i in range(n)]))
            tot = sum(cg.values())
            want = None if tot == 0 else F(sum((cg & rg).values()), tot)
            assert r[key] == want, (ref, cand, n)
        assert r["length_ratio"] == F(len(cand), len(ref))


def test_caps_both_sides():
    w = " ".join(["a"] * 200)
    assert O(w, w)["length_ratio"] == 1
    with pytest.raises(ValueError, match=r"^reference: at most 200 words$"):
        O(w + " a", "a")
    with pytest.raises(ValueError, match=r"^candidate: at most 200 words$"):
        O("a", w + " a")
    assert O("a" * 2000, "a")["precision_1"] == 0
    with pytest.raises(ValueError, match=r"^reference: at most 2000 characters$"):
        O("a" * 2001, "a")
    with pytest.raises(ValueError, match=r"^candidate: at most 2000 characters$"):
        O("a", "a" * 2001)
    with pytest.raises(ValueError, match=r"^reference: at least 1 word required$"):
        O(" \n", "a")
    with pytest.raises(ValueError, match=r"^candidate: at least 1 word required$"):
        O("a", "")
    with pytest.raises(ValueError, match=r"^candidate: at least 1 word required$"):
        O("a", "   ")


def test_type_refusals_and_order():
    for bad in (None, 5, b"a", ["a"], True):
        with pytest.raises(ValueError, match=r"^reference: string required$"):
            O(bad, "a")
        with pytest.raises(ValueError, match=r"^candidate: string required$"):
            O("a", bad)
    with pytest.raises(ValueError, match=r"^reference: string required$"):
        O(None, None)
    with pytest.raises(ValueError, match=r"^reference: at most 2000 characters$"):
        O("a" * 2001, None)
    with pytest.raises(ValueError, match=r"^reference: at least 1 word required$"):
        O("", None)
    with pytest.raises(ValueError, match=r"^candidate: at most 2000 characters$"):
        O("a", "a" * 2000 + " ")

import inspect
import random
from fractions import Fraction as F
from functools import lru_cache

import pytest
from sugarcode.extra_doc import word_error_rate as we

S = we.score


def test_constants_signature():
    assert (we.MAX_CHARS, we.MAX_WORDS) == (5000, 400)
    assert we.STATUS_NOTE.startswith("PARTIAL") and "no audio, no speech recognition" in we.STATUS_NOTE
    assert list(inspect.signature(S).parameters) == ["reference", "hypothesis"]


def test_hand_literals():
    r = S("the quick brown fox", "the quick brown fox")
    assert (r["distance"], r["reference_words"], r["hypothesis_words"], r["wer"]) == (0, 4, 4, F(0))
    assert r["status_note"] == we.STATUS_NOTE
    assert S("the quick brown fox", "the quack brown fox")["distance"] == 1            # substitution
    assert S("the quick brown fox", "the brown fox")["wer"] == F(1, 4)                 # deletion
    assert S("the quick brown fox", "the very quick brown fox")["wer"] == F(1, 4)      # insertion
    assert S("a b c", "")["wer"] == F(1) and S("a b c", "   ")["distance"] == 3         # all deleted
    assert S("a", "x y z")["wer"] == F(3) and S("a", "x y z")["distance"] == 3          # above 1
    assert S("a b", "b a")["distance"] == 2
    assert S("kitten", "sitting")["distance"] == 1
    assert S("Hello, World", "hello world")["distance"] == 1                           # punctuation counts, case does not
    assert S("HELLO  world\n", "hello\tWORLD")["distance"] == 0                        # whitespace varieties
    assert S("a b c d e f", "b c d e f g")["distance"] == 2


def edit(a, b):
    @lru_cache(None)
    def d(i, j):
        if i == 0:
            return j
        if j == 0:
            return i
        return min(d(i - 1, j) + 1, d(i, j - 1) + 1, d(i - 1, j - 1) + (a[i - 1] != b[j - 1]))
    return d(len(a), len(b))


def test_oracle_memoised_recursion():
    rnd = random.Random(556)
    for _ in range(400):
        ref = [rnd.choice("abcAB") for _ in range(rnd.randint(1, 8))]
        hyp = [rnd.choice("abcAB") for _ in range(rnd.randint(0, 9))]
        r = S(" ".join(ref), " ".join(hyp))
        want = edit(tuple(w.lower() for w in ref), tuple(w.lower() for w in hyp))
        assert r["distance"] == want and r["wer"] == F(want, len(ref))
        assert (r["reference_words"], r["hypothesis_words"]) == (len(ref), len(hyp))


def test_caps_both_sides():
    w400 = " ".join(["a"] * 400)
    assert S(w400, w400)["reference_words"] == 400 and S("a", w400)["distance"] == 399
    with pytest.raises(ValueError, match=r"^reference: at most 400 words$"):
        S(w400 + " a", "a")
    with pytest.raises(ValueError, match=r"^hypothesis: at most 400 words$"):
        S("a", w400 + " a")
    assert S("a" * 5000, "a")["distance"] == 1
    with pytest.raises(ValueError, match=r"^reference: at most 5000 characters$"):
        S("a" * 5001, "a")
    with pytest.raises(ValueError, match=r"^hypothesis: at most 5000 characters$"):
        S("a", "a" * 5001)
    with pytest.raises(ValueError, match=r"^reference: at least 1 word required$"):
        S("", "a")
    with pytest.raises(ValueError, match=r"^reference: at least 1 word required$"):
        S("  \n ", "a")
    assert S("a", "")["hypothesis_words"] == 0


def test_type_refusals_and_order():
    for bad in (None, 5, b"a", ["a"], True):
        with pytest.raises(ValueError, match=r"^reference: string required$"):
            S(bad, "a")
        with pytest.raises(ValueError, match=r"^hypothesis: string required$"):
            S("a", bad)
    with pytest.raises(ValueError, match=r"^reference: string required$"):
        S(None, None)                                   # reference checked first
    with pytest.raises(ValueError, match=r"^reference: at most 5000 characters$"):
        S("a" * 5001, None)
    with pytest.raises(ValueError, match=r"^reference: at least 1 word required$"):
        S("", None)
    with pytest.raises(ValueError, match=r"^hypothesis: at most 5000 characters$"):
        S("a", "a" * 5001 + " ")                        # char cap counts raw characters, before splitting

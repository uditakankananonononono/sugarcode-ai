import inspect
import random

import pytest
from sugarcode.extra_doc import speech_text as st

SP = st.spell


def w(n):
    return SP(n)["words"]


def parse(words):
    """Independent inverse: words back to an integer."""
    small = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
             "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
             "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
             "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
    sign = 1
    toks = words.replace("-", " ").split()
    if toks[0] == "minus":
        sign, toks = -1, toks[1:]
    total = cur = 0
    for t in toks:
        if t in small:
            cur += small[t]
        elif t == "hundred":
            cur *= 100
        else:
            total += cur * {"thousand": 10**3, "million": 10**6, "billion": 10**9}[t]
            cur = 0
    return sign * (total + cur)


def test_constants_signature():
    assert st.MAX_ABS == 10**9
    assert st.STATUS_NOTE.startswith("PARTIAL") and "no audio generation" in st.STATUS_NOTE
    assert list(inspect.signature(SP).parameters) == ["n"]


def test_hand_literals():
    cases = {0: "zero", 1: "one", 10: "ten", 13: "thirteen", 19: "nineteen", 20: "twenty", 21: "twenty-one",
             40: "forty", 99: "ninety-nine", 100: "one hundred", 101: "one hundred one", 110: "one hundred ten",
             115: "one hundred fifteen", 120: "one hundred twenty", 999: "nine hundred ninety-nine",
             1000: "one thousand", 1001: "one thousand one", 1100: "one thousand one hundred",
             12345: "twelve thousand three hundred forty-five", 100000: "one hundred thousand",
             1000000: "one million", 1000001: "one million one",
             2000300: "two million three hundred", 40000010: "forty million ten",
             999999999: "nine hundred ninety-nine million nine hundred ninety-nine thousand nine hundred ninety-nine",
             1000000000: "one billion", -1: "minus one", -1000000000: "minus one billion",
             -42: "minus forty-two", 90: "ninety", 70: "seventy", 80: "eighty", 60: "sixty", 50: "fifty", 30: "thirty"}
    for n, want in cases.items():
        assert w(n) == want, n
    assert SP(12345) == {"words": "twelve thousand three hundred forty-five", "word_count": 5,
                         "status_note": st.STATUS_NOTE}
    assert SP(-42)["word_count"] == 2 and SP(0)["word_count"] == 1 and SP(1000000000)["word_count"] == 2


def test_every_small_value_round_trips_and_scale_samples():
    for n in range(-2100, 2100):
        assert parse(w(n)) == n, n
        assert "  " not in w(n) and w(n) == w(n).strip()
    rnd = random.Random(557)
    for _ in range(3000):
        n = rnd.randint(-10**9, 10**9)
        assert parse(w(n)) == n, n
    for n in (10**9, -10**9, 10**9 - 1, 10**6, 10**6 - 1, 10**3, 10**3 - 1, 100, 99, 19, 20):
        assert parse(w(n)) == n


def test_word_count_matches_words():
    rnd = random.Random(5570)
    for _ in range(300):
        n = rnd.randint(-10**9, 10**9)
        r = SP(n)
        assert r["word_count"] == len(r["words"].split())


def test_caps_both_sides():
    assert w(10**9) == "one billion" and w(-10**9) == "minus one billion"
    with pytest.raises(ValueError, match=r"^n: must be within -1000000000 to 1000000000$"):
        SP(10**9 + 1)
    with pytest.raises(ValueError, match=r"^n: must be within -1000000000 to 1000000000$"):
        SP(-10**9 - 1)


def test_type_refusals_and_order():
    for bad in (True, False, 1.0, "1", None, [1], 10**30 + 0.5):
        with pytest.raises(ValueError, match=r"^n: integer required$"):
            SP(bad)


def test_word_count_literals():
    assert SP(999999999)["word_count"] == 11
    assert SP(21)["word_count"] == 1 and SP(100)["word_count"] == 2 and SP(-1)["word_count"] == 2

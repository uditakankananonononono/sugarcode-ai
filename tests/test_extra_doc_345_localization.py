from fractions import Fraction
import math
import random
import pytest
from sugarcode.extra_doc import localization as l

N = l.format_number
DT = l.format_date
NB = "\u202f"


def test_constants():
    assert (l.MAX_ABS, l.MAX_DECIMALS, l.NBSP_NARROW) == (10 ** 12, 6, "\u202f")
    assert sorted(l.LOCALES) == ["de-DE", "en-GB", "en-IN", "en-US", "fr-FR", "ja-JP"]
    assert l.STATUS_NOTE.startswith("PARTIAL") and "not a CLDR" in l.STATUS_NOTE


@pytest.mark.parametrize("loc,want", [("en-US", "1,234,567.89"), ("en-GB", "1,234,567.89"), ("de-DE", "1.234.567,89"),
                                      ("fr-FR", "1" + NB + "234" + NB + "567,89"), ("en-IN", "12,34,567.89"),
                                      ("ja-JP", "1,234,567.89")])
def test_number_hand_literals(loc, want):
    assert N(1234567.891, loc) == want


def test_default_locale_and_decimals():
    assert N(1234.5) == "1,234.50"
    assert N(1234.5, decimals=0) == "1,235"
    assert N(1234.5, "de-DE", 1) == "1.234,5"
    assert N(0.1234567, decimals=6) == "0.123457"
    assert N(1, decimals=6) == "1.000000"


def test_grouping_boundaries():
    assert [N(v, decimals=0) for v in (0, 9, 99, 999, 1000, 9999, 99999, 100000, 999999, 1000000)] == [
        "0", "9", "99", "999", "1,000", "9,999", "99,999", "100,000", "999,999", "1,000,000"]
    assert [N(v, "en-IN", 0) for v in (999, 1000, 99999, 100000, 9999999, 10000000, 123456789)] == [
        "999", "1,000", "99,999", "1,00,000", "99,99,999", "1,00,00,000", "12,34,56,789"]
    assert N(10 ** 12, decimals=0) == "1,000,000,000,000"
    assert N(10 ** 12, "en-IN", 0) == "10,00,00,00,00,000"


def test_rounding_half_up_exact_decimal():
    assert N(0.005) == "0.01" and N(0.015) == "0.02" and N(0.025) == "0.03" and N(2.675) == "2.68"
    assert N(1.005) == "1.01" and N(0.004) == "0.00" and N(0.995) == "1.00"
    assert N(-0.005) == "-0.01" and N(-2.675) == "-2.68" and N(2.5, decimals=0) == "3" and N(-2.5, decimals=0) == "-3"
    assert N(999999.995) == "1,000,000.00"


def test_negative_and_negative_zero():
    assert N(-1234.5, "de-DE", 1) == "-1.234,5"
    assert N(-0.001) == "0.00" and N(-0.0) == "0.00" and N(0) == "0.00"
    assert N(-1) == "-1.00"
    assert N(-10 ** 12, decimals=0) == "-1,000,000,000,000"


def test_number_against_independent_integer_oracle():
    rnd = random.Random(4)

    def oracle(v, dec, indian, sep, dp):
        fr = Fraction(repr(v)) if isinstance(v, float) else Fraction(v)
        s = fr * 10 ** dec
        sign = fr < 0
        n = abs(s)
        scaled = math.floor(n + Fraction(1, 2))
        text = str(scaled).rjust(dec + 1, "0")
        whole, frac = (text[:-dec], text[-dec:]) if dec else (text, "")
        out, cnt, size = "", 0, 3
        for ch in reversed(whole):
            if cnt == size:
                out, cnt = sep + out, 0
                if indian:
                    size = 2
            out, cnt = ch + out, cnt + 1
        res = out + (dp + frac if dec else "")
        return ("-" if sign and scaled != 0 else "") + res

    for _ in range(300):
        v = rnd.choice([rnd.randint(-10 ** 9, 10 ** 9), round(rnd.uniform(-1e7, 1e7), rnd.randint(0, 5)),
                        rnd.uniform(-5, 5)])
        dec = rnd.randint(0, 6)
        loc = rnd.choice(sorted(l.LOCALES))
        c = l.LOCALES[loc]
        assert N(v, loc, dec) == oracle(v, dec, c["indian"], c["grp"], c["dec"]), (v, dec, loc)


@pytest.mark.parametrize("loc,want", [("en-US", "3/5/2024"), ("en-GB", "05/03/2024"), ("de-DE", "05.03.2024"),
                                      ("fr-FR", "05/03/2024"), ("en-IN", "05/03/2024"), ("ja-JP", "2024/3/5")])
def test_date_hand_literals(loc, want):
    assert DT(2024, 3, 5, loc) == want


def test_date_two_digit_and_edges():
    assert DT(2024, 12, 31, "en-US") == "12/31/2024" and DT(2024, 12, 31, "de-DE") == "31.12.2024"
    assert DT(2024, 2, 29) == "2/29/2024" and DT(1, 1, 1, "ja-JP") == "1/1/1"
    assert DT(9999, 12, 31, "en-GB") == "31/12/9999"
    assert DT(2024, 10, 11, "en-US") == "10/11/2024" and DT(2024, 10, 11, "en-GB") == "11/10/2024"


@pytest.mark.parametrize("args", [(2023, 2, 29), (2024, 13, 1), (2024, 0, 1), (2024, 1, 0), (2024, 4, 31), (0, 1, 1),
                                  (10000, 1, 1), (2024, 1, 32), (-1, 1, 1)])
def test_invalid_dates(args):
    with pytest.raises(ValueError, match="date: not a valid calendar date"):
        DT(*args)


def test_date_type_errors():
    for bad in [(True, 1, 1), (2024.0, 1, 1), ("2024", 1, 1), (2024, None, 1), (2024, 1, 1.5), (2024, 1, True)]:
        with pytest.raises(ValueError, match="whole number required"):
            DT(*bad)
    with pytest.raises(ValueError, match="year: whole number required"):
        DT(2024.0, 1, 1)
    with pytest.raises(ValueError, match="month: whole number required"):
        DT(2024, "1", 1)
    with pytest.raises(ValueError, match="day: whole number required"):
        DT(2024, 1, None)


def test_unknown_locale_messages():
    for call in (lambda: N(1, "xx-XX"), lambda: N(1, None), lambda: N(1, 5), lambda: DT(2024, 1, 1, "en-us"),
                 lambda: DT(2024, 1, 1, "")):
        with pytest.raises(ValueError, match=r"locale: unknown, expected one of \['de-DE'"):
            call()


@pytest.mark.parametrize("args", [(True,), ("1",), (None,), (float("nan"),), (float("inf"),), (-float("inf"),),
                                  (10 ** 12 + 1,), (-10 ** 12 - 1,), (1e12 + 1e5,), (2e15,), (1, "en-US", -1),
                                  (1, "en-US", 7), (1, "en-US", True), (1, "en-US", 1.0), (1, "en-US", "2"), ([1],)])
def test_number_rejects(args):
    with pytest.raises(ValueError):
        N(*args)


def test_number_messages_and_edges():
    with pytest.raises(ValueError, match="value: number required"):
        N(True)
    with pytest.raises(ValueError, match="value: finite number required"):
        N(float("nan"))
    with pytest.raises(ValueError, match="value: must be within"):
        N(10 ** 12 + 1)
    with pytest.raises(ValueError, match="value: must be within"):
        N(1e15)
    with pytest.raises(ValueError, match="value: magnitude above 1e15"):
        N(1000000000000001)
    with pytest.raises(ValueError, match="value: magnitude above 1e15"):
        N(2e15)
    with pytest.raises(ValueError, match="decimals: whole number required"):
        N(1, decimals=1.5)
    with pytest.raises(ValueError, match=r"decimals: must be within \[0, 6\]"):
        N(1, decimals=7)
    with pytest.raises(ValueError, match=r"decimals: must be within \[0, 6\]"):
        N(1, decimals=-1)
    with pytest.raises(ValueError, match=r"value: must be within \[-1000000000000, 1000000000000\]"):
        N(-10 ** 12 - 1)
    assert N(1e12, decimals=0) == "1,000,000,000,000" and N(-1e12, decimals=0) == "-1,000,000,000,000"
    assert N(1e12, decimals=6) == "1,000,000,000,000.000000"

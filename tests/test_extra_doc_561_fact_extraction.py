import datetime
import inspect
import random
import re

import pytest
from sugarcode.extra_doc import fact_extraction as fx

X = fx.extract


def test_constants_signature():
    assert fx.MAX_TEXT == 3000
    assert fx.STATUS_NOTE.startswith("PARTIAL") and "fixed YYYY-MM-DD" in fx.STATUS_NOTE
    assert list(inspect.signature(X).parameters) == ["text"]


def test_hand_literals():
    r = X("Due 2024-02-29, not 2023-02-29. Growth was 12% and 5%, up from 100%.")
    assert r["dates"] == [(4, "2024-02-29", 2024, 2, 29)]
    assert r["percentages"] == [(43, 12), (51, 5), (63, 100)]
    assert r["status_note"] == fx.STATUS_NOTE
    assert X("2024-01-01")["dates"] == [(0, "2024-01-01", 2024, 1, 1)]               # start and end of text
    assert X("x2024-01-01y")["dates"] == [(1, "2024-01-01", 2024, 1, 1)]             # letters are fine neighbours
    assert X("12024-01-01")["dates"] == [] and X("2024-01-011")["dates"] == []       # digit neighbours refuse
    assert [d[1] for d in X("0001-01-01 9999-12-31")["dates"]] == ["0001-01-01", "9999-12-31"]
    assert X("0000-01-01")["dates"] == []                                           # year 0
    assert X("2024-00-10")["dates"] == [] and X("2024-13-10")["dates"] == []
    assert X("2024-12-10")["dates"] != [] and X("2024-01-00")["dates"] == []
    leap = {"2000-02-29": 1, "1900-02-29": 0, "2100-02-29": 0, "2024-02-29": 1, "2023-02-29": 0, "2024-02-30": 0}
    for s, ok in leap.items():
        assert len(X(s)["dates"]) == ok, s
    month_end = {"2023-01-31": 1, "2023-01-32": 0, "2023-04-30": 1, "2023-04-31": 0, "2023-02-28": 1}
    for s, ok in month_end.items():
        assert len(X(s)["dates"]) == ok, s
    assert X("2024-1-01 24-01-01 2024/01/01")["dates"] == []
    assert X("2024-01-01-02")["dates"] == [(0, "2024-01-01", 2024, 1, 1)]
    assert X("1% 22% 333% 4444% 55555%")["percentages"] == [(0, 1), (3, 22), (7, 333)]
    assert X("0%")["percentages"] == [(0, 0)] and X("007%")["percentages"] == [(0, 7)]
    assert X("5 %")["percentages"] == [] and X("%5")["percentages"] == [] and X("a5%")["percentages"] == [(1, 5)]
    assert X("nothing here") == {"dates": [], "percentages": [], "status_note": fx.STATUS_NOTE}
    assert X("2024-01-01%")["percentages"] == [(8, 1)]                               # "01%" at the tail is its own run
    assert X("\u0663%")["percentages"] == []                                         # non-ASCII digits ignored


def test_oracle_datetime_and_regex():
    rnd = random.Random(561)
    alphabet = "0123456789-%x 2024"
    for _ in range(600):
        s = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(1, 40)))
        want_d = []
        for m in re.finditer(r"(?<![0-9])([0-9]{4})-([0-9]{2})-([0-9]{2})(?![0-9])", s):
            y, mo, d = map(int, m.groups())
            try:
                datetime.date(y, mo, d)
            except ValueError:
                continue
            want_d.append((m.start(), m.group(0), y, mo, d))
        want_p = [(m.start(), int(m.group(1))) for m in re.finditer(r"(?<![0-9])([0-9]{1,3})%", s)]
        r = X(s)
        assert r["dates"] == want_d, s
        assert r["percentages"] == want_p, s


def test_caps_both_sides():
    assert X("a" * 2990 + "2024-01-01")["dates"][0][0] == 2990              # 3000 chars, date flush at the end
    with pytest.raises(ValueError, match=r"^text: 1 to 3000 characters required$"):
        X("a" * 3001)
    with pytest.raises(ValueError, match=r"^text: 1 to 3000 characters required$"):
        X("")
    assert X("5%" + "a" * 2998)["percentages"] == [(0, 5)]


def test_type_refusals():
    for bad in (None, 5, b"2024-01-01", ["a"], 1.5, True):
        with pytest.raises(ValueError, match=r"^text: string required$"):
            X(bad)
    for ch in "/:\u00a0":
        assert X(f"2024{ch}01-01")["dates"] == []


def test_every_month_last_day_both_sides():
    plain = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]        # written out by hand
    for year, extra in ((2023, 0), (2024, 1), (1900, 0), (2000, 1)):
        for month, last in enumerate(plain, 1):
            last += extra if month == 2 else 0
            assert len(X(f"{year}-{month:02d}-{last:02d}")["dates"]) == 1, (year, month, last)
            assert X(f"{year}-{month:02d}-{last + 1:02d}")["dates"] == [], (year, month, last)
            assert len(X(f"{year}-{month:02d}-01")["dates"]) == 1
            assert X(f"{year}-{month:02d}-00")["dates"] == []
    assert len(X("2024-12-31")["dates"]) == 1 and X("2024-13-01")["dates"] == []


def test_every_position_must_match_the_shape():
    good = "2024-05-17"
    assert len(X(good)["dates"]) == 1
    for p in range(10):
        for bad in ("x", "-", " ", "5" if p in (4, 7) else "-"):
            s = good[:p] + bad + good[p + 1:]
            assert X(s)["dates"] == [] or s == good, s
    assert X("2024-05-17")["dates"][0][2:] == (2024, 5, 17)
    assert X("9999-12-31")["dates"][0][2:] == (9999, 12, 31) and X("0001-12-31")["dates"][0][2:] == (1, 12, 31)

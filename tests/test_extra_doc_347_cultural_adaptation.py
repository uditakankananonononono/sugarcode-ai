from datetime import datetime
from decimal import Decimal as D
from fractions import Fraction as Fr
import pytest
from sugarcode.extra_doc import cultural_adaptation as c

M = c.adapt_measurement


def test_constants():
    assert c.UNITS == sorted(["C", "F", "cm", "ft", "g", "gal", "in", "kg", "km", "L", "lb", "m", "mi", "oz"])
    assert c.MAX_ABS == 10 ** 9 and c.STATUS_NOTE.startswith("PARTIAL")


@pytest.mark.parametrize("v,u,want,wu,rounded", [
    (60, "mi", Fr("96.56064"), "km", "96.56"), (1, "ft", Fr("0.3048"), "m", "0.30"), (1, "in", Fr("2.54"), "cm", "2.54"),
    (1, "lb", Fr("0.45359237"), "kg", "0.45"), (1, "oz", Fr("28.349523125"), "g", "28.35"),
    (1, "gal", Fr("3.785411784"), "L", "3.79"), (10, "mi", Fr("16.09344"), "km", "16.09"),
])
def test_imperial_to_metric_exact(v, u, want, wu, rounded):
    r = M(v, u, "metric")
    assert r["value"] == want and r["unit"] == wu and r["rounded"] == D(rounded) and r["status"] == c.STATUS_NOTE


@pytest.mark.parametrize("v,u,want,wu", [
    (1.609344, "km", 1, "mi"), (0.3048, "m", 1, "ft"), (25.4, "cm", 10, "in"), (0.45359237, "kg", 1, "lb"),
    (28.349523125, "g", 1, "oz"), (3.785411784, "L", 1, "gal"),
])
def test_metric_to_imperial_exact_inverse(v, u, want, wu):
    r = M(v, u, "imperial")
    assert r["value"] == want and r["unit"] == wu


def test_metric_to_imperial_hand_literals():
    r = M(1, "kg", "imperial")
    assert r["value"] == 1 / Fr("0.45359237") and r["rounded"] == D("2.20") and r["unit"] == "lb"
    assert M(5, "km", "imperial")["rounded"] == D("3.11")
    assert M(100, "cm", "imperial")["rounded"] == D("39.37")
    assert M(1, "L", "imperial")["rounded"] == D("0.26")
    assert M(1, "m", "imperial")["rounded"] == D("3.28")
    assert M(100, "g", "imperial")["rounded"] == D("3.53")


def test_temperature_exact():
    assert M(100, "F", "metric")["value"] == Fr(340, 9) and M(100, "F", "metric")["rounded"] == D("37.78")
    assert M(212, "F", "metric")["value"] == 100 and M(32, "F", "metric")["value"] == 0
    assert M(-40, "F", "metric")["value"] == -40 and M(-40, "F", "metric")["unit"] == "C"
    assert M(0, "C", "imperial")["value"] == 32 and M(100, "C", "imperial")["value"] == 212
    assert M(37, "C", "imperial")["value"] == Fr(493, 5) and M(37, "C", "imperial")["rounded"] == D("98.60")
    assert M(-40, "C", "imperial")["value"] == -40 and M(-40, "C", "imperial")["unit"] == "F"


def test_already_in_target_system_unchanged():
    for v, u, s in [(5, "km", "metric"), (3, "mi", "imperial"), (20, "C", "metric"), (70, "F", "imperial"),
                    (2, "kg", "metric"), (2, "lb", "imperial"), (7, "L", "metric"), (1, "gal", "imperial")]:
        r = M(v, u, s)
        assert r["value"] == v and r["unit"] == u and r["rounded"] == D(v).quantize(D("0.01"))


def test_rounding_half_up_and_negative_zero():
    assert M(0.005, "km", "metric")["rounded"] == D("0.01") and M(0.015, "km", "metric")["rounded"] == D("0.02")
    assert M(-0.005, "km", "metric")["rounded"] == D("-0.01") and M(0.004, "km", "metric")["rounded"] == D("0.00")
    r = M(-0.001, "km", "metric")["rounded"]
    assert str(r) == "0.00" and str(M(0, "km", "metric")["rounded"]) == "0.00"
    assert M(-0.0, "C", "metric")["value"] == 0
    assert M(0.1, "km", "metric")["value"] == Fr(1, 10)   # decimal repr, not the binary float
    assert M(2.675, "km", "metric")["rounded"] == D("2.68")
    assert M(-2.675, "km", "metric")["rounded"] == D("-2.68")


@pytest.mark.parametrize("args", [
    (True, "km", "metric"), ("1", "km", "metric"), (None, "km", "metric"), (float("nan"), "km", "metric"),
    (float("inf"), "km", "metric"), (10 ** 9 + 1, "km", "metric"), (-10 ** 9 - 1, "km", "metric"),
    (10 ** 12 + 1, "km", "metric"), (1, "KM", "metric"), (1, "mile", "metric"), (1, None, "metric"), (1, 5, "metric"),
    (1, "km", "Metric"), (1, "km", None), (1, "km", "si"), (1, "km", ""),
])
def test_measurement_rejects(args):
    with pytest.raises(ValueError):
        M(*args)


def test_measurement_messages_and_value_caps():
    assert M(10 ** 9, "km", "metric")["value"] == 10 ** 9 and M(-10 ** 9, "km", "metric")["value"] == -10 ** 9
    with pytest.raises(ValueError, match=r"value: must be within \[-1000000000, 1000000000\]"):
        M(10 ** 9 + 1, "km", "metric")
    with pytest.raises(ValueError, match="value: must be within"):
        M(10 ** 12, "km", "metric")
    with pytest.raises(ValueError, match="value: magnitude above 1e12"):
        M(10 ** 12 + 1, "km", "metric")
    with pytest.raises(ValueError, match="value: magnitude above 1e12"):
        M(-2e12, "km", "metric")
    with pytest.raises(ValueError, match="value: number required"):
        M(True, "km", "metric")
    with pytest.raises(ValueError, match="value: finite number required"):
        M(float("nan"), "km", "metric")
    with pytest.raises(ValueError, match="system: must be 'metric' or 'imperial'"):
        M(1, "km", "si")
    with pytest.raises(ValueError, match=r"unit: unknown, expected one of \['C', 'F'"):
        M(1, "furlong", "metric")


@pytest.mark.parametrize("src,want", [("3:30 PM", "15:30"), ("12:00 AM", "00:00"), ("12:30 PM", "12:30"),
                                      ("12:00 PM", "12:00"), ("1:05 am", "01:05"), ("11:59 PM", "23:59"),
                                      ("3:30PM", "15:30"), ("9:07 aM", "09:07"), ("12:59 AM", "00:59"),
                                      ("11:00 AM", "11:00"), ("01:00 PM", "13:00")])
def test_to_24h_hand(src, want):
    assert c.to_24h(src) == want


@pytest.mark.parametrize("src,want", [("15:30", "3:30 PM"), ("00:00", "12:00 AM"), ("12:00", "12:00 PM"),
                                      ("0:05", "12:05 AM"), ("23:59", "11:59 PM"), ("9:07", "9:07 AM"),
                                      ("11:59", "11:59 AM"), ("13:00", "1:00 PM"), ("1:00", "1:00 AM")])
def test_to_12h_hand(src, want):
    assert c.to_12h(src) == want


def test_all_minutes_against_stdlib_oracle():
    for h in range(24):
        for m in range(60):
            t = datetime(2000, 1, 1, h, m)
            s12 = t.strftime("%I:%M %p").lstrip("0")
            assert c.to_12h(f"{h:02d}:{m:02d}") == s12
            assert c.to_24h(s12) == f"{h:02d}:{m:02d}"


@pytest.mark.parametrize("bad", ["13:00 PM", "0:30 AM", "12:60 PM", "3:5 PM", "3:30", "", None, "3:30 XM", " 3:30 PM",
                                 "3:30 PM\n", "3:30  PM", "٣:30 PM", 330, "123:30 PM", "3:300 PM"])
def test_to_24h_rejects(bad):
    with pytest.raises(ValueError, match="time: "):
        c.to_24h(bad)


@pytest.mark.parametrize("bad", ["24:00", "12:60", "1:5", "abc", "", None, "12:00 PM", "15:30\n", " 15:30", "٣:30",
                                 "123:00", "1:300", 1530])
def test_to_12h_rejects(bad):
    with pytest.raises(ValueError, match="time: "):
        c.to_12h(bad)


def test_time_messages():
    with pytest.raises(ValueError, match=r"time: expected like '3:30 PM'"):
        c.to_24h("nope")
    with pytest.raises(ValueError, match=r"time: hour must be 1-12 and minute 0-59"):
        c.to_24h("13:00 PM")
    with pytest.raises(ValueError, match=r"time: hour must be 1-12 and minute 0-59"):
        c.to_24h("12:60 PM")
    with pytest.raises(ValueError, match=r"time: hour must be 1-12 and minute 0-59"):
        c.to_24h("0:10 AM")
    with pytest.raises(ValueError, match=r"time: expected like '15:30'"):
        c.to_12h("nope")
    with pytest.raises(ValueError, match=r"time: hour must be 0-23 and minute 0-59"):
        c.to_12h("24:00")
    with pytest.raises(ValueError, match=r"time: hour must be 0-23 and minute 0-59"):
        c.to_12h("12:60")
    assert c.to_24h("12:59 PM") == "12:59" and c.to_12h("23:00") == "11:00 PM" and c.to_12h("00:59") == "12:59 AM"

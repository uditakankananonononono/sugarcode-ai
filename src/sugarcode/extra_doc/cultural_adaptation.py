"""Row 347 cultural adaptation: conversion of measurements and clock times to a locale's convention.

Imperial/US units and metric units are converted with exact factors (Fractions); Fahrenheit and Celsius with the
exact affine formula. Times convert between 12-hour and 24-hour notation. Only unit and notation conversion:
no judgment of norms, taboos, imagery or whether content suits any culture."""
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
import math
import re

# imperial unit -> (metric unit, factor to metric)
_TO_METRIC = {
    "mi": ("km", Fraction("1.609344")),
    "ft": ("m", Fraction("0.3048")),
    "in": ("cm", Fraction("2.54")),
    "lb": ("kg", Fraction("0.45359237")),
    "oz": ("g", Fraction("28.349523125")),
    "gal": ("L", Fraction("3.785411784")),
}
_TO_IMPERIAL = {m: (i, 1 / f) for i, (m, f) in _TO_METRIC.items()}
UNITS = sorted(list(_TO_METRIC) + list(_TO_IMPERIAL) + ["F", "C"])
MAX_ABS = 10 ** 9
STATUS_NOTE = ("PARTIAL: exact unit and clock-notation conversion only; no judgment of cultural norms, "
               "taboos or imagery")


def _num(v, name):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name}: number required")
    if abs(v) > 1e12:
        raise ValueError(f"{name}: magnitude above 1e12")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if abs(v) > MAX_ABS:
        raise ValueError(f"{name}: must be within [-{MAX_ABS}, {MAX_ABS}]")
    return Fraction(repr(v)) if isinstance(v, float) else Fraction(v)


def adapt_measurement(value, unit, system):
    v = _num(value, "value")
    if system not in ("metric", "imperial"):
        raise ValueError("system: must be 'metric' or 'imperial'")
    if not isinstance(unit, str) or unit not in UNITS:
        raise ValueError(f"unit: unknown, expected one of {UNITS}")
    if unit == "F" or unit == "C":
        if system == "metric" and unit == "F":
            out, u = (v - 32) * Fraction(5, 9), "C"
        elif system == "imperial" and unit == "C":
            out, u = v * Fraction(9, 5) + 32, "F"
        else:
            out, u = v, unit
    elif system == "metric" and unit in _TO_METRIC:
        u, f = _TO_METRIC[unit]
        out = v * f
    elif system == "imperial" and unit in _TO_IMPERIAL:
        u, f = _TO_IMPERIAL[unit]
        out = v * f
    else:
        out, u = v, unit
    r = Decimal(out.numerator) / Decimal(out.denominator)
    rounded = r.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if rounded == 0:
        rounded = abs(rounded)
    return {"value": out, "unit": u, "rounded": rounded, "status": STATUS_NOTE}


_T12 = re.compile(r"([0-9]{1,2}):([0-9]{2}) ?([AaPp][Mm])")
_T24 = re.compile(r"([0-9]{1,2}):([0-9]{2})")


def to_24h(text):
    m = _T12.fullmatch(text) if isinstance(text, str) else None
    if not m:
        raise ValueError("time: expected like '3:30 PM'")
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if not 1 <= h <= 12 or mi > 59:
        raise ValueError("time: hour must be 1-12 and minute 0-59")
    h = h % 12 + (12 if ap == "pm" else 0)
    return f"{h:02d}:{mi:02d}"


def to_12h(text):
    m = _T24.fullmatch(text) if isinstance(text, str) else None
    if not m:
        raise ValueError("time: expected like '15:30'")
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        raise ValueError("time: hour must be 0-23 and minute 0-59")
    return f"{(h + 11) % 12 + 1}:{mi:02d} {'AM' if h < 12 else 'PM'}"

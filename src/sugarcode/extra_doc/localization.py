"""Row 345 localization (PARTIAL): locale-convention formatting of numbers and dates from a small fixed table.

Locales: en-US, en-GB, de-DE, fr-FR, en-IN, ja-JP. Numbers use exact Decimal with round-half-up; grouping is 3-3 or
the Indian 3-2 pattern. Dates follow the table's field order. The table is a coarse convention, not CLDR, and
covers no translation, wording, plural or culture-fit judgment."""
from decimal import Decimal, ROUND_HALF_UP
import datetime
import math

NBSP_NARROW = "\u202f"
LOCALES = {
    "en-US": {"dec": ".", "grp": ",", "indian": False, "date": "{m}/{d}/{y}"},
    "en-GB": {"dec": ".", "grp": ",", "indian": False, "date": "{dd}/{mm}/{y}"},
    "de-DE": {"dec": ",", "grp": ".", "indian": False, "date": "{dd}.{mm}.{y}"},
    "fr-FR": {"dec": ",", "grp": NBSP_NARROW, "indian": False, "date": "{dd}/{mm}/{y}"},
    "en-IN": {"dec": ".", "grp": ",", "indian": True, "date": "{dd}/{mm}/{y}"},
    "ja-JP": {"dec": ".", "grp": ",", "indian": False, "date": "{y}/{m}/{d}"},
}
MAX_ABS = 10 ** 12
MAX_DECIMALS = 6
STATUS_NOTE = ("PARTIAL: number and date formatting from a small fixed locale table; no translation, wording "
               "or cultural-fit judgment, and not a CLDR implementation")


def _locale(name):
    if not isinstance(name, str) or name not in LOCALES:
        raise ValueError(f"locale: unknown, expected one of {sorted(LOCALES)}")
    return LOCALES[name]


def _group(digits, indian, sep):
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    size = 2 if indian else 3
    parts = []
    while head:
        parts.append(head[-size:])
        head = head[:-size]
    return sep.join(reversed(parts)) + sep + tail


def format_number(value, locale="en-US", decimals=2):
    loc = _locale(locale)
    if isinstance(decimals, bool) or not isinstance(decimals, int):
        raise ValueError("decimals: whole number required")
    if not 0 <= decimals <= MAX_DECIMALS:
        raise ValueError(f"decimals: must be within [0, {MAX_DECIMALS}]")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("value: number required")
    if abs(value) > 1e15:
        raise ValueError("value: magnitude above 1e15")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("value: finite number required")
    if abs(value) > MAX_ABS:
        raise ValueError(f"value: must be within [-{MAX_ABS}, {MAX_ABS}]")
    d = Decimal(repr(value)) if isinstance(value, float) else Decimal(value)
    q = d.quantize(Decimal(10) ** -decimals, rounding=ROUND_HALF_UP)
    text = format(abs(q), "f")
    whole, _, frac = text.partition(".")
    out = _group(whole, loc["indian"], loc["grp"])
    if decimals:
        out += loc["dec"] + frac
    neg = q < 0
    return ("-" if neg else "") + out


def format_date(year, month, day, locale="en-US"):
    loc = _locale(locale)
    for n, v in (("year", year), ("month", month), ("day", day)):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"{n}: whole number required")
    try:
        datetime.date(year, month, day)
    except ValueError:
        raise ValueError("date: not a valid calendar date")
    return loc["date"].format(y=year, m=month, d=day, mm=f"{month:02d}", dd=f"{day:02d}")

"""Row 321 technical drawing: tolerance arithmetic for dimensioned features.

Decimal limits for nominal +/- tolerance, a worst-case and a root-sum-square stack-up over a chain of signed
dimensions, and hole/shaft fit classification. Inputs are limited to 20 decimal places so limits, worst-case sums
and fits are exact; the RSS uses a square root rounded to 50 significant digits. Not a drawing, not a standards check (no ISO or ASME conformance),
no manufacturing or safety claim."""
from decimal import Decimal, localcontext
import math

MAX_CHAIN = 50
MAX_DECIMAL_PLACES = 20
STATUS_NOTE = ("PARTIAL: nominal-and-tolerance arithmetic with worst-case and RSS stack-up and fit classification; "
               "no drawing standard conformance and no manufacturing or safety claim")
PREC = 50


def _places(d):
    sign, digits, exp = d.as_tuple()
    digits = list(digits)
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()
        exp += 1
    if digits == [0]:
        return 0
    return max(0, -exp)


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        raise ValueError(f"{name}: number required")
    if isinstance(v, str):
        try:
            d = Decimal(v)
        except Exception:
            raise ValueError(f"{name}: number required")
    else:
        d = Decimal(repr(v)) if isinstance(v, float) else Decimal(v)
    if not d.is_finite():
        raise ValueError(f"{name}: finite number required")
    if abs(d) > Decimal(10) ** 9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if _places(d) > MAX_DECIMAL_PLACES:
        raise ValueError(f"{name}: more than {MAX_DECIMAL_PLACES} decimal places")
    if not lo <= d <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return d


def limits(nominal, plus, minus=None):
    n = _num(nominal, "nominal", -1000000, 1000000)
    p = _num(plus, "plus", 0, 1000)
    m = p if minus is None else _num(minus, "minus", 0, 1000)
    with localcontext() as ctx:
        ctx.prec = PREC
        return {"nominal": n, "min": n - m, "max": n + p, "band": p + m}


def stack_up(chain):
    """chain: list of (nominal, plus, minus_or_None, sign) with sign +1 or -1."""
    if not isinstance(chain, (list, tuple)) or not 1 <= len(chain) <= MAX_CHAIN:
        raise ValueError(f"chain: 1 to {MAX_CHAIN} required")
    with localcontext() as ctx:
        ctx.prec = PREC
        nom = Decimal(0)
        mid = Decimal(0)
        wc = Decimal(0)
        sq = Decimal(0)
        for c in chain:
            if not isinstance(c, (list, tuple)) or len(c) != 4 or type(c[3]) is not int or c[3] not in (1, -1):
                raise ValueError("link: (nominal, plus, minus, sign) with sign 1 or -1 required")
            lim = limits(c[0], c[1], c[2])
            nom += c[3] * lim["nominal"]
            mid += c[3] * (lim["max"] + lim["min"]) / 2
            wc += lim["band"] / 2
            sq += (lim["band"] / 2) ** 2
        rss = sq.sqrt()
        return {"nominal": nom, "mid": mid, "worst_min": mid - wc, "worst_max": mid + wc, "rss_min": mid - rss,
                "rss_max": mid + rss, "status": STATUS_NOTE}


def fit(hole_nominal, hole_plus, hole_minus, shaft_nominal, shaft_plus, shaft_minus):
    h = limits(hole_nominal, hole_plus, hole_minus)
    s = limits(shaft_nominal, shaft_plus, shaft_minus)
    with localcontext() as ctx:
        ctx.prec = PREC
        lo, hi = h["min"] - s["max"], h["max"] - s["min"]
    kind = "clearance" if lo > 0 else "interference" if hi < 0 else "transition"
    return {"min_clearance": lo, "max_clearance": hi, "kind": kind, "status": STATUS_NOTE}

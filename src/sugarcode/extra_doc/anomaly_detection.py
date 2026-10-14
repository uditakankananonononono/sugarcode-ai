"""Row 552 anomaly detection: Tukey interquartile-range fences over a list of whole numbers.

values is a list of 4 to 500 whole numbers from -1e9 to 1e9. The quartiles use linear interpolation between the
sorted values (position (n - 1) * p for p = 1/4 and 3/4, the common "inclusive" definition), as exact Fractions.
iqr = q3 - q1. With k_tenths a whole number from 1 to 100 (k = k_tenths / 10, the usual choice being 15 for 1.5),
the fences are lower = q1 - k * iqr and upper = q3 + k * iqr, and a value is an outlier when it is strictly below
lower or strictly above upper. detect returns the quartiles, fences and the outliers with their original index and
side. An outlier is a value far from the middle of this list; it is not a finding that the value is wrong."""
from fractions import Fraction

MAX_VALUES = 500
MAX_ABS = 10**9
MAX_K_TENTHS = 100
STATUS_NOTE = ("PARTIAL: interquartile-range fences over the supplied list only; an outlier is unusual in this "
               "list, not proof of an error or a cause")


def _quantile(sorted_vals, num, den):
    pos = Fraction((len(sorted_vals) - 1) * num, den)
    lo = pos.numerator // pos.denominator
    frac = pos - lo
    return sorted_vals[lo] + frac * (sorted_vals[lo + 1] - sorted_vals[lo])


def detect(values, k_tenths=15):
    if type(k_tenths) is not int:
        raise ValueError("k_tenths: integer required")
    if not 1 <= k_tenths <= MAX_K_TENTHS:
        raise ValueError(f"k_tenths: must be within 1 to {MAX_K_TENTHS}")
    if type(values) not in (list, tuple):
        raise ValueError("values: list required")
    if not 4 <= len(values) <= MAX_VALUES:
        raise ValueError(f"values: 4 to {MAX_VALUES} entries required")
    for i, v in enumerate(values):
        if type(v) is not int:
            raise ValueError(f"values[{i}]: integer required")
        if not -MAX_ABS <= v <= MAX_ABS:
            raise ValueError(f"values[{i}]: must be within -{MAX_ABS} to {MAX_ABS}")
    ordered = sorted(values)
    q1 = _quantile(ordered, 1, 4)
    q3 = _quantile(ordered, 3, 4)
    iqr = q3 - q1
    k = Fraction(k_tenths, 10)
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    outliers = []
    for i, v in enumerate(values):
        if v < lower:
            outliers.append({"index": i, "value": v, "side": "low"})
        elif v > upper:
            outliers.append({"index": i, "value": v, "side": "high"})
    return {"q1": q1, "q3": q3, "iqr": iqr, "lower": lower, "upper": upper, "outliers": outliers,
            "status_note": STATUS_NOTE}

"""Row 496 compensation design (PARTIAL): salary-grade structure arithmetic.

pay_grades(first_midpoint, grade_count, progression_bps, spread_bps, salaries=()) builds grade 1 to grade_count.
Grade 1 midpoint is first_midpoint (whole number 1 to 1e9); each later midpoint is the previous one times
(1 + progression_bps / 10000). With spread s = spread_bps / 10000, a grade's minimum is 2 * midpoint / (2 + s)
and its maximum is minimum * (1 + s), so the midpoint is exactly halfway between them and (max - min) / min is s.
overlap is the share of grade g's range that grade g + 1's range starts inside: max(0, (max_g - min_g+1) /
(max_g - min_g)), None for the last grade. Each salary is a (grade, amount) pair; its compa_ratio is amount /
midpoint, its range_position is (amount - min) / (max - min) and its zone is below_min, within or above_max.
All values are exact Fractions. What pay level is right for a job is not judged here."""
from fractions import Fraction

MAX_MIDPOINT = 1_000_000_000
MAX_GRADES = 30
MAX_PROGRESSION_BPS = 10_000
MAX_SPREAD_BPS = 20_000
MAX_SALARIES = 200
MAX_AMOUNT = 10_000_000_000
STATUS_NOTE = ("PARTIAL: structure arithmetic from supplied midpoint, progression and spread only; no judgment "
               "of what pay is right")


def _int(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: integer required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within {lo} to {hi}")
    return v


def pay_grades(first_midpoint, grade_count, progression_bps, spread_bps, salaries=()):
    mid0 = _int(first_midpoint, "first_midpoint", 1, MAX_MIDPOINT)
    n = _int(grade_count, "grade_count", 1, MAX_GRADES)
    p = Fraction(_int(progression_bps, "progression_bps", 0, MAX_PROGRESSION_BPS), 10_000)
    s = Fraction(_int(spread_bps, "spread_bps", 1, MAX_SPREAD_BPS), 10_000)
    if not isinstance(salaries, (list, tuple)):
        raise ValueError("salaries: list required")
    if len(salaries) > MAX_SALARIES:
        raise ValueError(f"salaries: at most {MAX_SALARIES} entries allowed")
    checked = []
    for i, e in enumerate(salaries):
        if not isinstance(e, (list, tuple)):
            raise ValueError(f"salaries[{i}]: (grade, amount) required")
        if len(e) != 2:
            raise ValueError(f"salaries[{i}]: 2 entries required")
        g = _int(e[0], f"salaries[{i}] grade", 1, n)
        a = _int(e[1], f"salaries[{i}] amount", 0, MAX_AMOUNT)
        checked.append((g, a))
    grades = []
    mid = Fraction(mid0)
    for g in range(1, n + 1):
        lo = 2 * mid / (2 + s)
        grades.append({"grade": g, "min": lo, "mid": mid, "max": lo * (1 + s)})
        mid = mid * (1 + p)
    for k, row in enumerate(grades):
        if k + 1 < n:
            nxt = grades[k + 1]
            row["overlap"] = max(Fraction(0), (row["max"] - nxt["min"]) / (row["max"] - row["min"]))
        else:
            row["overlap"] = None
    placed = []
    for g, a in checked:
        row = grades[g - 1]
        zone = "below_min" if a < row["min"] else "above_max" if a > row["max"] else "within"
        placed.append({"grade": g, "amount": a, "compa_ratio": Fraction(a) / row["mid"],
                       "range_position": (a - row["min"]) / (row["max"] - row["min"]), "zone": zone})
    return {"grades": grades, "salaries": placed, "status_note": STATUS_NOTE}

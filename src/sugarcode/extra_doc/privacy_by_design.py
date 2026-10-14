"""Row 531 privacy by design (PARTIAL): data-field minimisation and retention bookkeeping.

Each field is (name, needed, sensitivity, collected_day, retention_days): a non-empty name up to 60 characters,
a real bool saying whether the product still needs it, a whole-number sensitivity from 0 (public) to 3
(restricted), the whole day it was collected from 0 to 1,000,000 (not after today) and the whole number of days
it may be kept from 1 to 36,500. age_days is today - collected_day; retention state is overdue when age is above
retention_days, due on the exact day and within before it. The report lists unneeded fields (worst sensitivity
first, ties in input order) and overdue fields, with the exact share of fields still needed and the total
sensitivity carried by unneeded fields. Whether collecting or keeping any field is lawful or right is not
judged here."""

MAX_FIELDS = 200
MAX_NAME = 60
MAX_SENSITIVITY = 3
MAX_DAY = 1_000_000
MAX_RETENTION = 36_500
RETENTION_STATES = ("within", "due", "overdue")
STATUS_NOTE = ("PARTIAL: minimisation and retention arithmetic over supplied fields only; no judgment of "
               "lawfulness or of what should be collected")


def _int(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: integer required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within {lo} to {hi}")
    return v


def audit(fields, today):
    t = _int(today, "today", 0, MAX_DAY)
    if not isinstance(fields, (list, tuple)):
        raise ValueError("fields: list required")
    if not 1 <= len(fields) <= MAX_FIELDS:
        raise ValueError(f"fields: 1 to {MAX_FIELDS} entries required")
    rows, seen = [], set()
    for i, f in enumerate(fields):
        if not isinstance(f, (list, tuple)):
            raise ValueError(f"fields[{i}]: (name, needed, sensitivity, collected_day, retention_days) required")
        if len(f) != 5:
            raise ValueError(f"fields[{i}]: 5 entries required")
        name, needed, sens, collected, retention = f
        if not isinstance(name, str) or not name.strip() or len(name) > MAX_NAME:
            raise ValueError(f"fields[{i}] name: non-empty string up to {MAX_NAME} characters required")
        if name in seen:
            raise ValueError(f"fields[{i}]: duplicate field {name}")
        seen.add(name)
        if not isinstance(needed, bool):
            raise ValueError(f"fields[{i}] needed: bool required")
        s = _int(sens, f"fields[{i}] sensitivity", 0, MAX_SENSITIVITY)
        c = _int(collected, f"fields[{i}] collected_day", 0, MAX_DAY)
        if c > t:
            raise ValueError(f"fields[{i}] collected_day: must not be after today")
        r = _int(retention, f"fields[{i}] retention_days", 1, MAX_RETENTION)
        age = t - c
        state = "overdue" if age > r else "due" if age == r else "within"
        rows.append({"name": name, "needed": needed, "sensitivity": s, "age_days": age,
                     "days_over": max(0, age - r), "retention": state})
    from fractions import Fraction
    unneeded = [(x["sensitivity"], i, x["name"]) for i, x in enumerate(rows) if not x["needed"]]
    unneeded.sort(key=lambda x: (-x[0], x[1]))
    overdue = [x["name"] for x in rows if x["retention"] == "overdue"]
    return {"fields": rows, "unneeded": [n for _, _, n in unneeded], "overdue": overdue,
            "needed_share": Fraction(sum(1 for x in rows if x["needed"]), len(rows)),
            "unneeded_sensitivity": sum(x["sensitivity"] for x in rows if not x["needed"]),
            "status_note": STATUS_NOTE}

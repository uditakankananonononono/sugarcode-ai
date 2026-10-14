"""Row 665 Factory Pattern (PARTIAL): numbered product identifiers produced by a creation plan.

plan is a list of 1..16 (kind, count) tuples. kind is 1..30 characters of a-z, 0-9 and underscore starting with
a letter (ASCII only), distinct across the plan; count is a whole number 0..1000; the counts add up to at most
2000. Each kind yields count identifiers "kind-0001", "kind-0002" and so on (numbered from 1, padded to four
digits), listed plan entry by plan entry. These ranges are this module's own choices. It only builds strings.
It creates no objects, runs no constructors and says nothing about whether a factory is a good design."""
import re

MAX_KINDS, MAX_COUNT, MAX_TOTAL = 16, 1000, 2000
NOT_CLAIMED = ("an implementation of the pattern", "object creation", "design quality",
               "runtime behaviour", "uniqueness across processes")
_NAME = re.compile(r"[a-z][a-z0-9_]{0,29}")


def produce(plan):
    if type(plan) is not list or not 1 <= len(plan) <= MAX_KINDS:
        raise ValueError(f"plan: list of 1 to {MAX_KINDS} required")
    for i, row in enumerate(plan):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f"plan[{i}]: (kind, count) tuple required")
        if type(row[0]) is not str or _NAME.fullmatch(row[0]) is None:
            raise ValueError(f"plan[{i}] kind: name of a-z, 0-9, _ (1 to 30, starting with a letter) required")
        if type(row[1]) is not int or not 0 <= row[1] <= MAX_COUNT:
            raise ValueError(f"plan[{i}] count: whole number 0 to {MAX_COUNT} required")
    if len({r[0] for r in plan}) != len(plan):
        raise ValueError("plan: kinds must be distinct")
    total = sum(r[1] for r in plan)
    if total > MAX_TOTAL:
        raise ValueError(f"plan: counts must add up to at most {MAX_TOTAL}")
    ids = [f"{kind}-{n:04d}" for kind, count in plan for n in range(1, count + 1)]
    return {"identifiers": ids, "total": total,
            "factory_validated": False, "not_claimed": NOT_CLAIMED}

"""Row 611 continuous deployment: turning canary percentage steps into instance counts for a release.

instances is the whole number of running instances, 1 to 10000. steps is a list of 1 to 10 whole-number
percentages from 1 to 100 that strictly increase and end at 100. plan(instances, steps) gives, for each step, the
total updated instances after it, ceil(instances * percent / 100) (so any non-zero percent updates at least one
instance), and how many instances that step newly updates. Because of rounding up, two close steps on a small fleet
can land on the same total and update 0 new instances; those steps are flagged "empty". This is arithmetic on a
supplied plan; it does not deploy anything, watch health, or decide whether to roll back."""

MAX_INSTANCES = 10000
MAX_STEPS = 10
STATUS_NOTE = ("PARTIAL: instance-count arithmetic for a supplied rollout plan only; nothing is deployed, "
               "health is not watched and no rollback decision is made")


def _int(v, name, lo, hi):
    if type(v) is not int:
        raise ValueError(f"{name}: integer required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within {lo} to {hi}")
    return v


def plan(instances, steps):
    instances = _int(instances, "instances", 1, MAX_INSTANCES)
    if type(steps) not in (list, tuple):
        raise ValueError("steps: list required")
    if not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError(f"steps: 1 to {MAX_STEPS} entries required")
    pcts = []
    for i, p in enumerate(steps):
        p = _int(p, f"steps[{i}]", 1, 100)
        if pcts and p <= pcts[-1]:
            raise ValueError(f"steps[{i}]: must be greater than the previous step")
        pcts.append(p)
    if pcts[-1] != 100:
        raise ValueError("steps: last step must be 100")
    out = []
    before = 0
    for p in pcts:
        total = -(-instances * p // 100)
        out.append({"percent": p, "total": total, "new": total - before, "empty": total == before})
        before = total
    return {"steps": out, "status_note": STATUS_NOTE}

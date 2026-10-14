"""Row 494 balanced scorecard: attainment arithmetic across the four scorecard perspectives.

Each measure is (perspective, name, actual, target, higher_is_better) with perspective one of financial,
customer, internal_process or learning_growth, actual a whole number from 0 to 1e9, target a whole number from 1
to 1e9 and higher_is_better a real bool. Attainment is actual / target when higher is better and target / actual
when lower is better (a lower-is-better actual of 0 counts as the cap), never above 2 (200%). A perspective's
score is the exact mean attainment of its measures (None when it has none) and its status is green from 1,
amber from 4/5 and red below. The overall score is the weighted mean over the perspectives that have measures,
using four whole-number weights from 0 to 100 (None when those weights sum to 0). Which measures to choose,
and whether the targets are right, are not judged here."""
from fractions import Fraction

PERSPECTIVES = ("financial", "customer", "internal_process", "learning_growth")
MAX_MEASURES = 200
MAX_NAME = 60
MAX_VALUE = 1_000_000_000
MAX_WEIGHT = 100
CAP = Fraction(2)
STATUS_NOTE = ("PARTIAL: attainment arithmetic over supplied measures and targets only; no judgment of the "
               "measures or targets chosen")


def _int(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: integer required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within {lo} to {hi}")
    return v


def scorecard(measures, weights=(1, 1, 1, 1)):
    if not isinstance(weights, (list, tuple)):
        raise ValueError("weights: list required")
    if len(weights) != len(PERSPECTIVES):
        raise ValueError(f"weights: {len(PERSPECTIVES)} entries required")
    if not isinstance(measures, (list, tuple)):
        raise ValueError("measures: list required")
    if not 1 <= len(measures) <= MAX_MEASURES:
        raise ValueError(f"measures: 1 to {MAX_MEASURES} entries required")
    w = [_int(x, f"weights[{i}]", 0, MAX_WEIGHT) for i, x in enumerate(weights)]
    per = {p: [] for p in PERSPECTIVES}
    seen = set()
    out = []
    for i, m in enumerate(measures):
        if not isinstance(m, (list, tuple)):
            raise ValueError(f"measures[{i}]: (perspective, name, actual, target, higher_is_better) required")
        if len(m) != 5:
            raise ValueError(f"measures[{i}]: 5 entries required")
        p, name, actual, target, hib = m
        if not isinstance(p, str) or p not in per:
            raise ValueError(f"measures[{i}] perspective: one of {', '.join(PERSPECTIVES)} required")
        if not isinstance(name, str) or not name.strip() or len(name) > MAX_NAME:
            raise ValueError(f"measures[{i}] name: non-empty string up to {MAX_NAME} characters required")
        if (p, name) in seen:
            raise ValueError(f"measures[{i}]: duplicate measure {name} in {p}")
        seen.add((p, name))
        a = _int(actual, f"measures[{i}] actual", 0, MAX_VALUE)
        t = _int(target, f"measures[{i}] target", 1, MAX_VALUE)
        if not isinstance(hib, bool):
            raise ValueError(f"measures[{i}] higher_is_better: bool required")
        if hib:
            att = min(Fraction(a, t), CAP)
        else:
            att = CAP if a == 0 else min(Fraction(t, a), CAP)
        per[p].append(att)
        out.append({"perspective": p, "name": name, "attainment": att})
    scores, status = {}, {}
    for p in PERSPECTIVES:
        if per[p]:
            s = sum(per[p]) / len(per[p])
            scores[p] = s
            status[p] = "green" if s >= 1 else "amber" if s >= Fraction(4, 5) else "red"
        else:
            scores[p] = status[p] = None
    live = [(wt, scores[p]) for wt, p in zip(w, PERSPECTIVES) if scores[p] is not None]
    tw = sum(x for x, _ in live)
    overall = sum(x * s for x, s in live) / tw if tw else None
    return {"measures": out, "scores": scores, "status": status, "overall": overall, "status_note": STATUS_NOTE}

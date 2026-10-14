"""Row 280 visual storyboarding (PARTIAL): sequencing arithmetic over supplied panel shot sizes and durations.

Computes timecodes, shot-size transitions, jump cuts and repeated-shot runs only.
No drawing, framing quality, visual taste or cinematic-merit judgement is made."""
import math
from fractions import Fraction

SHOT_SCALE = {"extreme_wide": 1, "wide": 2, "medium": 3, "close": 4, "extreme_close": 5}
MAX_PANELS = 300
MAX_ID = 40
MAX_SECONDS = 600
DEFAULT_JUMP = 3
DEFAULT_RUN = 3
STATUS_NOTE = ("PARTIAL: sequencing arithmetic over supplied shot sizes and durations; "
               "no judgement of framing, drawing, taste or cinematic merit")


def _seconds(v, name):
    if isinstance(v, bool) or not isinstance(v, (int, float, Fraction)):
        raise ValueError(f"{name}: number required")
    if abs(v) > 1e9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not 0 < v <= MAX_SECONDS:
        raise ValueError(f"{name}: must be above 0 and at most {MAX_SECONDS}")
    return Fraction(v)


def _count(v, name):
    if isinstance(v, bool) or not isinstance(v, int) or not 2 <= v <= 5:
        raise ValueError(f"{name}: int in [2, 5] required")
    return v


def analyze_storyboard(panels, jump_threshold=DEFAULT_JUMP, run_threshold=DEFAULT_RUN):
    if not isinstance(panels, (list, tuple)) or not 1 <= len(panels) <= MAX_PANELS:
        raise ValueError(f"panels: list of 1..{MAX_PANELS} entries required")
    jt = _count(jump_threshold, "jump_threshold")
    rt = _count(run_threshold, "run_threshold")
    rows, seen, t = [], set(), Fraction(0)
    for i, p in enumerate(panels):
        if not isinstance(p, dict):
            raise ValueError(f"panels[{i}]: dict required")
        k = p.get("id")
        if not isinstance(k, str) or not 1 <= len(k) <= MAX_ID:
            raise ValueError(f"panels[{i}]: id must be a string of 1..{MAX_ID} characters")
        if k in seen:
            raise ValueError(f"panels[{i}]: duplicate id {k!r}")
        seen.add(k)
        shot = p.get("shot")
        if not isinstance(shot, str) or shot not in SHOT_SCALE:
            raise ValueError(f"panels[{i}]: shot must be one of {sorted(SHOT_SCALE, key=SHOT_SCALE.get)}")
        d = _seconds(p.get("seconds"), f"panels[{i}].seconds")
        rows.append({"id": k, "shot": shot, "scale": SHOT_SCALE[shot], "start": float(t), "end": float(t + d),
                     "seconds": float(d)})
        t += d
    jumps = []
    for a, b in zip(rows, rows[1:]):
        if abs(a["scale"] - b["scale"]) >= jt:
            jumps.append({"from": a["id"], "to": b["id"], "change": b["scale"] - a["scale"]})
    runs, i = [], 0
    while i < len(rows):
        j = i
        while j + 1 < len(rows) and rows[j + 1]["shot"] == rows[i]["shot"]:
            j += 1
        if j - i + 1 >= rt:
            runs.append({"shot": rows[i]["shot"], "start_id": rows[i]["id"], "length": j - i + 1})
        i = j + 1
    counts = {}
    for r in rows:
        counts[r["shot"]] = counts.get(r["shot"], 0) + 1
    return {"panels": rows, "total_seconds": float(t), "mean_seconds": float(t / len(rows)),
            "jump_cuts": jumps, "repeated_runs": runs, "shot_counts": counts,
            "status_note": STATUS_NOTE}

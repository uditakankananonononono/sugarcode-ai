"""Row 295 animation principles: squash-and-stretch and anticipation arithmetic over supplied keyframes.

Checks area preservation of scale pairs, counts squash and stretch frames and measures the opposite-direction lead-in.
No judgement of timing feel, appeal, weight or animation quality."""
import math
from fractions import Fraction

MAX_FRAMES = 500
MAX_ABS = 10 ** 6
SCALE_RANGE = (Fraction(1, 10), Fraction(10))
DEFAULT_TOLERANCE = Fraction(1, 50)
STATUS_NOTE = ("PARTIAL: area preservation of scale pairs, squash and stretch counts and opposite-direction lead-in "
               "duration from supplied keyframes; no judgement of timing feel, appeal or weight")


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float, Fraction)):
        raise ValueError(f"{name}: number required")
    if abs(v) > MAX_ABS:
        raise ValueError(f"{name}: magnitude above {MAX_ABS}")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return Fraction(v)


def analyze_keyframes(frames, tolerance=DEFAULT_TOLERANCE):
    tol = _num(tolerance, "tolerance", 0, 1)
    if not isinstance(frames, (list, tuple)) or not 3 <= len(frames) <= MAX_FRAMES:
        raise ValueError(f"frames: list of 3..{MAX_FRAMES} entries required")
    fs = []
    for i, f in enumerate(frames):
        if not isinstance(f, dict):
            raise ValueError(f"frames[{i}]: dict required")
        t = _num(f.get("t"), f"frames[{i}].t", 0, MAX_ABS)
        y = _num(f.get("y"), f"frames[{i}].y", -MAX_ABS, MAX_ABS)
        sx = _num(f.get("sx"), f"frames[{i}].sx", *SCALE_RANGE)
        sy = _num(f.get("sy"), f"frames[{i}].sy", *SCALE_RANGE)
        if fs and t <= fs[-1][0]:
            raise ValueError(f"frames[{i}].t: must be strictly increasing")
        fs.append((t, y, sx, sy))
    rows = []
    for t, y, sx, sy in fs:
        err = abs(sx * sy - 1)
        rows.append({"t": float(t), "area_error": float(err), "area_ok": err <= tol,
                     "pose": "stretch" if sy > 1 else "squash" if sy < 1 else "rest"})
    net = fs[-1][1] - fs[0][1]
    lead = None
    if net != 0:
        direction = 1 if net > 0 else -1
        first = fs[1][1] - fs[0][1]
        if first * direction < 0:
            # net motion has the opposite sign, so some later step moves with it
            k = next(i for i in range(2, len(fs)) if (fs[i][1] - fs[i - 1][1]) * direction > 0)
            span = fs[k - 1][0] - fs[0][0]
            lead = {"frames": k, "duration": float(span), "share_of_total": float(span / (fs[-1][0] - fs[0][0])),
                    "depth": float(max((fs[0][1] - y) * direction for _, y, _, _ in fs[:k]))}
    return {"frames": rows, "all_area_ok": all(r["area_ok"] for r in rows),
            "squash_frames": sum(r["pose"] == "squash" for r in rows),
            "stretch_frames": sum(r["pose"] == "stretch" for r in rows),
            "net_direction": "up" if net > 0 else "down" if net < 0 else "none",
            "anticipation": lead, "status_note": STATUS_NOTE}

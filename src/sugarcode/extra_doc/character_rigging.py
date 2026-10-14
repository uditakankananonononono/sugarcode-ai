"""Row 296 character rigging: 2D forward kinematics and rig validity checks for a supplied bone tree.

Validates the hierarchy, computes joint positions and reach, and checks optional joint angle limits.
No judgement of deformation quality, skinning, weight painting or animation suitability."""
import math

MAX_BONES = 64
MAX_ID = 40
MAX_LENGTH = 10000
MAX_ANGLE = 360
STATUS_NOTE = ("PARTIAL: 2D forward kinematics, hierarchy validation and angle-limit checks of a supplied bone tree; "
               "no judgement of deformation, skinning or animation suitability")


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name}: number required")
    if abs(v) > 1e9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return float(v)


def _r(x):
    return round(x, 9) + 0.0


def solve_rig(bones):
    if not isinstance(bones, (list, tuple)) or not 1 <= len(bones) <= MAX_BONES:
        raise ValueError(f"bones: list of 1..{MAX_BONES} entries required")
    info, order = {}, []
    for i, b in enumerate(bones):
        if not isinstance(b, dict):
            raise ValueError(f"bones[{i}]: dict required")
        k = b.get("id")
        if not isinstance(k, str) or not 1 <= len(k) <= MAX_ID:
            raise ValueError(f"bones[{i}]: id must be a string of 1..{MAX_ID} characters")
        if k in info:
            raise ValueError(f"bones[{i}]: duplicate id {k!r}")
        parent = b.get("parent")
        if parent is not None and not isinstance(parent, str):
            raise ValueError(f"bones[{i}]: parent must be a bone id or None")
        length = _num(b.get("length"), f"bones[{i}].length", 0.001, MAX_LENGTH)
        angle = _num(b.get("angle_deg"), f"bones[{i}].angle_deg", -MAX_ANGLE, MAX_ANGLE)
        lo = _num(b["min_deg"], f"bones[{i}].min_deg", -MAX_ANGLE, MAX_ANGLE) if "min_deg" in b else None
        hi = _num(b["max_deg"], f"bones[{i}].max_deg", -MAX_ANGLE, MAX_ANGLE) if "max_deg" in b else None
        if lo is not None and hi is not None and lo > hi:
            raise ValueError(f"bones[{i}]: min_deg above max_deg")
        info[k] = (parent, length, angle, lo, hi)
        order.append(k)
    roots = [k for k in order if info[k][0] is None]
    if len(roots) != 1:
        raise ValueError(f"bones: exactly one root (parent None) required, found {len(roots)}")
    for k in order:
        p = info[k][0]
        if p is not None and p not in info:
            raise ValueError(f"bone {k!r}: unknown parent {p!r}")
    depth, pos = {}, {}

    def solve(k, trail=()):
        if k in pos:
            return pos[k]
        if k in trail:
            raise ValueError(f"bone {k!r}: cycle in hierarchy")
        parent, length, angle, _, _ = info[k]
        if parent is None:
            start, world, d = (0.0, 0.0), angle, 0
        else:
            ps = solve(parent, trail + (k,))
            start, world, d = ps["tail"], ps["world_deg"] + angle, ps["depth"] + 1
        rad = math.radians(world)
        tail = (start[0] + length * math.cos(rad), start[1] + length * math.sin(rad))
        pos[k] = {"start": start, "tail": tail, "world_deg": world, "depth": d}
        return pos[k]

    rows = []
    for k in order:
        s = solve(k)
        _, length, angle, lo, hi = info[k]
        ok = (lo is None or angle >= lo) and (hi is None or angle <= hi)
        rows.append({"id": k, "parent": info[k][0], "depth": s["depth"], "world_deg": _r(s["world_deg"]),
                     "start": [_r(s["start"][0]), _r(s["start"][1])], "tail": [_r(s["tail"][0]), _r(s["tail"][1])],
                     "within_limits": ok})
    parents = {info[k][0] for k in order}
    reach = max(math.hypot(*pos[k]["tail"]) for k in order)
    return {"bones": rows, "root": roots[0], "leaves": [k for k in order if k not in parents],
            "max_depth": max(pos[k]["depth"] for k in order), "max_reach": _r(reach),
            "all_within_limits": all(r["within_limits"] for r in rows), "status_note": STATUS_NOTE}

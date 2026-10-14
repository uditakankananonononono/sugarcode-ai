"""Row 322 architectural rendering: pinhole projection of building geometry and sun shadow length.

Projects 3D points (x east, y up, z north) into an image for a camera with position, yaw about the vertical axis
and focal length in pixels, and returns a box's 12 projected edges and 2D bounds. Also computes the shadow length
cast by a wall for a given sun altitude. No lighting, materials or visual quality: this is geometry only."""
import math

MAX_POINTS = 1000
MIN_DEPTH = 1e-6
STATUS_NOTE = ("PARTIAL: pinhole projection and shadow-length geometry only; no lighting, materials, "
               "or claim of visual quality")
_EDGES = [(0, 1), (1, 3), (3, 2), (2, 0), (4, 5), (5, 7), (7, 6), (6, 4), (0, 4), (1, 5), (2, 6), (3, 7)]


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


def project(points, cam_pos=(0, 0, 0), yaw_deg=0, focal_px=1000):
    """Camera looks along +z when yaw is 0; positive yaw turns it toward +x. Returns (u, v) per point, y up."""
    if not isinstance(points, (list, tuple)) or not 1 <= len(points) <= MAX_POINTS:
        raise ValueError(f"points: 1 to {MAX_POINTS} required")
    if not isinstance(cam_pos, (list, tuple)) or len(cam_pos) != 3:
        raise ValueError("cam_pos: (x, y, z) required")
    cx, cy, cz = (_num(c, "cam_pos", -100000, 100000) for c in cam_pos)
    yaw = math.radians(_num(yaw_deg, "yaw_deg", -180, 180))
    f = _num(focal_px, "focal_px", 1, 100000)
    out = []
    for p in points:
        if not isinstance(p, (list, tuple)) or len(p) != 3:
            raise ValueError("point: (x, y, z) required")
        x, y, z = (_num(c, "point", -100000, 100000) for c in p)
        dx, dy, dz = x - cx, y - cy, z - cz
        depth = dx * math.sin(yaw) + dz * math.cos(yaw)
        side = dx * math.cos(yaw) - dz * math.sin(yaw)
        if depth <= 0:
            raise ValueError("point is behind the camera")
        if depth < MIN_DEPTH:
            raise ValueError("point is closer than 1e-06 to the camera plane")
        out.append((f * side / depth + 0.0, f * dy / depth + 0.0))
    return out


def box_wireframe(origin, size, **cam):
    ox, oy, oz = (_num(c, "origin", -100000, 100000) for c in origin)
    sx, sy, sz = (_num(c, "size", 0.001, 100000) for c in size)
    corners = [(ox + i * sx, oy + j * sy, oz + k * sz) for k in (0, 1) for j in (0, 1) for i in (0, 1)]
    pts = project(corners, **cam)
    us, vs = [p[0] for p in pts], [p[1] for p in pts]
    return {"edges": [(pts[a], pts[b]) for a, b in _EDGES], "bounds": (min(us), min(vs), max(us), max(vs)),
            "status": STATUS_NOTE}


def shadow_length(height, sun_altitude_deg):
    h = _num(height, "height", 0, 100000)
    a = _num(sun_altitude_deg, "sun_altitude_deg", 1, 90)
    return h / math.tan(math.radians(a))

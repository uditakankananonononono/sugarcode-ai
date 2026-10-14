"""Row 298 physics simulation (PARTIAL): fixed-step projectile integration compared with the closed-form answer.

Integrates a point mass under constant gravity with semi-implicit Euler, no drag, flat ground at y = 0.
Reports landing time, range and apex from the integration and the continuous analytic values with their errors.
No claim of realism for real objects, air resistance, spin, terrain or any engine."""
import math

MAX_STEPS = 100000
MAX_SPEED = 1000
G_RANGE = (0.1, 100)
DT_RANGE = (0.0001, 0.1)
MAX_HEIGHT = 10000
STATUS_NOTE = ("PARTIAL: semi-implicit Euler point mass under constant gravity, no drag, flat ground, compared with the "
               "closed-form answer; no claim of realism for real objects or any physics engine")


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


def simulate_projectile(speed, angle_deg, g=9.81, dt=0.01, height=0):
    v = _num(speed, "speed", 0, MAX_SPEED)
    a = _num(angle_deg, "angle_deg", 0, 90)
    gg = _num(g, "g", *G_RANGE)
    h = _num(dt, "dt", *DT_RANGE)
    y0 = _num(height, "height", 0, MAX_HEIGHT)
    vx, vy = v * math.cos(math.radians(a)), v * math.sin(math.radians(a))
    # continuous closed form
    t_flight = (vy + math.sqrt(vy * vy + 2 * gg * y0)) / gg
    apex_a = y0 + vy * vy / (2 * gg) if vy > 0 else y0
    range_a = vx * t_flight
    if t_flight / h > MAX_STEPS:
        raise ValueError(f"flight would need more than {MAX_STEPS} steps; raise dt")
    x = 0.0
    y = y0
    vyc = vy
    apex = y0
    steps = 0
    while True:
        steps += 1
        vyc -= gg * h
        px, py = x, y
        x += vx * h
        y += vyc * h
        if y < 0:
            frac = py / (py - y)
            t_land = (steps - 1 + frac) * h
            x_land = px + (x - px) * frac
            break
        apex = max(apex, y)
        if steps > MAX_STEPS:
            raise ValueError(f"no landing within {MAX_STEPS} steps; raise dt")
    return {"steps": steps, "landing_time": t_land, "range": x_land, "apex": apex,
            "analytic": {"flight_time": t_flight, "range": range_a, "apex": apex_a},
            "errors": {"time": abs(t_land - t_flight), "range": abs(x_land - range_a), "apex": abs(apex - apex_a)},
            "status_note": STATUS_NOTE}

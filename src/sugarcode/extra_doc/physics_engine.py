"""Physics Engine - exact fixed-step simulation of one ball under gravity with a floor.

Pure function over caller data. No rendering, no network, no clock, no floats, no
randomness. Input: height, int 0..1000 (start height above the floor); velocity, int
-100..100 (up is positive); gravity, int 1..100; steps_per_unit, int 1..100 (the time
step is dt = 1/steps_per_unit); steps, int 1..500; restitution_num and restitution_den,
ints with 1 <= den <= 10 and 0 <= num <= den (bounce keeps num/den of the speed).

Each step (semi-implicit Euler, all arithmetic in exact Fractions): v = v - g*dt, then
y = y + v*dt. If y < 0 the ball is put on the floor (y = 0) and v = -v * restitution,
and the bounce counter rises. The result reports final height and velocity (Fraction
strings), the bounce count, the step number of the first bounce (or null), and the
maximum height seen (the start included).

Scope: PARTIAL for the Physics Engine line. Exact stepping of one ball in one dimension
with one discrete rule. It is not a physics engine in the general sense: no 2D or 3D, no
collisions between bodies, no friction, no continuous collision detection, no adaptive
step. The discrete rule is not claimed to match true physics.

Not claimed: that the stepping matches real physical motion, that the step is small
enough for any purpose, that the numbers apply to a real object, or anything about the
real world. Every claim flag in the result is False.
"""
from fractions import Fraction

_TOP = frozenset({"height", "velocity", "gravity", "steps_per_unit", "steps", "restitution_num", "restitution_den"})

NOT_CLAIMED = (
    "the stepping matches real physical motion",
    "the time step is small enough for any purpose",
    "the numbers apply to a real object",
    "real-world outcome",
)
CLAIMS = {"matches_real_physics": False, "step_adequate": False, "real_object": False, "real_world": False}


class PhysicsError(ValueError):
    pass


def _int(data, key, lo, hi):
    v = data[key]
    if type(v) is not int:
        raise PhysicsError(f"{key} must be an int")
    if v < lo or v > hi:
        raise PhysicsError(f"{key} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise PhysicsError("data keys must be exactly " + ", ".join(sorted(_TOP)))
    h = _int(data, "height", 0, 1000)
    v = _int(data, "velocity", -100, 100)
    g = _int(data, "gravity", 1, 100)
    spu = _int(data, "steps_per_unit", 1, 100)
    n = _int(data, "steps", 1, 500)
    den = _int(data, "restitution_den", 1, 10)
    num = _int(data, "restitution_num", 0, den)
    return h, v, g, spu, n, num, den


def physics_engine(data):
    h, v0, g, spu, n, num, den = _validate(data)
    dt = Fraction(1, spu)
    e = Fraction(num, den)
    y, v = Fraction(h), Fraction(v0)
    top = y
    bounces = 0
    first = None
    for step in range(1, n + 1):
        v = v - g * dt
        y = y + v * dt
        if y < 0:
            y = Fraction(0)
            v = -v * e
            bounces += 1
            if first is None:
                first = step
        if y > top:
            top = y
    return {
        "status": "completed",
        "final_height": str(y),
        "final_velocity": str(v),
        "bounces": bounces,
        "first_bounce_step": first,
        "max_height": str(top),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }

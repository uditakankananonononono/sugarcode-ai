"""Row 577, Physics Engine (bounded scope: one exact two-body model): head-on collision of two point masses on a line.

collide_1d(m1, x1, v1, m2, x2, v2, restitution) puts body 1 at x1 and body 2 at x2 (x1 < x2) moving at constant
velocities v1 and v2. If body 1 is closing on body 2 (v1 > v2) they meet once, and the speeds change at that meeting
by conservation of momentum and the restitution rule (the relative speed after is restitution times the relative speed
before, reversed): 1 is a perfectly elastic bounce, 0 is a perfectly sticky one with equal velocities after. All
arithmetic is exact (Fractions). It returns:
  collides             True when v1 > v2;
  time                 when they meet, (x2 - x1) / (v1 - v2), or None;
  impact_position      where, x1 + v1 * time, or None;
  velocities_after     [u1, u2] after the meeting (the unchanged [v1, v2] when they never meet);
  momentum_before / momentum_after   m1 v1 + m2 v2 for the starting and final velocities;
  energy_before / energy_after       half the sum of m v squared, the same two ways;
  energy_lost          energy_before - energy_after (never negative).
Caps: masses in (0, 1000000]; positions and velocities in [-1000000, 1000000]; restitution in [0, 1]; every value a
nonbool int or Fraction with 32-bit numerator and denominator; x1 strictly below x2.
Order of checks: types, 32-bit widths and ranges in argument order (m1, x1, v1, m2, x2, v2, restitution), then
x1 below x2, and only then any arithmetic.

NOT_CLAIMED: a textbook model only. It says nothing about real objects of size, friction, deformation, rotation, a
third body, air, or whether a restitution coefficient is constant; it is not a physics engine, only this one
calculation, and does not step time. No clinical or wet-lab claim.
"""
from fractions import Fraction

LIM = 1000000


def _num(v, what):
    if type(v) not in (int, Fraction):
        raise TypeError(what + ' must be a nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def collide_1d(m1, x1, v1, m2, x2, v2, restitution):
    a = _num(m1, 'm1')
    if not 0 < a <= LIM:
        raise ValueError('m1 must be greater than 0 and at most 1000000')
    p1 = _num(x1, 'x1')
    if not -LIM <= p1 <= LIM:
        raise ValueError('x1 must be between -1000000 and 1000000')
    u1 = _num(v1, 'v1')
    if not -LIM <= u1 <= LIM:
        raise ValueError('v1 must be between -1000000 and 1000000')
    b = _num(m2, 'm2')
    if not 0 < b <= LIM:
        raise ValueError('m2 must be greater than 0 and at most 1000000')
    p2 = _num(x2, 'x2')
    if not -LIM <= p2 <= LIM:
        raise ValueError('x2 must be between -1000000 and 1000000')
    u2 = _num(v2, 'v2')
    if not -LIM <= u2 <= LIM:
        raise ValueError('v2 must be between -1000000 and 1000000')
    e = _num(restitution, 'restitution')
    if not 0 <= e <= 1:
        raise ValueError('restitution must be between 0 and 1')
    if not p1 < p2:
        raise ValueError('x1 must be below x2')
    hit = u1 > u2
    if hit:
        t = (p2 - p1) / (u1 - u2)
        where = p1 + u1 * t
        w1 = (a * u1 + b * u2 + b * e * (u2 - u1)) / (a + b)
        w2 = (a * u1 + b * u2 + a * e * (u1 - u2)) / (a + b)
    else:
        t = where = None
        w1, w2 = u1, u2
    before = Fraction(1, 2) * (a * u1 * u1 + b * u2 * u2)
    after = Fraction(1, 2) * (a * w1 * w1 + b * w2 * w2)
    return {'collides': hit, 'time': t, 'impact_position': where, 'velocities_after': [w1, w2],
            'momentum_before': a * u1 + b * u2, 'momentum_after': a * w1 + b * w2,
            'energy_before': before, 'energy_after': after, 'energy_lost': before - after}

"""Row 186 Kalman Filtering - Estimates hidden states (Bounded: one exact scalar local-level filter): follow a hidden level through noisy readings.

kalman_filter(zs, m0, p0, q, r) takes zs, a list (subclasses refused) of 1 to 6 exact ints, each -100 to 100, the readings,
m0, an exact int -100 to 100, the starting estimate, p0, an exact int 0 to 100, its variance, q, an exact int 0 to 20, the
variance added to the estimate before each reading, and r, an exact int 1 to 20, the reading variance. For each reading z
the filter first sets p = p + q, then the gain g = p / (p + r), then the estimate m = m + g * (z - m), then p = (1 - g) * p.
All values are exact fractions. 'gains', 'estimates' and 'variances' are the lists of g, m and p after each reading, each a
[numerator, denominator] pair (lowest terms, denominator above 0). 'final' is the last estimate pair.
It returns {'gains': ..., 'estimates': ..., 'variances': ..., 'final': ...}.
Order of checks: zs (type, length, then each entry in order: type, then range), m0 (type, then range), p0 (type, then
range), q (type, then range), r (type, then range).

NOT_CLAIMED: this runs one fixed-parameter scalar filter on supplied readings. It does not estimate the noise variances,
test that the model fits, smooth backward, handle several dimensions, or say the estimate is correct.
"""

from fractions import Fraction


def _int(name, x, lo, hi):
    if type(x) is not int:
        raise TypeError(name + ' must be an exact int')
    if not lo <= x <= hi:
        raise ValueError(name + ' must be ' + str(lo) + ' to ' + str(hi))


def _pair(f):
    return [f.numerator, f.denominator]


def kalman_filter(zs, m0, p0, q, r):
    if type(zs) is not list:
        raise TypeError('zs must be a list')
    if not 1 <= len(zs) <= 6:
        raise ValueError('zs must hold 1 to 6 entries')
    for i, z in enumerate(zs, 1):
        _int('reading ' + str(i), z, -100, 100)
    _int('m0', m0, -100, 100)
    _int('p0', p0, 0, 100)
    _int('q', q, 0, 20)
    _int('r', r, 1, 20)
    m = Fraction(m0)
    p = Fraction(p0)
    gains = []
    ests = []
    variances = []
    for z in zs:
        p = p + q
        g = p / (p + r)
        m = m + g * (z - m)
        p = (1 - g) * p
        gains.append(_pair(g))
        ests.append(_pair(m))
        variances.append(_pair(p))
    return {'gains': gains, 'estimates': ests, 'variances': variances, 'final': ests[-1][:]}

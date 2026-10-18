"""Bounded exact arithmetic on caller-supplied finite integer-weight laws.

SCOPE: pure arithmetic, at most 16 atoms, integer labels |x| <= 100,
integer weights 0..100; no sampling, retrieval, inference or network.
NOT_CLAIMED: empirical calibration, real-world probabilities, integration.
"""
from fractions import Fraction

CLAIMS = False
SCOPE = "caller-supplied finite weighted integer distributions only"
NOT_CLAIMED = "calibration, sampling, retrieval, network, product integration"
MAX_ATOMS = 16
MAX_VALUE = 100
MAX_WEIGHT = 100
MAX_ORDER = 8


def _integer(value, name, low, high):
    if type(value) is not int:
        raise TypeError(name + " must be an integer")
    if value < low or value > high:
        raise ValueError(name + " out of range")
    return value


def _law(law):
    if type(law) is not dict:
        raise TypeError("law must be a dict")
    if not 1 <= len(law) <= MAX_ATOMS:
        raise ValueError("law size out of range")
    out = {}
    for value, weight in law.items():
        _integer(value, "value", -MAX_VALUE, MAX_VALUE)
        _integer(weight, "weight", 0, MAX_WEIGHT)
        out[value] = weight
    total = sum(out.values())
    if total == 0:
        raise ValueError("law must have positive mass")
    return out, total


def normalize(law):
    """Return exact probabilities, retaining zero-weight atoms."""
    data, total = _law(law)
    return {x: Fraction(w, total) for x, w in sorted(data.items())}


def expectation(law):
    data, total = _law(law)
    return Fraction(sum(x*w for x, w in data.items()), total)


def variance(law):
    data, total = _law(law)
    mean = Fraction(sum(x*w for x, w in data.items()), total)
    return sum((Fraction(w, total)*(x-mean)**2 for x, w in data.items()), Fraction())


def raw_moment(law, order):
    data, total = _law(law)
    _integer(order, "order", 0, MAX_ORDER)
    return Fraction(sum(x**order*w for x, w in data.items()), total)


def event_probability(law, values):
    data, total = _law(law)
    if type(values) not in (list, tuple):
        raise TypeError("values must be a list or tuple")
    if len(values) > MAX_ATOMS:
        raise ValueError("event size out of range")
    seen = set()
    for value in values:
        _integer(value, "value", -MAX_VALUE, MAX_VALUE)
        if value in seen:
            raise ValueError("event values must be distinct")
        seen.add(value)
    return Fraction(sum(data.get(x, 0) for x in seen), total)


def cumulative_probability(law, threshold):
    data, total = _law(law)
    _integer(threshold, "threshold", -MAX_VALUE, MAX_VALUE)
    return Fraction(sum(w for x, w in data.items() if x <= threshold), total)


def quantile(law, numerator, denominator):
    """Smallest positive-mass atom whose CDF reaches numerator/denominator.

    The zero quantile is the smallest positive-mass atom.
    """
    data, total = _law(law)
    _integer(numerator, "numerator", 0, MAX_WEIGHT)
    _integer(denominator, "denominator", 1, MAX_WEIGHT)
    if numerator > denominator:
        raise ValueError("quantile out of range")
    mass = 0
    for x, w in sorted(data.items()):
        if w == 0:
            continue
        mass += w
        if mass*denominator >= numerator*total:
            return x
    raise AssertionError("unreachable quantile")


def convolution(left, right):
    a, ta = _law(left)
    b, tb = _law(right)
    result = {}
    for x, wx in a.items():
        for y, wy in b.items():
            result[x+y] = result.get(x+y, 0) + wx*wy
    return {x: Fraction(w, ta*tb) for x, w in sorted(result.items())}


def independent_product(left, right):
    a, ta = _law(left)
    b, tb = _law(right)
    result = {}
    for x, wx in a.items():
        for y, wy in b.items():
            result[x*y] = result.get(x*y, 0) + wx*wy
    return {x: Fraction(w, ta*tb) for x, w in sorted(result.items())}


def collision_probability(law):
    data, total = _law(law)
    return Fraction(sum(w*w for w in data.values()), total*total)

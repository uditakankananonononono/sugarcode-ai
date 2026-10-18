"""Bounded exact rational and simple continued-fraction arithmetic.

SCOPE: caller-supplied integers, rational pairs and coefficient sequences.
NOT_CLAIMED: irrational approximation guarantees, cryptography, integration.
"""
from fractions import Fraction

CLAIMS = False
SCOPE = "finite exact rational arithmetic only"
NOT_CLAIMED = "irrational inputs, cryptography, retrieval, network, product integration"
MAX_INTEGER = 10000
MAX_TERMS = 16
MAX_INTERMEDIATES = 512
MAX_DENOMINATOR = 32


def _int(value, name, low, high):
    if type(value) is not int:
        raise TypeError(name + " must be an integer")
    if value < low or value > high:
        raise ValueError(name + " out of range")
    return value


def _pair(p, q):
    _int(p, "numerator", -MAX_INTEGER, MAX_INTEGER)
    _int(q, "denominator", 1, MAX_INTEGER)
    return p, q


def _terms(terms):
    if type(terms) not in (list, tuple):
        raise TypeError("terms must be a list or tuple")
    if not 1 <= len(terms) <= MAX_TERMS:
        raise ValueError("terms size out of range")
    for i, value in enumerate(terms):
        _int(value, "coefficient", -MAX_INTEGER if i == 0 else 1, MAX_INTEGER)
    return tuple(terms)


def expand(p, q):
    """Canonical simple continued fraction, including negative rationals."""
    p, q = _pair(p, q)
    out = []
    while q:
        a, r = divmod(p, q)
        out.append(a)
        p, q = q, r
    return tuple(out)


def evaluate(terms):
    values = _terms(terms)
    result = Fraction(values[-1])
    for a in reversed(values[:-1]):
        result = a + 1/result
    return result


def convergents(terms):
    values = _terms(terms)
    pm2, pm1, qm2, qm1 = 0, 1, 1, 0
    out = []
    for a in values:
        p, q = a*pm1+pm2, a*qm1+qm2
        out.append(Fraction(p, q))
        pm2, pm1, qm2, qm1 = pm1, p, qm1, q
    return tuple(out)


def continuant(terms):
    """Numerator continuant; the first coefficient may be negative."""
    values = _terms(terms)
    previous, current = 0, 1
    for a in values:
        previous, current = current, a*current+previous
    return current


def convergent_determinants(terms):
    values = _terms(terms)
    p0, p1, q0, q1 = 0, 1, 1, 0
    out = []
    for a in values:
        p, q = a*p1+p0, a*q1+q0
        out.append(p*q1-p1*q)
        p0, p1, q0, q1 = p1, p, q1, q
    return tuple(out)


def convergent_errors(p, q):
    p, q = _pair(p, q)
    target = Fraction(p, q)
    # The Euclidean expansion may exceed the public caller-supplied term cap.
    # Its length is still bounded by the numerator/denominator input cap.
    pm2, pm1, qm2, qm1 = 0, 1, 1, 0
    errors = []
    for a in expand(p, q):
        numerator, denominator = a*pm1+pm2, a*qm1+qm2
        errors.append(target-Fraction(numerator, denominator))
        pm2, pm1, qm2, qm1 = pm1, numerator, qm1, denominator
    return tuple(errors)


def intermediate_convergents(terms):
    """Include each intermediate with multiplier 1..a_i, for i >= 1."""
    values = _terms(terms)
    if sum(values[1:]) > MAX_INTERMEDIATES:
        raise ValueError("intermediate count out of range")
    pm2, pm1, qm2, qm1 = 1, values[0], 0, 1
    out = []
    for a in values[1:]:
        for k in range(1, a+1):
            out.append(Fraction(k*pm1+pm2, k*qm1+qm2))
        pm2, pm1, qm2, qm1 = pm1, a*pm1+pm2, qm1, a*qm1+qm2
    return tuple(out)


def best_approximation(p, q, limit):
    """Closest fraction with denominator <= limit; ties use (q, p)."""
    p, q = _pair(p, q)
    _int(limit, "limit", 1, MAX_DENOMINATOR)
    target = Fraction(p, q)
    candidates = set()
    for d in range(1, limit+1):
        n = p*d // q
        candidates.add(Fraction(n, d))
        candidates.add(Fraction(n+1, d))
    return min(candidates, key=lambda x: (abs(x-target), x.denominator, x.numerator))


def rational_floor(p, q):
    p, q = _pair(p, q)
    return p // q


def rational_compare(p, q, r, s):
    p, q = _pair(p, q)
    r, s = _pair(r, s)
    difference = p*s-r*q
    return (difference > 0)-(difference < 0)

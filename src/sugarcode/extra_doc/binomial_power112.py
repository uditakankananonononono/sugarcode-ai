"""Row 112 Power Analysis - Determines sample sizes needed for statistical significance.

PARTIAL: exact finite sample-size search for a one-sided fair-binomial test.
Input exact dict alpha, alternative, target, maximum. Each fraction is an exact
list [numerator, denominator] of exact ints 1 <= numerator < denominator <= 12;
alternative must exceed 1/2. Maximum is an exact int 1..8. For each n from 1 to
maximum, reject the fair-coin null for counts k with P_null(K >= k) <= alpha.
Power is the alternative probability of rejection. Return powers as reduced
rational pairs in n order, minimum as the first n attaining target or None,
and claims as three False booleans. Finite search failure is not impossibility.
NOT_CLAIMED: general power analysis, assumptions verification, production readiness.
"""
from fractions import Fraction
from math import comb
SCOPE = 'PARTIAL: exact bounded one-sided fair-binomial sample-size search only'
NOT_CLAIMED = ('general power analysis', 'assumptions verification', 'production readiness')


def search(data):
    if type(data) is not dict or set(data) != {'alpha', 'alternative', 'target', 'maximum'}:
        raise ValueError('exact dict with alpha, alternative, target, maximum required')
    values = {}
    for name in ('alpha', 'alternative', 'target'):
        row = data[name]
        if type(row) is not list or len(row) != 2:
            raise ValueError(name + ' must be an exact two-integer fraction list')
        if any(type(v) is not int for v in row) or not 1 <= row[0] < row[1] <= 12:
            raise ValueError(name + ' requires integers 1 <= numerator < denominator <= 12')
        values[name] = Fraction(*row)
    p = values['alternative']
    if p <= Fraction(1, 2):
        raise ValueError('alternative must exceed one half')
    maximum = data['maximum']
    if type(maximum) is not int or not 1 <= maximum <= 8:
        raise ValueError('maximum must be an exact integer 1..8')
    powers = []
    minimum = None
    for n in range(1, maximum + 1):
        power = sum((comb(n, k) * p**k * (1-p)**(n-k)
                     for k in range(n+1)
                     if Fraction(sum(comb(n, j) for j in range(k, n+1)), 2**n) <= values['alpha']), Fraction(0))
        powers.append([power.numerator, power.denominator])
        if minimum is None and power >= values['target']:
            minimum = n
    return {'powers': powers, 'minimum': minimum, 'claims': [False, False, False]}

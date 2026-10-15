"""Row 145 Generative Modeling - Creates new samples from learned distributions.

PARTIAL: exact beta-Bernoulli posterior predictive count and supplied-quantile draw.
Input exact dict prior, observed, length, quantile. Prior exact two-value list of
exact integers 1..4 (success,failure beta parameters); observed exact two-value
list of exact integers 0..4 (success,failure counts); length exact integer 1..6;
quantile exact two-integer list [num,den], 0 <= num < den <= 12 and den >= 1.
Learn beta parameters by adding observed counts; form beta-binomial predictive
mass for success counts k=0..length. Return parameters integer pair, masses in
k order as reduced rational pairs, draw as first k with cumulative mass strictly
greater than quantile, claims three False. Quantile is supplied, never random.
NOT_CLAIMED: general generative modeling, random sampling, empirical model validity.
"""
from fractions import Fraction
from math import comb
SCOPE = 'PARTIAL: exact beta-Bernoulli predictive count and supplied-quantile draw only'
NOT_CLAIMED = ('general generative modeling', 'random sampling', 'empirical model validity')


def _rising(a, count):
    result = 1
    for i in range(count):
        result *= a+i
    return result


def generate(data):
    if type(data) is not dict or set(data) != {'prior', 'observed', 'length', 'quantile'}:
        raise ValueError('exact dict with prior, observed, length, quantile required')
    for name, lower in (('prior', 1), ('observed', 0)):
        row = data[name]
        if type(row) is not list or len(row) != 2:
            raise ValueError(name + ' must be an exact two-value list')
        if any(type(v) is not int or not lower <= v <= 4 for v in row):
            raise ValueError(name + ' values must be exact integers ' + str(lower) + '..4')
    length = data['length']
    if type(length) is not int or not 1 <= length <= 6:
        raise ValueError('length must be an exact integer 1..6')
    q = data['quantile']
    if type(q) is not list or len(q) != 2:
        raise ValueError('quantile must be an exact two-value list')
    if any(type(v) is not int for v in q) or not 0 <= q[0] < q[1] <= 12:
        raise ValueError('quantile requires integers 0 <= numerator < denominator <= 12')
    q = Fraction(*q)
    a, b = [x+y for x, y in zip(data['prior'], data['observed'])]
    masses = [Fraction(comb(length, k)*_rising(a, k)*_rising(b, length-k), _rising(a+b, length)) for k in range(length+1)]
    cumulative = Fraction(0)
    draw = None
    for k, mass in enumerate(masses):
        cumulative += mass
        if draw is None and cumulative > q:
            draw = k
    return {'parameters': [a, b], 'masses': [[p.numerator, p.denominator] for p in masses], 'draw': draw, 'claims': [False, False, False]}

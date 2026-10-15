"""Row 120 P-Hacking Prevention - Avoids statistical manipulation.

PARTIAL: exact running likelihood-ratio e-process for supplied binary outcomes.
Input exact dict outcomes, alternative, alpha. Outcomes exact list of 1..8 exact
integer bits; alternative exact two-integer list [num,den] with 1 <= num < den
<= 12 and alternative > 1/2; alpha same fraction schema, no >1/2 requirement.
Null is independent fair bits, fixed alternative is Bernoulli(p). E0=1; multiply
E by 2p for bit1, by 2(1-p) for bit0. Running anytime p-bound=min(1,1/max(E0..Et)).
Return evalues and bounds rational pairs per observed bit, first_crossing first
1-based time bound <= alpha or None, claims three False. Continue after crossing.
No null assumptions, data provenance or actual manipulation prevention verified.
NOT_CLAIMED: manipulation prevention, assumptions verification, production readiness.
"""
from fractions import Fraction
SCOPE = 'PARTIAL: exact supplied-bit fixed-alternative running e-process only'
NOT_CLAIMED = ('manipulation prevention', 'assumptions verification', 'production readiness')


def analyze(data):
    if type(data) is not dict or set(data) != {'outcomes', 'alternative', 'alpha'}:
        raise ValueError('exact dict with outcomes, alternative, alpha required')
    outcomes = data['outcomes']
    if type(outcomes) is not list or not 1 <= len(outcomes) <= 8:
        raise ValueError('outcomes must be an exact list of 1..8 bits')
    for bit in outcomes:
        if type(bit) is not int or bit not in (0, 1):
            raise ValueError('outcomes must be exact integer bits')
    fractions = {}
    for name in ('alternative', 'alpha'):
        row = data[name]
        if type(row) is not list or len(row) != 2:
            raise ValueError(name + ' must be an exact two-value fraction list')
        if any(type(v) is not int for v in row) or not 1 <= row[0] < row[1] <= 12:
            raise ValueError(name + ' requires integers 1 <= numerator < denominator <= 12')
        fractions[name] = Fraction(*row)
    p = fractions['alternative']
    if p <= Fraction(1, 2):
        raise ValueError('alternative must exceed one half')
    e = Fraction(1)
    peak = Fraction(1)
    evalues, bounds = [], []
    crossing = None
    for time, bit in enumerate(outcomes, 1):
        e *= 2*(p if bit else 1-p)
        peak = max(peak, e)
        bound = 1/peak
        evalues.append([e.numerator, e.denominator])
        bounds.append([bound.numerator, bound.denominator])
        if crossing is None and bound <= fractions['alpha']:
            crossing = time
    return {'evalues': evalues, 'bounds': bounds, 'first_crossing': crossing, 'claims': [False, False, False]}

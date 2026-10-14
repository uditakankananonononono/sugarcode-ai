"""Row 265, Plot Twist Design: surprise versus plausibility of a twist (exact).

Model (one stated model, nothing more): a reader holds prior probability pi that
the twist happens. Before the reveal the story has planted k clues. Clue j is
seen with probability a_j if the twist is coming and b_j if it is not (clues are
conditionally independent given the hypothesis). Reported, all exact Fractions:
- surprise = 1 - pi (chance the reader did not expect it);
- bayes_factor = prod a_j / b_j;
- posterior = P(twist | all clues seen) = pi prod a / (pi prod a + (1-pi) prod b),
  the plausibility in hindsight;
- surprising = surprise >= min_surprise and plausible = posterior >= min_plausible,
  with both thresholds supplied by the caller; well_designed = both.
Caps: 0 to 8 clues; pi, a_j, b_j, thresholds nonbool int or Fraction with
numerator and denominator at most 32 bits; pi in (0, 1); a_j, b_j in (0, 1];
thresholds in [0, 1]. Order of checks: container types and counts first (at most a few
hundred cheap element type checks), then value conversion and range checks, and
only then any arithmetic on the values.

NOT_CLAIMED: a two-hypothesis Bayes model only. It scores numbers the caller
supplies; it reads no story text, judges no originality or quality, generates no
plot, and renders nothing visual. Probabilities are caller inputs and unverified.
No clinical or wet-lab claim.
"""
from fractions import Fraction

MAX_CLUES = 8


def _q(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def design_twist(prior, clues, min_surprise, min_plausible):
    if type(clues) not in (list, tuple):
        raise TypeError('clues must be a list or tuple of pairs')
    if len(clues) > MAX_CLUES:
        raise ValueError('at most 8 clues')
    for c in clues:
        if type(c) not in (list, tuple) or len(c) != 2:
            raise TypeError('each clue must be a pair (a, b)')
    pi = _q(prior)
    pairs = [(_q(c[0]), _q(c[1])) for c in clues]
    ms, mp = _q(min_surprise), _q(min_plausible)
    if not 0 < pi < 1:
        raise ValueError('prior must be in (0, 1)')
    if any(not 0 < v <= 1 for pair in pairs for v in pair):
        raise ValueError('clue probabilities must be in (0, 1]')
    if not (0 <= ms <= 1 and 0 <= mp <= 1):
        raise ValueError('thresholds must be in [0, 1]')
    pa, pb = Fraction(1), Fraction(1)
    for a, b in pairs:
        pa *= a
        pb *= b
    posterior = pi * pa / (pi * pa + (1 - pi) * pb)
    surprise = 1 - pi
    surprising, plausible = surprise >= ms, posterior >= mp
    return {'surprise': surprise, 'bayes_factor': pa / pb, 'posterior': posterior,
            'surprising': surprising, 'plausible': plausible,
            'well_designed': surprising and plausible}

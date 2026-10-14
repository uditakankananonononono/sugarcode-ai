"""Row 256, Expert Advice Aggregation: multiplicative-weights mixture (exact).

Implements the multiplicative-weights (linear Hedge variant) learner: weights
start at 1 for each of n experts; in each round the learner's mixture is the
weights normalised BEFORE the round's losses are seen (prior-round weights), the
losses l[t][i] in [0, 1] are then revealed (full information), and
w_i *= (1 - eta * l[t][i]) with 0 < eta <= 1/2. Everything is an exact Fraction.
Reported: the mixture used each round, the learner's expected loss, each expert's
cumulative loss, and the exact regret against every fixed expert
(learner expected loss minus that expert's loss). The module also reports the
best fixed expert (lowest cumulative loss, ties to the lowest index).
It uses the linear (1 - eta l) update instead of exp(-eta l) because the
exponential is not rational.
Caps: 1 to 5 experts, 1 to 16 rounds, losses and eta nonbool int or Fraction with
numerator and denominator at most 32 bits, losses in [0, 1]. Checks run before
any scan.

NOT_CLAIMED: no regret bound is asserted by this module (the textbook bound is
not checked here); regret values are exact for the supplied losses only. Losses
are caller inputs and are not verified; no claim about real experts, forecasts or
outcomes; no clinical or wet-lab claim; no exponential Hedge.
"""
from fractions import Fraction

MAX_EXPERTS, MAX_ROUNDS = 5, 16


def _q(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def aggregate_experts(losses, eta):
    if type(losses) not in (list, tuple):
        raise TypeError('losses must be a list or tuple of rounds')
    T = len(losses)
    if not 1 <= T <= MAX_ROUNDS:
        raise ValueError('rounds must be between 1 and 16')
    for row in losses:
        if type(row) not in (list, tuple):
            raise TypeError('losses must be a list or tuple of rounds')
    n = len(losses[0])
    if not 1 <= n <= MAX_EXPERTS:
        raise ValueError('experts must be between 1 and 5')
    if any(len(row) != n for row in losses):
        raise ValueError('every round must have the same number of experts')
    L = [[_q(v) for v in row] for row in losses]
    eta = _q(eta)
    if any(v < 0 or v > 1 for row in L for v in row):
        raise ValueError('losses must be in [0, 1]')
    if not 0 < eta <= Fraction(1, 2):
        raise ValueError('eta must be in (0, 1/2]')
    w = [Fraction(1)] * n
    mixes, learner = [], Fraction(0)
    cum = [Fraction(0)] * n
    for row in L:
        s = sum(w)
        p = [v / s for v in w]
        mixes.append(p)
        learner += sum(p[i] * row[i] for i in range(n))
        cum = [cum[i] + row[i] for i in range(n)]
        w = [w[i] * (1 - eta * row[i]) for i in range(n)]
    regret = [learner - c for c in cum]
    best = min(range(n), key=lambda i: (cum[i], i))
    return {'mixtures': mixes, 'learner_loss': learner, 'expert_losses': cum,
            'regret_vs_expert': regret, 'best_expert': best, 'final_weights': w}

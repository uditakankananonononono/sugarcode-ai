"""Row 257, Regret Minimization: full-information regret matching (exact).

Hart and Mas-Colell regret matching over n actions. Each round the policy p is
proportional to the positive parts of the cumulative regrets (uniform when no
regret is positive). The round's payoff vector u in [0, 1]^n is then revealed and
regret R_i += u_i - p . u. Exact Fractions throughout. Reported: the policy used
each round, the learner's expected payoff each round and in total, the cumulative
regrets, the average policy, and the largest cumulative regret (external regret).
Caps: 1 to 5 actions, 1 to 10 rounds (exact fractions double in size each round,
so the round cap is low on purpose), payoffs nonbool int or Fraction with
numerator and denominator at most 32 bits, in [0, 1]. Order of checks: the round cap first, then row
types and the first-row action cap (at most 10 cheap type checks), then every value
is converted to a Fraction and checked against the 32-bit and range rules, and only
then is any arithmetic done. An oversized int is converted to a Fraction just before
its bit-length check (bounded cost, no arithmetic on it).

NOT_CLAIMED: only the update rule and exact bookkeeping. No sublinear regret
bound is checked or asserted; payoffs are caller inputs and are not verified;
not a real-world outcome claim; no clinical or wet-lab claim.
"""
from fractions import Fraction

MAX_ACTIONS, MAX_ROUNDS = 5, 10


def _q(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def regret_matching(payoffs):
    if type(payoffs) not in (list, tuple):
        raise TypeError('payoffs must be a list or tuple of rounds')
    T = len(payoffs)
    if not 1 <= T <= MAX_ROUNDS:
        raise ValueError('rounds must be between 1 and 10')
    for row in payoffs:
        if type(row) not in (list, tuple):
            raise TypeError('payoffs must be a list or tuple of rounds')
    n = len(payoffs[0])
    if not 1 <= n <= MAX_ACTIONS:
        raise ValueError('actions must be between 1 and 5')
    if any(len(row) != n for row in payoffs):
        raise ValueError('every round must have the same number of actions')
    U = [[_q(v) for v in row] for row in payoffs]
    if any(v < 0 or v > 1 for row in U for v in row):
        raise ValueError('payoffs must be in [0, 1]')
    R = [Fraction(0)] * n
    policies, earned, total = [], [], Fraction(0)
    for u in U:
        pos = [max(r, 0) for r in R]
        s = sum(pos)
        p = [Fraction(1, n)] * n if s == 0 else [v / s for v in pos]
        policies.append(p)
        got = sum(p[i] * u[i] for i in range(n))
        earned.append(got)
        total += got
        R = [R[i] + u[i] - got for i in range(n)]
    avg = [sum(p[i] for p in policies) / T for i in range(n)]
    return {'policies': policies, 'round_payoffs': earned, 'total_payoff': total,
            'cumulative_regret': R, 'average_policy': avg, 'external_regret': max(R)}

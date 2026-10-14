"""Row 252: Bandit Algorithms - Balances exploration and exploitation.

Exact epsilon-greedy finite-arm sequential replay. Each supplied uniform
rational ticket u in [0,1) chooses exploration when u<epsilon; conditional
exploration selects floor(k*u/epsilon). Unseen arms are sampled first.
Only the chosen arm's supplied reward updates its empirical mean.
NOT_CLAIMED: random ticket generation, reward acquisition, regret guarantees,
contextual or adversarial bandits, optimal epsilon selection, biological validity.
"""
from fractions import Fraction


def _scalar(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length() > 32:
            raise ValueError('rational values must fit 32 bits')
    elif v.numerator.bit_length() > 32 or v.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return Fraction(v)


def epsilon_greedy_replay(arm_count, tickets, rewards, epsilon=Fraction(1,10)):
    if type(arm_count) is not int or not 1 <= arm_count <= 16:
        raise ValueError('arm_count must be a nonbool integer between 1 and 16')
    if type(tickets) not in (list, tuple) or type(rewards) not in (list, tuple):
        raise TypeError('tickets and rewards must be lists or tuples')
    if not 1 <= len(tickets) <= 256:
        raise ValueError('round count must be between 1 and 256')
    if len(rewards) != len(tickets):
        raise ValueError('tickets and rewards must have equal length')
    us = [_scalar(v) for v in tickets]
    rs = [_scalar(v) for v in rewards]
    eps = _scalar(epsilon)
    if not 0 <= eps <= 1:
        raise ValueError('epsilon must be between zero and one')
    if any(not 0 <= u < 1 for u in us):
        raise ValueError('tickets must be at least zero and less than one')
    if any(not 0 <= r <= 1 for r in rs):
        raise ValueError('rewards must be between zero and one')
    counts = [0]*arm_count
    totals = [Fraction(0)]*arm_count
    trace = []
    for t, (u, reward) in enumerate(zip(us, rs), 1):
        means = [totals[i]/counts[i] if counts[i] else None for i in range(arm_count)]
        if 0 in counts:
            arm = counts.index(0)
            mode = 'initialize'
        elif u < eps:
            scaled = arm_count*u/eps
            arm = scaled.numerator // scaled.denominator
            mode = 'explore'
        else:
            arm = max(range(arm_count), key=means.__getitem__)
            mode = 'exploit'
        counts[arm] += 1
        totals[arm] += reward
        trace.append({'round': t, 'arm': arm, 'mode': mode,
                      'means_before': means, 'reward': reward})
    means = [totals[i]/counts[i] if counts[i] else None for i in range(arm_count)]
    return {'counts': counts, 'reward_totals': totals, 'means': means, 'trace': trace,
            'total_reward': sum(totals, Fraction(0)), 'regret_guarantee_claimed': False}

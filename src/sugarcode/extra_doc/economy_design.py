"""Row 339 Economy Design: finite virtual-economy faucet/sink balance selection (exact).

Each faucet (currency source) and each sink (currency drain) has 1 to 4 candidate
rates, in currency units per player per day. One rate is chosen per faucet and per
sink. Net flow = total faucet rate - total sink rate. The selection minimizes
|net - target_net|; ties go to the smaller faucet total, then to the first
candidate in option order. Also reports the projected change in total circulating
supply = net * players * days. All arithmetic is exact (Fraction).
Caps: at most 6 faucets plus sinks in total, 4 options each, 4096 candidates;
players 1..1000000; days 1..3650. Rates, target and counts are nonbool int or
Fraction (no float), numerator and denominator at most 32 bits. Rates are
nonnegative; target_net may be negative. Caps are implementation choices, not spec values.
NOT_CLAIMED: a healthy or fair economy, player behavior or retention, inflation
beyond this one flow identity, price discovery, market or trading dynamics,
monetization, real-money or legal/regulatory advice, human playtesting, deployment.
"""
from fractions import Fraction
from itertools import product

NOT_CLAIMED = ('healthy or fair economy', 'player behavior or retention', 'price discovery',
               'market or trading dynamics', 'monetization', 'real-money or legal advice',
               'human playtesting', 'deployment')
MAX_GROUPS = 6
MAX_OPTIONS = 4
MAX_PLAYERS = 1000000
MAX_DAYS = 3650


def _number(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length() > 32:
            raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length() > 32 or v.denominator.bit_length() > 32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def balance_economy(faucets, sinks, players, days, target_net=0):
    for name, groups in (('faucets', faucets), ('sinks', sinks)):
        if type(groups) not in (list, tuple):
            raise TypeError(name + ' must be a list or tuple')
    if not 1 <= len(faucets) + len(sinks) <= MAX_GROUPS:
        raise ValueError('faucet and sink count together must be between 1 and 6')
    for options in tuple(faucets) + tuple(sinks):
        if type(options) not in (list, tuple) or not 1 <= len(options) <= MAX_OPTIONS:
            raise ValueError('each faucet and sink must have between 1 and 4 rate options')
    if type(players) is not int or type(days) is not int:
        raise TypeError('players and days must be nonbool int')
    if not 1 <= players <= MAX_PLAYERS:
        raise ValueError('players must be between 1 and 1000000')
    if not 1 <= days <= MAX_DAYS:
        raise ValueError('days must be between 1 and 3650')
    target = _number(target_net)
    f_rates = [[_number(v) for v in options] for options in faucets]
    s_rates = [[_number(v) for v in options] for options in sinks]
    if any(v < 0 for opts in f_rates + s_rates for v in opts):
        raise ValueError('rates must be nonnegative')
    groups = f_rates + s_rates
    nf = len(f_rates)
    best = None
    for idx in product(*(range(len(g)) for g in groups)):
        fsum = sum((groups[i][j] for i, j in enumerate(idx[:nf])), Fraction(0))
        ssum = sum((groups[nf + i][j] for i, j in enumerate(idx[nf:])), Fraction(0))
        net = fsum - ssum
        gap = abs(net - target)
        if best is None or (gap, fsum) < (best[0], best[1]):
            best = (gap, fsum, ssum, net, idx)
    gap, fsum, ssum, net, idx = best
    return {'faucet_indices': list(idx[:nf]), 'sink_indices': list(idx[nf:]),
            'faucet_total': fsum, 'sink_total': ssum, 'net_per_player_day': net,
            'imbalance': gap, 'balanced': gap == 0,
            'projected_supply_change': net * players * days,
            'candidate_count': _count(groups),
            'economy_health_validated': False, 'not_claimed': NOT_CLAIMED}


def _count(groups):
    n = 1
    for g in groups:
        n *= len(g)
    return n

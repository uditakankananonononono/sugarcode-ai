"""Exact counting numbers, lattice paths, gambler's ruin and bounded walks on supplied small parameters.

SCOPE: every function takes nonbool ints (and, for walks, one mode string) and returns exact ints,
Fractions and lists. Ballot and lattice-path counts up to 30 by 30; simple +-1 walk statistics for
length up to 24; gambler's ruin and walk laws for a target or state count of at most 60 or 12
with step probability p_num/p_den (0 < p < 1, p_den up to 100); dice sums for up to 10 dice of up to 12 sides.
Adjacent to, but not overlapping, a separate sequences module (Stirling, Bell, Catalan and similar named
sequences); this module has no named-sequence functions.

Order of checks: arguments left to right as written in each signature. Ints: nonbool int type
first (TypeError), then range (ValueError). Mode: exact str type, then membership. Caps are checked
before any computation or allocation that depends on them.

Definitions: a simple walk has n steps of +1 or -1 from 0, all 2**n sequences. ballot_count(a, b) counts sequences of a up-steps and b down-steps whose running sum never drops
below 0. lattice_paths_under_slope(m, n, p, q) counts monotone right/up paths from (0,0) to (m,n)
that stay on or below the line y = (p/q) x at every visited point (y*q <= x*p). In the gambler's
ruin the gambler starts with `start`, wins 1 with probability p, loses 1 otherwise, and stops at 0
or at `target`. bounded_walk_distribution uses states 0..states-1 and p as the step-up probability;
mode 'absorbing' keeps the walker at an end state, mode 'reflecting' moves it one step inward with
probability 1 from an end state. dice_sum_distribution returns the count of outcomes for each total
from n_dice to n_dice*sides.

Every result dict carries 'claims', all False.

NOT_CLAIMED: arithmetic on the supplied parameters only. It makes no claim about gambling odds in
any real game, casino, market or population, no fairness or randomness claim, and no forecast.
"""
from fractions import Fraction

CLAIMS = {
    'gambling_advice': False,
    'real_world_odds': False,
    'randomness': False,
    'forecast': False,
}


def _int(v, name, lo, hi):
    if type(v) is not int:
        raise TypeError(name + ' must be a nonbool int')
    if v < lo or v > hi:
        raise ValueError('%s must be between %d and %d' % (name, lo, hi))
    return v


def _res(**kw):
    kw['claims'] = dict(CLAIMS)
    return kw


def _p(p_num, p_den):
    _int(p_den, 'p_den', 1, 100)
    _int(p_num, 'p_num', 1, p_den - 1)
    return Fraction(p_num, p_den)


def ballot_count(a, b):
    """Up/down sequences with a ups and b downs that never go below zero."""
    _int(a, 'a', 0, 30)
    _int(b, 'b', 0, 30)
    ways = [[0] * (b + 1) for _ in range(a + 1)]
    ways[0][0] = 1
    for i in range(a + 1):
        for j in range(b + 1):
            if (i, j) == (0, 0) or j > i:
                continue
            ways[i][j] = (ways[i - 1][j] if i else 0) + (ways[i][j - 1] if j else 0)
    return _res(a=a, b=b, count=ways[a][b])


def lattice_paths_under_slope(m, n, p, q):
    """Monotone paths (0,0) to (m,n) staying on or below y = (p/q) x."""
    _int(m, 'm', 0, 30)
    _int(n, 'n', 0, 30)
    _int(p, 'p', 1, 5)
    _int(q, 'q', 1, 5)
    w = [[0] * (n + 1) for _ in range(m + 1)]
    for x in range(m + 1):
        for y in range(n + 1):
            if y * q > x * p:
                continue
            if (x, y) == (0, 0):
                w[x][y] = 1
            else:
                w[x][y] = (w[x - 1][y] if x else 0) + (w[x][y - 1] if y else 0)
    return _res(m=m, n=n, count=w[m][n])


def gamblers_ruin_probability(start, target, p_num, p_den):
    """Probability of reaching target before 0, starting at `start`."""
    _int(target, 'target', 1, 60)
    _int(start, 'start', 0, target)
    p = _p(p_num, p_den)
    q = 1 - p
    if p == q:
        win = Fraction(start, target)
    else:
        r = q / p
        win = (1 - r ** start) / (1 - r ** target)
    return _res(start=start, target=target, win=win, ruin=1 - win)


def gamblers_ruin_expected_duration(start, target, p_num, p_den):
    """Expected number of rounds until the gambler stops."""
    _int(target, 'target', 1, 60)
    _int(start, 'start', 0, target)
    p = _p(p_num, p_den)
    q = 1 - p
    if p == q:
        d = Fraction(start * (target - start))
    else:
        r = q / p
        win = (1 - r ** start) / (1 - r ** target)
        d = Fraction(start, 1) / (q - p) - Fraction(target, 1) / (q - p) * win
    return _res(start=start, target=target, duration=d)


def bounded_walk_distribution(states, start, steps, mode, p_num, p_den):
    """Exact law after `steps` steps of a walk on states 0..states-1."""
    _int(states, 'states', 2, 12)
    _int(start, 'start', 0, states - 1)
    _int(steps, 'steps', 0, 60)
    if type(mode) is not str:
        raise TypeError('mode must be an exact str')
    if mode not in ('absorbing', 'reflecting'):
        raise ValueError("mode must be 'absorbing' or 'reflecting'")
    p = _p(p_num, p_den)
    q = 1 - p
    law = [Fraction(0)] * states
    law[start] = Fraction(1)
    for _ in range(steps):
        new = [Fraction(0)] * states
        for i, pr in enumerate(law):
            if not pr:
                continue
            if i == 0:
                if mode == 'absorbing':
                    new[0] += pr
                else:
                    new[1] += pr
            elif i == states - 1:
                if mode == 'absorbing':
                    new[i] += pr
                else:
                    new[i - 1] += pr
            else:
                new[i + 1] += pr * p
                new[i - 1] += pr * q
        law = new
    return _res(states=states, steps=steps, mode=mode, law=law)


def dice_sum_distribution(n_dice, sides):
    """Counts of outcomes for each total of n_dice dice with `sides` faces."""
    _int(n_dice, 'n_dice', 1, 10)
    _int(sides, 'sides', 1, 12)
    dist = {0: 1}
    for _ in range(n_dice):
        new = {}
        for s, c in dist.items():
            for f in range(1, sides + 1):
                new[s + f] = new.get(s + f, 0) + c
        dist = new
    return _res(n_dice=n_dice, sides=sides, totals=sorted(dist.items()))


def walk_max_distribution(n):
    """For simple +-1 walks of n steps, sorted (maximum height reached, number of walks)."""
    _int(n, 'n', 0, 24)
    cur = {(0, 0): 1}
    for _ in range(n):
        nxt = {}
        for (pos, mx), c in cur.items():
            for d in (1, -1):
                k = (pos + d, max(mx, pos + d))
                nxt[k] = nxt.get(k, 0) + c
        cur = nxt
    out = {}
    for (_, mx), c in cur.items():
        out[mx] = out.get(mx, 0) + c
    return _res(n=n, maxima=sorted(out.items()))


def walk_return_count_distribution(n):
    """Sorted (number of returns to 0 at times 1..n, number of walks) for simple walks."""
    _int(n, 'n', 0, 24)
    cur = {(0, 0): 1}
    for _ in range(n):
        nxt = {}
        for (pos, r), c in cur.items():
            for d in (1, -1):
                k = (pos + d, r + (pos + d == 0))
                nxt[k] = nxt.get(k, 0) + c
        cur = nxt
    out = {}
    for (_, r), c in cur.items():
        out[r] = out.get(r, 0) + c
    return _res(n=n, returns=sorted(out.items()))


def walk_hit_level_count(n, level):
    """Number of simple n-step walks that reach height `level` at some step (level >= 1)."""
    _int(n, 'n', 0, 24)
    _int(level, 'level', 1, 24)
    ends = {0: 1}
    hit = 0
    for t in range(n):
        nxt = {}
        for pos, c in ends.items():
            for d in (1, -1):
                if pos + d == level:
                    hit += c * 2 ** (n - 1 - t)
                else:
                    nxt[pos + d] = nxt.get(pos + d, 0) + c
        ends = nxt
    return _res(n=n, level=level, count=hit)


def ruin_stopping_time_distribution(start, target, p_num, p_den, steps):
    """P(the gambler stops exactly at round t) for t = 0..steps, and P(still playing after steps)."""
    _int(target, 'target', 1, 20)
    _int(start, 'start', 0, target)
    p = _p(p_num, p_den)
    _int(steps, 'steps', 0, 60)
    q = 1 - p
    law = [Fraction(0)] * (target + 1)
    law[start] = Fraction(1)
    dist = [law[0] + law[target]]
    prev = dist[0]
    for _t in range(steps):
        new = [Fraction(0)] * (target + 1)
        new[0], new[target] = law[0], law[target]
        for i in range(1, target):
            new[i + 1] += law[i] * p
            new[i - 1] += law[i] * q
        law = new
        total = law[0] + law[target]
        dist.append(total - prev)
        prev = total
    return _res(start=start, target=target, steps=steps, stop_at=dist, still_playing=1 - prev)

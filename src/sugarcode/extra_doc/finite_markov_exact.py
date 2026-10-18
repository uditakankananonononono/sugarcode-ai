"""Exact analysis of a finite Markov chain given by a supplied table of nonnegative weights.

SCOPE: W is an n x n table (n from 1 to 7) of built-in ints 0..1000 given as a list or tuple
of rows. Row i is divided by its sum, which must be positive, to give the transition
probabilities P[i][j] as Fractions. States are 0..n-1. All results are exact: ints, Fractions
(or None where a quantity is infinite or undefined) and sorted lists. A class is a set of
mutually reachable states; it is closed when no positive-weight edge leaves it, otherwise
transient. The period of a closed class is the gcd of its cycle lengths.

Order of checks, then computation, for every function: W is checked first (container type,
row count 1..7 before any row is read, then each row in order: row type, row length, each
entry's nonbool int type then its range, then the row sum), then the remaining arguments left
to right (targets or partition: container type, count before entries, entry types before
ranges, duplicates, coverage; start then k as nonbool ints, then ranges). Nothing is computed
before every check has passed.

hitting_probabilities and mean_first_passage_times take a nonempty set of distinct target
states; the mean first passage time is None where the target is not reached with
probability 1, and 0 on targets. total_variation_to_stationary needs an irreducible aperiodic
chain.

Every result dict carries 'claims', all False.

NOT_CLAIMED: arithmetic on one supplied table. It estimates nothing from data, makes no
forecast, no modeling-adequacy, convergence-rate, mixing-time-bound, Monte Carlo or
real-world process claim.
"""
from fractions import Fraction
from math import gcd

MAX_N = 7
MAX_W = 1000
MAX_K = 64
CLAIMS = {
    'forecast': False,
    'estimation_from_data': False,
    'model_adequacy': False,
    'mixing_time_bound': False,
}


def _int(v, name, lo, hi):
    if type(v) is not int:
        raise TypeError(name + ' must be a nonbool int')
    if v < lo or v > hi:
        raise ValueError('%s must be between %d and %d' % (name, lo, hi))
    return v


def _chain(W):
    if type(W) not in (list, tuple):
        raise TypeError('W must be a list or tuple')
    n = len(W)
    if n < 1 or n > MAX_N:
        raise ValueError('W row count must be between 1 and 7')
    P = []
    for row in W:
        if type(row) not in (list, tuple):
            raise TypeError('W rows must be lists or tuples')
        if len(row) != n:
            raise ValueError('W row length must equal the row count')
        for v in row:
            if type(v) is not int:
                raise TypeError('W entries must be nonbool int')
            if v < 0 or v > MAX_W:
                raise ValueError('W entries must be between 0 and 1000')
        s = sum(row)
        if s <= 0:
            raise ValueError('W row sums must be positive')
        P.append([Fraction(v, s) for v in row])
    return n, P


def _set(vals, n, name, lo_len=1):
    if type(vals) not in (list, tuple):
        raise TypeError(name + ' must be a list or tuple')
    if len(vals) < lo_len or len(vals) > n:
        raise ValueError('%s length must be between %d and %d' % (name, lo_len, n))
    for v in vals:
        if type(v) is not int:
            raise TypeError(name + ' entries must be nonbool int')
        if v < 0 or v >= n:
            raise ValueError('%s entries must be between 0 and %d' % (name, n - 1))
    if len(set(vals)) != len(vals):
        raise ValueError(name + ' entries must be distinct')
    return list(vals)


def _res(**kw):
    kw['claims'] = dict(CLAIMS)
    return kw


def _reach(P, n):
    """reach[i] = set of states reachable from i in zero or more steps (BFS)."""
    out = []
    for s in range(n):
        seen = {s}
        stack = [s]
        while stack:
            u = stack.pop()
            for v in range(n):
                if P[u][v] and v not in seen:
                    seen.add(v)
                    stack.append(v)
        out.append(seen)
    return out


def _classes(P, n):
    reach = _reach(P, n)
    done = set()
    out = []
    for s in range(n):
        if s in done:
            continue
        cls = sorted(j for j in reach[s] if s in reach[j])
        done.update(cls)
        closed = all(P[u][v] == 0 for u in cls for v in range(n) if v not in cls)
        out.append((cls, closed))
    return out, reach


def _solve(A, B):
    """Solve A X = B for square A (Fractions) by Gauss-Jordan elimination."""
    m = len(A)
    M = [list(A[i]) + list(B[i]) for i in range(m)]
    w = len(M[0]) if m else 0
    for c in range(m):
        piv = next(r for r in range(c, m) if M[r][c] != 0)
        M[c], M[piv] = M[piv], M[c]
        inv = 1 / M[c][c]
        M[c] = [x * inv for x in M[c]]
        for r in range(m):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [row[m:w] for row in M]


def _imq(P, idx):
    return [[(1 if a == b else 0) - P[i][j] for b, j in enumerate(idx)] for a, i in enumerate(idx)]


def communicating_classes(W):
    """Sorted communicating classes, each with its states and a closed flag."""
    n, P = _chain(W)
    cl, _ = _classes(P, n)
    return _res(n=n, classes=[{'states': c, 'closed': k} for c, k in cl])


def class_periods(W):
    """Period of each closed class (gcd of cycle lengths, from BFS levels)."""
    n, P = _chain(W)
    cl, _ = _classes(P, n)
    out = []
    for cls, closed in cl:
        if not closed:
            continue
        level = {cls[0]: 0}
        order = [cls[0]]
        for u in order:
            for v in cls:
                if P[u][v] and v not in level:
                    level[v] = level[u] + 1
                    order.append(v)
        g = 0
        for u in cls:
            for v in cls:
                if P[u][v]:
                    g = gcd(g, level[u] + 1 - level[v])
        out.append({'states': cls, 'period': g})
    return _res(n=n, periods=out)


def _transient(P, n):
    cl, _ = _classes(P, n)
    closed = [c for c, k in cl if k]
    trans = sorted(s for c, k in cl if not k for s in c)
    return closed, trans


def fundamental_matrix(W):
    """N = (I - Q)**-1 over the transient states (sorted), Q the transient-to-transient block."""
    n, P = _chain(W)
    _, trans = _transient(P, n)
    ident = [[Fraction(int(a == b)) for b in range(len(trans))] for a in range(len(trans))]
    N = _solve(_imq(P, trans), ident) if trans else []
    return _res(n=n, transient=trans, matrix=N)


def absorption_probabilities(W):
    """Per transient state (sorted), the probability of ending in each closed class."""
    n, P = _chain(W)
    closed, trans = _transient(P, n)
    if not trans:
        return _res(n=n, transient=[], closed_classes=closed, probabilities=[])
    R = [[sum(P[i][j] for j in c) for c in closed] for i in trans]
    return _res(n=n, transient=trans, closed_classes=closed, probabilities=_solve(_imq(P, trans), R))


def expected_steps_to_absorption(W):
    """Expected steps until a closed class is entered, per transient state (sorted)."""
    n, P = _chain(W)
    _, trans = _transient(P, n)
    if not trans:
        return _res(n=n, transient=[], steps=[])
    X = _solve(_imq(P, trans), [[Fraction(1)] for _ in trans])
    return _res(n=n, transient=trans, steps=[r[0] for r in X])


def stationary_distributions(W):
    """One exact stationary distribution per closed class, over that class's states."""
    n, P = _chain(W)
    closed, _ = _transient(P, n)
    out = []
    for c in closed:
        m = len(c)
        A = [[(1 if a == b else 0) - P[c[b]][c[a]] for b in range(m)] for a in range(m)]
        A[m - 1] = [Fraction(1)] * m
        rhs = [[Fraction(0)] for _ in range(m)]
        rhs[m - 1] = [Fraction(1)]
        pi = [r[0] for r in _solve(A, rhs)]
        out.append({'states': c, 'distribution': pi})
    return _res(n=n, distributions=out, unique=len(closed) == 1)


def _hit(P, n, targets, reach):
    tset = set(targets)
    h = [Fraction(0)] * n
    for t in tset:
        h[t] = Fraction(1)
    u = [i for i in range(n) if i not in tset and reach[i] & tset]
    if u:
        r = [[sum(P[i][t] for t in tset)] for i in u]
        x = _solve(_imq(P, u), r)
        for i, row in zip(u, x):
            h[i] = row[0]
    return h


def hitting_probabilities(W, targets):
    """Probability of ever reaching the target set, from every state."""
    n, P = _chain(W)
    tg = _set(targets, n, 'targets')
    return _res(n=n, targets=sorted(tg), probabilities=_hit(P, n, tg, _reach(P, n)))


def mean_first_passage_times(W, targets):
    """Expected steps to reach the target set; 0 on targets, None where not certain."""
    n, P = _chain(W)
    tg = _set(targets, n, 'targets')
    h = _hit(P, n, tg, _reach(P, n))
    tset = set(tg)
    v = [i for i in range(n) if i not in tset and h[i] == 1]
    out = [None] * n
    for t in tset:
        out[t] = Fraction(0)
    if v:
        x = _solve(_imq(P, v), [[Fraction(1)] for _ in v])
        for i, row in zip(v, x):
            out[i] = row[0]
    return _res(n=n, targets=sorted(tg), times=out)


def _blocks(part, n):
    if type(part) not in (list, tuple):
        raise TypeError('partition must be a list or tuple')
    if len(part) < 1 or len(part) > n:
        raise ValueError('partition block count must be between 1 and %d' % n)
    blocks = []
    seen = set()
    for b in part:
        if type(b) not in (list, tuple):
            raise TypeError('partition blocks must be lists or tuples')
        if len(b) < 1 or len(b) > n:
            raise ValueError('partition block length must be between 1 and %d' % n)
        for v in b:
            if type(v) is not int:
                raise TypeError('partition entries must be nonbool int')
            if v < 0 or v >= n:
                raise ValueError('partition entries must be between 0 and %d' % (n - 1))
            if v in seen:
                raise ValueError('partition entries must be distinct')
            seen.add(v)
        blocks.append(list(b))
    if len(seen) != n:
        raise ValueError('partition must cover every state')
    return blocks


def is_strongly_lumpable(W, partition):
    """Dynkin test: every state of a block sends the same total probability to each block."""
    n, P = _chain(W)
    blocks = _blocks(partition, n)
    lumped = []
    ok = True
    for A in blocks:
        row = None
        for i in A:
            r = [sum(P[i][j] for j in B) for B in blocks]
            if row is None:
                row = r
            elif r != row:
                ok = False
        lumped.append(row)
    return _res(n=n, lumpable=ok, lumped_matrix=lumped if ok else None)


def total_variation_to_stationary(W, start, k):
    """Exact total variation distance between the k-step law from start and the stationary law."""
    n, P = _chain(W)
    _int(start, 'start', 0, n - 1)
    _int(k, 'k', 0, MAX_K)
    cl, _ = _classes(P, n)
    if len(cl) != 1 or not cl[0][1] or class_periods(W)['periods'][0]['period'] != 1:
        raise ValueError('chain must be irreducible and aperiodic')
    pi = stationary_distributions(W)['distributions'][0]['distribution']
    mu = [Fraction(int(i == start)) for i in range(n)]
    for _ in range(k):
        mu = [sum(mu[i] * P[i][j] for i in range(n)) for j in range(n)]
    return _res(n=n, tv=sum(abs(a - b) for a, b in zip(mu, pi)) / 2, distribution=mu, stationary=pi)

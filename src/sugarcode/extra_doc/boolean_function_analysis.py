"""Exact analysis of a Boolean function given as a supplied truth table.

SCOPE: the caller supplies a truth table f: {0,1}^n -> {0,1} as a list or tuple of
2**n built-in ints 0/1, with n between 1 and 8. Index x of the table holds f(x); bit i of
x (least significant bit first) is variable i. Every result is computed exactly on
ints and Fractions from that table alone: Walsh spectrum, algebraic normal form,
algebraic degree, nonlinearity, variable influences, total influence, sensitivity,
unateness, balance with correlation-immunity order, and symmetry.

Order of checks, then computation: container type (list or tuple, exact type), length
(2**n, n from 1 to 8, so 2 to 256 entries; checked before any entry is read), then each
entry in index order: nonbool int type first, then the value 0 or 1. Nothing is
materialized before these checks pass.

Conventions: the degree of a constant function is 0. correlation_immunity_order is the
largest m in 0..n such that every nonzero Walsh coefficient index of weight 1..m is
zero; resilience_order is that order when the function is balanced and -1 otherwise.

Every result dict carries 'claims', all False.

NOT_CLAIMED: this is arithmetic on one supplied table. It makes no cryptographic
strength, security, randomness, hardware, biological or regulatory-network claim, does
not derive a table from any circuit or network, and does not reach beyond n = 8.
"""
from fractions import Fraction

MAX_VARS = 8
CLAIMS = {
    'cryptographic_strength': False,
    'security': False,
    'randomness': False,
    'biological_network_model': False,
}


def _table(table):
    if type(table) not in (list, tuple):
        raise TypeError('table must be a list or tuple')
    size = len(table)
    if size < 2 or size > 1 << MAX_VARS or size & (size - 1):
        raise ValueError('table length must be 2**n with n between 1 and 8')
    for v in table:
        if type(v) is not int:
            raise TypeError('table entries must be nonbool int')
        if v != 0 and v != 1:
            raise ValueError('table entries must be 0 or 1')
    return list(table), size.bit_length() - 1


def _wht(vals):
    a = list(vals)
    h = 1
    while h < len(a):
        for i in range(0, len(a), 2 * h):
            for j in range(i, i + h):
                x, y = a[j], a[j + h]
                a[j], a[j + h] = x + y, x - y
        h *= 2
    return a


def _walsh(t):
    return _wht([1 - 2 * v for v in t])


def _anf(t):
    c = list(t)
    h = 1
    while h < len(c):
        for i in range(0, len(c), 2 * h):
            for j in range(i, i + h):
                c[j + h] ^= c[j]
        h *= 2
    return c


def _pop(x):
    return bin(x).count('1')


def _result(**kw):
    kw['claims'] = dict(CLAIMS)
    return kw


def walsh_spectrum(table):
    """W(a) = sum over x of (-1)**(f(x) xor a.x) for every a."""
    t, n = _table(table)
    return _result(n=n, spectrum=_walsh(t))


def algebraic_normal_form(table):
    """GF(2) polynomial coefficients; coefficient u belongs to the monomial of bits in u."""
    t, n = _table(table)
    c = _anf(t)
    return _result(n=n, coefficients=c, monomials=[u for u in range(len(c)) if c[u]])


def algebraic_degree(table):
    """Largest monomial size in the algebraic normal form (0 for a constant function)."""
    t, n = _table(table)
    c = _anf(t)
    return _result(n=n, degree=max([_pop(u) for u in range(len(c)) if c[u]] + [0]))


def nonlinearity(table):
    """Least Hamming distance from the table to any affine function."""
    t, n = _table(table)
    top = max(abs(w) for w in _walsh(t))
    return _result(n=n, nonlinearity=(1 << (n - 1)) - top // 2, max_abs_walsh=top)


def variable_influences(table):
    """Inf_i = Fraction of the 2**n inputs whose flip of variable i changes f."""
    t, n = _table(table)
    size = len(t)
    inf = [Fraction(sum(t[x] != t[x ^ (1 << i)] for x in range(size)), size) for i in range(n)]
    return _result(n=n, influences=inf)


def total_influence(table):
    """Sum of the variable influences, exactly, as a Fraction."""
    t, n = _table(table)
    size = len(t)
    flips = sum(t[x] != t[x ^ (1 << i)] for i in range(n) for x in range(size))
    return _result(n=n, total_influence=Fraction(flips, size))


def sensitivity_profile(table):
    """Per-input sensitivity (flipped bits that change f), its maximum and exact mean."""
    t, n = _table(table)
    s = [sum(t[x] != t[x ^ (1 << i)] for i in range(n)) for x in range(len(t))]
    return _result(n=n, sensitivities=s, max_sensitivity=max(s),
                   average_sensitivity=Fraction(sum(s), len(s)))


def unate_profile(table):
    """Per variable: 'constant', 'increasing', 'decreasing' or 'binate'; unate if none binate."""
    t, n = _table(table)
    dirs = []
    for i in range(n):
        up = down = False
        for x in range(len(t)):
            if not x >> i & 1:
                d = t[x | 1 << i] - t[x]
                up = up or d > 0
                down = down or d < 0
        dirs.append('binate' if up and down else 'increasing' if up else 'decreasing' if down else 'constant')
    return _result(n=n, directions=dirs, unate='binate' not in dirs,
                   monotone_increasing=all(d in ('constant', 'increasing') for d in dirs))


def balance_and_immunity(table):
    """Balance, correlation-immunity order and resilience order via the Walsh spectrum."""
    t, n = _table(table)
    w = _walsh(t)
    order = 0
    while order < n and all(w[a] == 0 for a in range(1, len(w)) if _pop(a) == order + 1):
        order += 1
    balanced = w[0] == 0
    return _result(n=n, balanced=balanced, correlation_immunity_order=order,
                   resilience_order=order if balanced else -1)


def symmetric_profile(table):
    """Whether f depends only on the Hamming weight of x, with the value for each weight."""
    t, n = _table(table)
    by_weight = {}
    ok = True
    for x in range(len(t)):
        if by_weight.setdefault(_pop(x), t[x]) != t[x]:
            ok = False
            break
    return _result(n=n, symmetric=ok, values_by_weight=[by_weight[k] for k in range(n + 1)] if ok else None)

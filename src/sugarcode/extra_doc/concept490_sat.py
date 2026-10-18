"""Exact bounded CNF fixtures, not a general SAT service.

n exact int0..10; CNF exact tuple<=8 clauses, each exact tuple<=10
signed literals. Literal abs1..n, exact int, no duplicate variables within
one clause (including opposite signs). Duplicate clauses refused. Empty
CNF and empty clause allowed. Canonical outputs sort literals by abs then
sign and clauses lexicographically. Assignment masks exact int0..2**n-1.
Validation order n, outer type/length, all clause shapes/lengths, all scalar
types, all scalar ranges, clause variable uniqueness, clause uniqueness.
Partial assignments exact tuple<=n distinct signed variables, same rules.
No symbolic strings, file reads, network, randomization or solver packages.
"""
from itertools import combinations
SCOPE = 'PARTIAL exact finite CNF counting, conditioning and certificates'
NOT_CLAIMED = ('AGI-like intelligence', 'unbounded SAT solving', 'production readiness', 'proof-system completeness')
CLAIMS = {'agi_like_intelligence': False, 'production_ready': False, 'unbounded_solver': False}


def _fail(code):
    raise ValueError('S490:' + code)


def _n(n):
    if type(n) is not int:
        _fail('type:n')
    if not 0 <= n <= 10:
        _fail('bound:n')


def _canon(clauses):
    return tuple(sorted(set(tuple(sorted(c, key=lambda x: (abs(x), x))) for c in clauses)))


def _cnf(n, cnf):
    _n(n)
    if type(cnf) is not tuple:
        _fail('type:cnf')
    if len(cnf) > 8:
        _fail('length:cnf')
    if any(type(c) is not tuple for c in cnf):
        _fail('type:clause')
    if any(len(c) > 10 for c in cnf):
        _fail('length:clause')
    if any(type(x) is not int for c in cnf for x in c):
        _fail('type:literal')
    if any(not 1 <= abs(x) <= n for c in cnf for x in c):
        _fail('bound:literal')
    if any(len(set(map(abs, c))) != len(c) for c in cnf):
        _fail('duplicate:variable')
    result = _canon(cnf)
    if len(result) != len(cnf):
        _fail('duplicate:clause')
    return result


def _partial(n, partial):
    if type(partial) is not tuple:
        _fail('type:partial')
    if len(partial) > n:
        _fail('length:partial')
    if any(type(x) is not int for x in partial):
        _fail('type:partial:literal')
    if any(not 1 <= abs(x) <= n for x in partial):
        _fail('bound:partial:literal')
    if len(set(map(abs, partial))) != len(partial):
        _fail('duplicate:partial')


def _eval(cnf, mask):
    return all(any(bool(mask & (1 << (abs(x)-1))) == (x > 0) for x in c) for c in cnf)


def _apply(cnf, literal):
    return _canon(tuple(tuple(x for x in c if x != -literal) for c in cnf if literal not in c))


def _propagate(cnf, fixed):
    fixed = dict(fixed)
    while True:
        if () in cnf:
            return None
        units = sorted((c[0] for c in cnf if len(c) == 1), key=lambda x: (abs(x), x))
        if not units:
            return cnf, fixed
        literal = units[0]
        variable, value = abs(literal), literal > 0
        if variable in fixed and fixed[variable] != value:
            return None
        fixed[variable] = value
        cnf = _apply(cnf, literal)


def _count(n, cnf, fixed):
    propagated = _propagate(cnf, fixed)
    if propagated is None:
        return 0
    cnf, fixed = propagated
    if not cnf:
        return 1 << (n-len(fixed))
    variable = min(abs(x) for c in cnf for x in c)
    total = 0
    for literal in (-variable, variable):
        next_fixed = dict(fixed)
        next_fixed[variable] = literal > 0
        total += _count(n, _apply(cnf, literal), next_fixed)
    return total


def sat_evaluate(n, cnf, mask):
    """Boolean truth value at a complete assignment mask."""
    cnf = _cnf(n, cnf)
    if type(mask) is not int:
        _fail('type:mask')
    if not 0 <= mask < (1 << n):
        _fail('bound:mask')
    return _eval(cnf, mask)


def sat_models(n, cnf):
    """All satisfying masks in increasing order, at most1024."""
    cnf = _cnf(n, cnf)
    return tuple(mask for mask in range(1 << n) if _eval(cnf, mask))


def sat_count(n, cnf):
    """Exact DPLL model count with free-variable factor, no table enumeration."""
    return _count(n, _cnf(n, cnf), {})


def sat_restrict(n, cnf, partial):
    """Condition CNF on supplied signed literals; variables retain indices."""
    cnf = _cnf(n, cnf)
    _partial(n, partial)
    for literal in partial:
        cnf = _apply(cnf, literal)
    return cnf


def sat_unit_propagate(n, cnf):
    """Return (canonical residual, sorted forced literals), or None on conflict.

    Forced literals only from unit propagation, not every logical consequence.
    """
    result = _propagate(_cnf(n, cnf), {})
    if result is None:
        return None
    residual, fixed = result
    return residual, tuple(a if v else -a for a, v in sorted(fixed.items()))


def sat_backbone(n, cnf):
    """Forced literals via two conditional counts per variable; None if UNSAT."""
    cnf = _cnf(n, cnf)
    if not _count(n, cnf, {}):
        return None
    result = []
    for a in range(1, n+1):
        zero = _count(n, _apply(cnf, -a), {a: False})
        one = _count(n, _apply(cnf, a), {a: True})
        if not zero:
            result.append(a)
        elif not one:
            result.append(-a)
    return tuple(result)


def sat_hamming_profile(n, cnf):
    """Counts of satisfying masks by number of true variables0..n."""
    cnf = _cnf(n, cnf)
    counts = [0] * (n+1)
    for mask in range(1 << n):
        if _eval(cnf, mask):
            counts[mask.bit_count()] += 1
    return tuple(counts)


def sat_minimal_unsat_cores(n, cnf):
    """All inclusion-minimal UNSAT clause-index subsets, caller index order.

    At most256 subsets. Indices refer to caller CNF, not canonical ordering.
    """
    _cnf(n, cnf)
    cores = []
    for size in range(1, len(cnf)+1):
        for indices in combinations(range(len(cnf)), size):
            if any(set(core) <= set(indices) for core in cores):
                continue
            if not _count(n, tuple(cnf[i] for i in indices), {}):
                cores.append(indices)
    return tuple(sorted(cores))


def sat_equivalent(n, left, right):
    """Return (equivalent bool, first counterexample mask or None)."""
    left = _cnf(n, left)
    right = _cnf(n, right)
    for mask in range(1 << n):
        if _eval(left, mask) != _eval(right, mask):
            return False, mask
    return True, None


def sat_forced_implications(n, cnf):
    """All nonvacuous entailed signed-literal implications (a,b), abs(a)!=abs(b).

    An antecedent must be satisfiable with CNF. Sorted integer pair order.
    """
    cnf = _cnf(n, cnf)
    result = []
    literals = tuple(range(-n, 0)) + tuple(range(1, n+1))
    for a in literals:
        conditioned = _apply(cnf, a)
        if not _count(n, conditioned, {abs(a): a > 0}):
            continue
        for b in literals:
            if abs(a) == abs(b):
                continue
            fixed = {abs(a): a > 0, abs(b): b < 0}
            if not _count(n, _apply(conditioned, -b), fixed):
                result.append((a, b))
    return tuple(result)

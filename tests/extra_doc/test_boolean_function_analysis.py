import enum
import itertools
import random
from fractions import Fraction

import pytest

import sugarcode.extra_doc.boolean_function_analysis as m
from sugarcode.extra_doc.boolean_function_analysis import (
    algebraic_degree, algebraic_normal_form, balance_and_immunity, nonlinearity,
    sensitivity_profile, symmetric_profile, total_influence, unate_profile,
    variable_influences, walsh_spectrum)

FUNCS = [walsh_spectrum, algebraic_normal_form, algebraic_degree, nonlinearity,
         variable_influences, total_influence, sensitivity_profile, unate_profile,
         balance_and_immunity, symmetric_profile]
E_TYPE = 'table must be a list or tuple'
E_LEN = 'table length must be 2**n with n between 1 and 8'
E_ENT = 'table entries must be nonbool int'
E_VAL = 'table entries must be 0 or 1'


def pop(x):
    return bin(x).count('1')


def tables():
    """All functions for n=1..3, seeded random ones for n=4..8."""
    for n in (1, 2, 3):
        for bits in itertools.product((0, 1), repeat=1 << n):
            yield list(bits)
    rnd = random.Random(20261016)
    for n in (4, 5, 6, 7, 8):
        for k in range(40):
            p = (0.5, 0.1, 0.9, 0.5)[k % 4]
            t = [int(rnd.random() < p) for _ in range(1 << n)]
            if k % 8 == 3:
                t = [pop(x) % 2 for x in range(1 << n)]
            if k % 8 == 7:
                t = [int(pop(x) >= n // 2) for x in range(1 << n)]
            yield t


ALL = list(tables())


# ---- independent oracles (brute force or a different algorithm) ----
def o_walsh(t):
    n = len(t).bit_length() - 1
    return [sum((-1) ** (t[x] ^ (pop(a & x) & 1)) for x in range(len(t))) for a in range(1 << n)]


def o_anf(t):
    # subset-sum (inclusion-exclusion over subcube) rather than butterfly
    return [sum(t[x] for x in range(len(t)) if x & u == x) & 1 for u in range(len(t))]


def o_anf_eval(c, x):
    return sum(c[u] for u in range(len(c)) if u & x == u) & 1


def o_degree(t):
    # degree <= d iff every subcube of dimension > d has even weight
    n = len(t).bit_length() - 1
    for d in range(n + 1):
        if all(sum(t[x] for x in range(len(t)) if x & u == x) % 2 == 0
               for u in range(len(t)) if pop(u) > d):
            return d
    raise AssertionError


def o_nonlin(t):
    n = len(t).bit_length() - 1
    best = len(t)
    for a in range(1 << n):
        for c in (0, 1):
            best = min(best, sum(t[x] != ((pop(a & x) + c) & 1) for x in range(len(t))))
    return best


def o_inf_fourier(t):
    n = len(t).bit_length() - 1
    w = o_walsh(t)
    fh = [Fraction(v, len(t)) for v in w]
    return [sum(fh[s] ** 2 for s in range(len(t)) if s >> i & 1) for i in range(n)]


def o_total_fourier(t):
    w = o_walsh(t)
    return sum(pop(s) * Fraction(w[s], len(t)) ** 2 for s in range(len(t)))


def o_sens(t):
    n = len(t).bit_length() - 1
    out = []
    for x in range(len(t)):
        nb = [x ^ (1 << i) for i in range(n)]
        out.append(sum(1 for y in nb if t[y] != t[x]))
    return out


def o_unate(t):
    n = len(t).bit_length() - 1
    res = []
    for i in range(n):
        f0 = [t[x] for x in range(len(t)) if not x >> i & 1]
        f1 = [t[x] for x in range(len(t)) if x >> i & 1]
        ge = all(a >= b for a, b in zip(f1, f0))
        le = all(a <= b for a, b in zip(f1, f0))
        res.append('constant' if ge and le else 'increasing' if ge else 'decreasing' if le else 'binate')
    return res


def o_independent(t, m_):
    """Definition of m-th order correlation immunity: ones-count equal across every
    assignment of every set of m_ variables."""
    n = len(t).bit_length() - 1
    for T in itertools.combinations(range(n), m_):
        counts = set()
        for vals in itertools.product((0, 1), repeat=m_):
            counts.add(sum(t[x] for x in range(len(t))
                           if all((x >> v & 1) == b for v, b in zip(T, vals))))
        if len(counts) > 1:
            return False
    return True


def o_ci(t):
    n = len(t).bit_length() - 1
    order = 0
    while order < n and o_independent(t, order + 1):
        order += 1
    return order


def o_symmetric(t, rnd):
    n = len(t).bit_length() - 1
    if n <= 5:
        perms = list(itertools.permutations(range(n)))
    else:
        perms = [rnd.sample(range(n), n) for _ in range(40)]
        perms += [[*range(i), i + 1, i] + list(range(i + 2, n)) for i in range(n - 1)]
    for p in perms:
        for x in range(len(t)):
            y = sum((x >> i & 1) << p[i] for i in range(n))
            if t[y] != t[x]:
                return False
    return True


# ---- oracle agreement ----
def test_walsh_matches_double_sum():
    for t in ALL:
        assert walsh_spectrum(t)['spectrum'] == o_walsh(t)


def test_anf_matches_subset_sum_and_evaluates_back():
    for t in ALL:
        c = algebraic_normal_form(t)
        assert c['coefficients'] == o_anf(t)
        assert c['monomials'] == [u for u in range(len(t)) if c['coefficients'][u]]
        assert [o_anf_eval(c['coefficients'], x) for x in range(len(t))] == t


def test_degree_matches_subcube_parity():
    for t in ALL:
        assert algebraic_degree(t)['degree'] == o_degree(t)


def test_nonlinearity_matches_affine_distance():
    for t in ALL:
        if len(t) <= 64:
            r = nonlinearity(t)
            assert r['nonlinearity'] == o_nonlin(t)
            assert r['max_abs_walsh'] == max(abs(v) for v in o_walsh(t))
        else:
            n = len(t).bit_length() - 1
            assert nonlinearity(t)['nonlinearity'] == (1 << (n - 1)) - max(abs(v) for v in o_walsh(t)) // 2


def test_influences_match_fourier_identity():
    for t in ALL:
        r = variable_influences(t)['influences']
        assert r == o_inf_fourier(t)
        assert all(type(v) is Fraction for v in r)


def test_total_influence_matches_fourier_and_sensitivity_mean():
    for t in ALL:
        r = total_influence(t)['total_influence']
        assert r == o_total_fourier(t)
        assert r == Fraction(sum(o_sens(t)), len(t))
        assert r == sum(variable_influences(t)['influences'])
        assert type(r) is Fraction


def test_sensitivity_matches_neighbour_count():
    for t in ALL:
        r = sensitivity_profile(t)
        s = o_sens(t)
        assert r['sensitivities'] == s
        assert r['max_sensitivity'] == max(s)
        assert r['average_sensitivity'] == Fraction(sum(s), len(s))


def test_unate_matches_cofactor_comparison():
    for t in ALL:
        r = unate_profile(t)
        d = o_unate(t)
        assert r['directions'] == d
        assert r['unate'] == ('binate' not in d)
        assert r['monotone_increasing'] == all(v in ('constant', 'increasing') for v in d)
        assert r['monotone_increasing'] == all(
            t[x] <= t[y] for x in range(len(t)) for y in range(len(t)) if x & y == x)


def test_balance_and_immunity_match_definition():
    for t in ALL:
        if len(t) > 64:
            continue
        r = balance_and_immunity(t)
        assert r['balanced'] == (sum(t) * 2 == len(t))
        assert r['correlation_immunity_order'] == o_ci(t)
        assert r['resilience_order'] == (o_ci(t) if r['balanced'] else -1)


def test_balance_large_n_against_walsh_free_definition():
    rnd = random.Random(5)
    for n in (7, 8):
        for t in ([pop(x) % 2 for x in range(1 << n)], [1] * (1 << n), [0] * (1 << n),
                  [int(rnd.random() < .5) for _ in range(1 << n)]):
            r = balance_and_immunity(t)
            assert r['balanced'] == (sum(t) * 2 == len(t))
            # only orders 1..3 checked by definition at this size, cheap enough
            top = min(r['correlation_immunity_order'], 3)
            assert all(o_independent(t, k) for k in range(1, top + 1))
            if r['correlation_immunity_order'] < 3:
                assert not o_independent(t, r['correlation_immunity_order'] + 1)


def test_symmetric_matches_permutation_invariance():
    rnd = random.Random(9)
    for t in ALL:
        r = symmetric_profile(t)
        assert r['symmetric'] == o_symmetric(t, rnd)
        n = len(t).bit_length() - 1
        if r['symmetric']:
            assert r['values_by_weight'] == [t[(1 << k) - 1] for k in range(n + 1)]
        else:
            assert r['values_by_weight'] is None


# ---- hand values ----
def test_and2_hand_values():
    t = [0, 0, 0, 1]
    assert walsh_spectrum(t)['spectrum'] == [2, 2, 2, -2]
    assert algebraic_normal_form(t)['coefficients'] == [0, 0, 0, 1]
    assert algebraic_normal_form(t)['monomials'] == [3]
    assert algebraic_degree(t)['degree'] == 2
    assert nonlinearity(t)['nonlinearity'] == 1
    assert variable_influences(t)['influences'] == [Fraction(1, 2)] * 2
    assert total_influence(t)['total_influence'] == 1
    assert sensitivity_profile(t)['sensitivities'] == [0, 1, 1, 2]
    assert unate_profile(t)['directions'] == ['increasing', 'increasing']
    assert balance_and_immunity(t) == {'n': 2, 'balanced': False, 'correlation_immunity_order': 0,
                                       'resilience_order': -1, 'claims': m.CLAIMS}
    assert symmetric_profile(t)['values_by_weight'] == [0, 0, 1]


def test_bent_function_n4():
    t = [(x & 1) * (x >> 1 & 1) ^ (x >> 2 & 1) * (x >> 3 & 1) for x in range(16)]
    assert nonlinearity(t)['nonlinearity'] == 6
    assert algebraic_degree(t)['degree'] == 2
    assert set(abs(v) for v in walsh_spectrum(t)['spectrum']) == {4}


def test_parity_and_constants():
    t = [pop(x) % 2 for x in range(8)]
    assert nonlinearity(t)['nonlinearity'] == 0
    assert balance_and_immunity(t)['resilience_order'] == 2
    assert algebraic_degree(t)['degree'] == 1
    assert total_influence(t)['total_influence'] == 3
    z = [0] * 8
    assert algebraic_degree(z)['degree'] == 0
    assert balance_and_immunity(z)['correlation_immunity_order'] == 3
    assert variable_influences(z)['influences'] == [0, 0, 0]
    assert unate_profile(z)['directions'] == ['constant'] * 3
    assert symmetric_profile([1, 1])['values_by_weight'] == [1, 1]


def test_max_size_runs_and_tuple_accepted():
    t = tuple(pop(x) % 2 for x in range(256))
    assert nonlinearity(t)['nonlinearity'] == 0
    assert algebraic_degree(t)['degree'] == 1
    assert total_influence(t)['total_influence'] == 8


# ---- hardening ----
@pytest.mark.parametrize('f', FUNCS)
def test_container_type_refused_with_pinned_message(f):
    for bad in (None, 5, 'abcd', b'\x00\x01', {0, 1}, {0: 0, 1: 1}, iter([0, 1]), range(2),
                m.CLAIMS, 1.5):
        with pytest.raises(TypeError) as e:
            f(bad)
        assert str(e.value) == E_TYPE

    class L(list):
        pass
    with pytest.raises(TypeError) as e:
        f(L([0, 1]))
    assert str(e.value) == E_TYPE


@pytest.mark.parametrize('f', FUNCS)
def test_length_caps_at_cap_and_cap_plus_one(f):
    f([0, 1] * 128)
    f([0] * 2)
    f([1] * 256)
    for n in (0, 1, 3, 5, 6, 7, 255, 257, 384, 512, 1024):
        with pytest.raises(ValueError) as e:
            f([0] * n)
        assert str(e.value) == E_LEN


class Boom:
    def __eq__(self, other):
        raise AssertionError('entry touched')

    __hash__ = None

    def __index__(self):
        raise AssertionError('entry touched')


@pytest.mark.parametrize('f', FUNCS)
def test_length_refused_before_any_entry_is_read(f):
    for n in (0, 1, 3, 257, 512):
        with pytest.raises(ValueError) as e:
            f([Boom()] * n)
        assert str(e.value) == E_LEN
    with pytest.raises(TypeError) as e:
        f([Boom()] * 4)
    assert str(e.value) == E_ENT


class Flag(enum.IntEnum):
    ZERO = 0
    ONE = 1


@pytest.mark.parametrize('f', FUNCS)
def test_entry_refusals_bool_first(f):
    for bad in (True, False, 0.0, 1.0, '1', None, Flag.ONE, Flag.ZERO, Fraction(1), 1j):
        with pytest.raises(TypeError) as e:
            f([0, bad])
        assert str(e.value) == E_ENT
    for bad in (2, -1, 10 ** 30, -10 ** 30):
        with pytest.raises(ValueError) as e:
            f([1, bad])
        assert str(e.value) == E_VAL
    # a bad entry type is refused even when a later entry is a bad value, and vice versa
    with pytest.raises(TypeError) as e:
        f([0, True, 2, 0])
    assert str(e.value) == E_ENT
    with pytest.raises(ValueError) as e:
        f([0, 2, True, 0])
    assert str(e.value) == E_VAL
    with pytest.raises(ValueError) as e:
        f([0, 0, 0, True, 0, 0, 0, 0] + [5])
    assert str(e.value) == E_LEN


@pytest.mark.parametrize('f', FUNCS)
def test_both_bad_container_then_length_then_entry(f):
    with pytest.raises(TypeError) as e:
        f('xyz')
    assert str(e.value) == E_TYPE
    with pytest.raises(ValueError) as e:
        f([True] * 3)
    assert str(e.value) == E_LEN


@pytest.mark.parametrize('f', FUNCS)
def test_no_input_mutation_and_claims_false(f):
    t = [0, 1, 1, 0, 1, 0, 0, 1]
    c = list(t)
    r = f(t)
    assert t == c
    assert r['n'] == 3
    assert r['claims'] == {'cryptographic_strength': False, 'security': False,
                           'randomness': False, 'biological_network_model': False}
    assert all(v is False for v in r['claims'].values())
    r['claims']['security'] = True
    assert m.CLAIMS['security'] is False
    assert f(t)['claims']['security'] is False


def test_tuple_and_list_agree():
    t = [1, 0, 0, 1, 1, 1, 0, 0]
    for f in FUNCS:
        assert f(t) == f(tuple(t))


def test_module_statements():
    assert 'SCOPE' in m.__doc__ and 'NOT_CLAIMED' in m.__doc__
    assert m.MAX_VARS == 8

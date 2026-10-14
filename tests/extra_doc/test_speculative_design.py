from itertools import product
import pytest
from sugarcode.extra_doc.speculative_design import explore_futures as solve, NOT_CLAIMED


def oracle(axes, forbidden):
    """Independent: filter the full product by testing every forbidden pair on dict lookups."""
    names = [a[0] for a in axes]
    out = []
    for combo in product(*[a[1] for a in axes]):
        sc = dict(zip(names, combo))
        if all(not (sc[p[0][0]] == p[0][1] and sc[p[1][0]] == p[1][1]) for p in forbidden):
            out.append(sc)
    return out


def test_hand_derived_literals():
    axes = [('energy', ['scarce', 'cheap']), ('governance', ['local', 'global'])]
    r = solve(axes, [(('energy', 'scarce'), ('governance', 'global'))])
    assert r['scenarios'] == [{'energy': 'scarce', 'governance': 'local'},
                              {'energy': 'cheap', 'governance': 'local'},
                              {'energy': 'cheap', 'governance': 'global'}]
    assert (r['consistent_count'], r['candidate_count'], r['excluded_count']) == (3, 4, 1)
    assert r['value_usage'] == {'energy': {'scarce': 1, 'cheap': 2}, 'governance': {'local': 2, 'global': 1}}


def test_no_constraints_is_full_product_in_input_order():
    r = solve([('a', ['1', '2']), ('b', ['x', 'y', 'z'])])
    assert [tuple(s.values()) for s in r['scenarios']] == [('1', 'x'), ('1', 'y'), ('1', 'z'), ('2', 'x'), ('2', 'y'), ('2', 'z')]
    assert r['excluded_count'] == 0 and r['candidate_count'] == 6
    assert r['value_usage'] == {'a': {'1': 3, '2': 3}, 'b': {'x': 2, 'y': 2, 'z': 2}}


def test_pair_order_and_duplicates_are_irrelevant_and_all_excluded_is_allowed():
    axes = [('a', ['1']), ('b', ['x'])]
    p = (('a', '1'), ('b', 'x'))
    q = (('b', 'x'), ('a', '1'))
    assert solve(axes, [p])['scenarios'] == [] == solve(axes, [q])['scenarios'] == solve(axes, [p, q, p])['scenarios']
    assert solve(axes, [p])['value_usage'] == {'a': {'1': 0}, 'b': {'x': 0}}


@pytest.mark.parametrize('axes,forbidden', [
    ([('a', ['1', '2', '3']), ('b', ['x', 'y']), ('c', ['p', 'q'])], [(('a', '1'), ('b', 'x')), (('b', 'y'), ('c', 'q')), (('a', '3'), ('c', 'p'))]),
    ([('a', ['1', '2', '3', '4']), ('b', ['1', '2', '3', '4']), ('c', ['1', '2', '3', '4']), ('d', ['1', '2', '3', '4'])],
     [(('a', '1'), ('d', '4')), (('b', '2'), ('c', '3')), (('a', '2'), ('b', '2')), (('c', '1'), ('d', '1'))]),
    ([('a', ['1'])], []),
])
def test_matches_independent_oracle(axes, forbidden):
    r = solve(axes, forbidden)
    want = oracle(axes, forbidden)
    assert r['scenarios'] == want and r['consistent_count'] == len(want)
    for a, values in axes:
        for v in values:
            assert r['value_usage'][a][v] == sum(1 for s in want if s[a] == v)


def test_flags_not_claimed_and_no_mutation():
    axes = [('a', ['1', '2'])]
    snap = [('a', ['1', '2'])]
    r = solve(axes)
    assert axes == snap and r['forecast_validated'] is False and r['not_claimed'] is NOT_CLAIMED
    assert 'probability or likelihood' in NOT_CLAIMED and 'forecasting' in NOT_CLAIMED
    assert r == solve(tuple((n, tuple(v)) for n, v in axes), ())


def test_cap_boundaries_accepted():
    axes = [(c, ['1', '2', '3', '4']) for c in 'abcd']
    assert solve(axes)['candidate_count'] == 256
    f = [(('a', '1'), ('b', str(k % 4 + 1))) for k in range(16)]
    assert solve(axes, f)['consistent_count'] == 256 - 64                  # all of a=1 excluded combos: a=1 with any b -> 64
    assert solve([('x' * 40, ['y' * 40])])['scenarios'] == [{'x' * 40: 'y' * 40}]


OK = [('a', ['1', '2']), ('b', ['x'])]


@pytest.mark.parametrize('args,error,message', [
    ((None,), TypeError, 'axes must be a list or tuple'),
    (('ab',), TypeError, 'axes must be a list or tuple'),
    (([],), ValueError, 'axis count must be between 1 and 4'),
    (([('a%d' % k, ['1']) for k in range(5)],), ValueError, 'axis count must be between 1 and 4'),
    (([5],), ValueError, 'each axis must be (name, values)'),
    (([('a',)],), ValueError, 'each axis must be (name, values)'),
    (([('a', [])],), ValueError, 'each axis must have between 1 and 4 values'),
    (([('a', ['1'] * 5)],), ValueError, 'each axis must have between 1 and 4 values'),
    (([('a', '12')],), ValueError, 'each axis must have between 1 and 4 values'),
    (([(1, ['1'])],), TypeError, 'names and values must be str'),
    (([('a', [1])],), TypeError, 'names and values must be str'),
    (([('', ['1'])],), ValueError, 'names and values must be 1 to 40 characters'),
    (([('a', ['x' * 41])],), ValueError, 'names and values must be 1 to 40 characters'),
    (([('a', ['1']), ('a', ['2'])],), ValueError, 'axis names must be unique'),
    (([('a', ['1', '1'])],), ValueError, 'values within an axis must be unique'),
    ((OK, 'ab'), TypeError, 'forbidden_pairs must be a list or tuple'),
    ((OK, [(('a', '1'), ('b', 'x'))] * 17), ValueError, 'at most 16 forbidden pairs'),
    ((OK, [5]), ValueError, 'each forbidden pair must contain two (axis, value) choices'),
    ((OK, [(('a', '1'),)]), ValueError, 'each forbidden pair must contain two (axis, value) choices'),
    ((OK, [(5, ('b', 'x'))]), ValueError, 'each choice must be (axis, value)'),
    ((OK, [(('a',), ('b', 'x'))]), ValueError, 'each choice must be (axis, value)'),
    ((OK, [((1, '1'), ('b', 'x'))]), TypeError, 'names and values must be str'),
    ((OK, [(('c', '1'), ('b', 'x'))]), ValueError, 'forbidden pairs may only use listed axes and values'),
    ((OK, [(('a', '9'), ('b', 'x'))]), ValueError, 'forbidden pairs may only use listed axes and values'),
    ((OK, [(('a', '1'), ('a', '2'))]), ValueError, 'a forbidden pair must name two different axes'),
])
def test_errors(args, error, message):
    with pytest.raises(error) as exc:
        solve(*args)
    assert type(exc.value) is error and str(exc.value) == message

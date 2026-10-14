from fractions import Fraction as F
from itertools import product
import pytest
from sugarcode.extra_doc.design_thinking import cover_needs as solve, NOT_CLAIMED


def oracle(needs, ideas):
    """Independent: bitmask enumeration of every subset."""
    n = len(ideas)
    best = None
    for mask in range(1 << n):
        picked = [i for i in range(n) if mask >> i & 1]
        cov = {c for i in picked for c in ideas[i][1]}
        if cov >= set(needs):
            cost = sum(F(ideas[i][2]) for i in picked)
            key = (cost, len(picked), tuple(picked))
            if best is None or key < best:
                best = key
    return best


def test_hand_derived_literals():
    needs = ['a', 'b', 'c']
    ideas = [('i1', ['a', 'b'], 5), ('i2', ['c'], 2), ('i3', ['a', 'b', 'c'], 8), ('i4', ['b', 'c'], 3)]
    # subsets covering all: {i1,i2}=7, {i3}=8, {i1,i4}=8, {i2,i4}? covers b,c only no. cheapest {i1,i2} cost 7
    r = solve(needs, ideas)
    assert r['chosen_ideas'] == ['i1', 'i2'] and r['chosen_indices'] == [0, 1] and r['cost'] == 7
    assert r['coverage'] == {'a': ['i1'], 'b': ['i1'], 'c': ['i2']}
    assert type(r['cost']) is F


def test_ties_fewer_ideas_then_lexicographic_indices():
    # cost 6 either as one idea (index 2) or as two ideas (0,1): fewer ideas wins
    r = solve(['x', 'y'], [('p', ['x'], 3), ('q', ['y'], 3), ('r', ['x', 'y'], 6)])
    assert r['chosen_indices'] == [2]
    # equal cost, equal size: lexicographically smallest index tuple
    r = solve(['x'], [('p', ['x'], 4), ('q', ['x'], 4)])
    assert r['chosen_indices'] == [0]
    r = solve(['x', 'y'], [('p', ['x'], 1), ('q', ['y'], 2), ('r', ['x'], 1), ('s', ['y'], 2)])
    assert r['chosen_indices'] == [0, 1]


def test_zero_cost_extra_ideas_are_not_added():
    r = solve(['x'], [('p', ['x'], 0), ('q', ['x'], 0)])
    assert r['chosen_indices'] == [0] and r['cost'] == 0


@pytest.mark.parametrize('needs,ideas', [
    (['a', 'b', 'c', 'd'], [('i1', ['a', 'b'], 4), ('i2', ['c', 'd'], 4), ('i3', ['a', 'c'], 2), ('i4', ['b', 'd'], 2), ('i5', ['a'], 1)]),
    (['a', 'b'], [('i1', ['a'], F(1, 3)), ('i2', ['b'], F(1, 6)), ('i3', ['a', 'b'], F(1, 2)), ('i4', [], 0)]),
    (['n%d' % k for k in range(8)], [('j%d' % k, ['n%d' % k, 'n%d' % ((k + 1) % 8)], 3 + k % 2) for k in range(8)] + [('all', ['n%d' % k for k in range(8)], 17)]),
])
def test_matches_independent_oracle(needs, ideas):
    cost, size, combo = oracle(needs, ideas)
    r = solve(needs, ideas)
    assert (r['cost'], len(r['chosen_indices']), tuple(r['chosen_indices'])) == (cost, size, combo)


def test_flags_not_claimed_and_no_mutation():
    needs, ideas = ['a'], [('i', ['a'], 1)]
    snap = (list(needs), [('i', ['a'], 1)])
    r = solve(needs, ideas)
    assert (needs, ideas) == snap and r['user_research_validated'] is False and r['not_claimed'] is NOT_CLAIMED
    assert 'user research' in NOT_CLAIMED and 'usability' in NOT_CLAIMED
    assert r == solve(tuple(needs), tuple((i, tuple(c), k) for i, c, k in ideas))


def test_cap_boundaries_accepted():
    needs = ['n%d' % k for k in range(8)]
    ideas = [('j%d' % k, [needs[k % 8]], 1) for k in range(10)]
    assert solve(needs, ideas[:8])['cost'] == 8
    assert solve(needs, ideas)['chosen_indices'] == list(range(8))       # 10 ideas allowed
    assert solve(['a' * 40], [('b' * 40, ['a' * 40], 2**32 - 1)])['cost'] == 2**32 - 1
    assert solve(['a'], [('i', ['a'], F(1, 2**32 - 1))])['cost'] == F(1, 2**32 - 1)
    assert solve(['a'], [('i', ['a'], F(2**32 - 1, 7))])['cost'] == F(2**32 - 1, 7)
    assert solve(['a'], [('i', ['a'], F(2**20, 3))])['cost'] == F(2**20, 3)
    assert solve(['a'], [('i', ['a'], 0)])['cost'] == 0


OK = (['a'], [('i', ['a'], 1)])


@pytest.mark.parametrize('args,error,message', [
    ((None, OK[1]), TypeError, 'needs and ideas must be lists or tuples'),
    ((OK[0], 'ab'), TypeError, 'needs and ideas must be lists or tuples'),
    (([], OK[1]), ValueError, 'need count must be between 1 and 8'),
    ((['n%d' % k for k in range(9)], OK[1]), ValueError, 'need count must be between 1 and 8'),
    ((OK[0], []), ValueError, 'idea count must be between 1 and 10'),
    ((OK[0], [('i%d' % k, ['a'], 1) for k in range(11)]), ValueError, 'idea count must be between 1 and 10'),
    ((['a', 'a'], OK[1]), ValueError, 'need ids must be unique'),
    ((OK[0], [('i', ['a'], 1), ('i', ['a'], 2)]), ValueError, 'idea ids must be unique'),
    ((OK[0], [5]), ValueError, 'each idea must be (id, covered_needs, cost)'),
    ((OK[0], [('i', ['a'])]), ValueError, 'each idea must be (id, covered_needs, cost)'),
    ((OK[0], [('i', 'a', 1)]), ValueError, 'covered needs must be a list or tuple of at most 8 ids'),
    ((OK[0], [('i', ['a'] * 9, 1)]), ValueError, 'covered needs must be a list or tuple of at most 8 ids'),
    (([5], OK[1]), TypeError, 'ids must be str'),
    (([''], OK[1]), ValueError, 'ids must be 1 to 40 characters'),
    ((['a' * 41], OK[1]), ValueError, 'ids must be 1 to 40 characters'),
    ((OK[0], [('i', ['b'], 1)]), ValueError, 'ideas may only cover listed needs'),
    ((['a', 'b'], [('i', ['a'], 1)]), ValueError, 'no set of ideas covers every need'),
    ((OK[0], [('i', ['a'], True)]), TypeError, 'cost must be nonbool int or Fraction'),
    ((OK[0], [('i', ['a'], 1.5)]), TypeError, 'cost must be nonbool int or Fraction'),
    ((OK[0], [('i', ['a'], float('nan'))]), TypeError, 'cost must be nonbool int or Fraction'),
    ((OK[0], [('i', ['a'], -1)]), ValueError, 'cost must be nonnegative'),
    ((OK[0], [('i', ['a'], F(-1, 2))]), ValueError, 'cost must be nonnegative'),
    ((OK[0], [('i', ['a'], 2**32)]), ValueError, 'cost must fit 32 bits'),
    ((OK[0], [('i', ['a'], F(2**32, 3))]), ValueError, 'cost must fit 32 bits'),
    ((OK[0], [('i', ['a'], F(1, 2**32))]), ValueError, 'cost must fit 32 bits'),
])
def test_errors(args, error, message):
    with pytest.raises(error) as exc:
        solve(*args)
    assert type(exc.value) is error and str(exc.value) == message

import pytest
from sugarcode.extra_doc.critical_design import challenge_assumptions as solve, NOT_CLAIMED


def oracle(assumptions, claims):
    """Independent: simulate negating each assumption and test every claim's conjunction."""
    out = {}
    for a in assumptions:
        holds = {x: (x != a) for x in assumptions}
        out[a] = [cid for cid, deps in claims if not all(holds[d] for d in deps)]
    return out


def test_hand_derived_literals():
    # claims: c1 needs a,b ; c2 needs b ; c3 needs a,b,c ; c4 needs nothing. a carries c1,c3 ; b carries c1,c2,c3 ; c carries c3 ; d none
    r = solve(['a', 'b', 'c', 'd'], [('c1', ['a', 'b']), ('c2', ['b']), ('c3', ['a', 'b', 'c']), ('c4', [])])
    assert r['falls_if_negated'] == {'a': ['c1', 'c3'], 'b': ['c1', 'c2', 'c3'], 'c': ['c3'], 'd': []}
    assert r['ranking'] == ['b', 'a', 'c', 'd'] and r['most_critical'] == ['b']
    assert r['unused_assumptions'] == ['d'] and r['unconditional_claims'] == ['c4']


def test_ties_keep_input_order_and_most_critical_lists_all_tied():
    r = solve(['x', 'y', 'z'], [('c1', ['x']), ('c2', ['y']), ('c3', ['z', 'x'])])
    assert r['ranking'] == ['x', 'y', 'z'] and r['most_critical'] == ['x']          # x carries 2
    r = solve(['x', 'y'], [('c1', ['x']), ('c2', ['y'])])
    assert r['ranking'] == ['x', 'y'] and r['most_critical'] == ['x', 'y']
    r = solve(['y', 'x'], [('c1', ['x']), ('c2', ['y'])])
    assert r['ranking'] == ['y', 'x'] and r['most_critical'] == ['y', 'x']


def test_no_dependencies_means_no_critical_assumption():
    r = solve(['a'], [('c', [])])
    assert r['most_critical'] == [] and r['unused_assumptions'] == ['a'] and r['unconditional_claims'] == ['c']
    assert r['ranking'] == ['a'] and r['falls_if_negated'] == {'a': []}


@pytest.mark.parametrize('assumptions,claims', [
    (['a', 'b', 'c', 'd', 'e'], [('c1', ['a', 'b']), ('c2', ['b', 'c']), ('c3', ['d']), ('c4', ['a', 'b', 'c', 'd', 'e']), ('c5', [])]),
    (['p', 'q'], [('k%d' % i, ['p'] if i % 2 else ['q']) for i in range(10)]),
    (['a%d' % i for i in range(8)], [('c%d' % i, ['a%d' % i, 'a%d' % ((i + 1) % 8)]) for i in range(8)]),
])
def test_matches_independent_oracle(assumptions, claims):
    r = solve(assumptions, claims)
    assert r['falls_if_negated'] == oracle(assumptions, claims)
    counts = {a: len(v) for a, v in r['falls_if_negated'].items()}
    assert counts == {a: len(v) for a, v in oracle(assumptions, claims).items()}
    assert [counts[a] for a in r['ranking']] == sorted(counts.values(), reverse=True)


def test_flags_not_claimed_and_no_mutation():
    a, c = ['a'], [('c', ['a'])]
    snap = (list(a), [('c', ['a'])])
    r = solve(a, c)
    assert (a, c) == snap and r['assumptions_validated'] is False and r['not_claimed'] is NOT_CLAIMED
    assert 'assumption truth' in NOT_CLAIMED and 'critique quality' in NOT_CLAIMED
    assert r == solve(tuple(a), tuple((i, tuple(d)) for i, d in c))


def test_cap_boundaries_accepted():
    names = ['a%d' % i for i in range(8)]
    claims = [('c%d' % i, list(names)) for i in range(10)]
    r = solve(names, claims)
    assert all(len(v) == 10 for v in r['falls_if_negated'].values()) and r['most_critical'] == names
    assert solve(['a' * 40], [('b' * 40, ['a' * 40])])['ranking'] == ['a' * 40]


OK = (['a'], [('c', ['a'])])


@pytest.mark.parametrize('args,error,message', [
    ((None, OK[1]), TypeError, 'assumptions and claims must be lists or tuples'),
    ((OK[0], 'ab'), TypeError, 'assumptions and claims must be lists or tuples'),
    (([], OK[1]), ValueError, 'assumption count must be between 1 and 8'),
    ((['a%d' % i for i in range(9)], OK[1]), ValueError, 'assumption count must be between 1 and 8'),
    ((OK[0], []), ValueError, 'claim count must be between 1 and 10'),
    ((OK[0], [('c%d' % i, []) for i in range(11)]), ValueError, 'claim count must be between 1 and 10'),
    (([5], OK[1]), TypeError, 'ids must be str'),
    ((['x' * 41], OK[1]), ValueError, 'ids must be 1 to 40 characters'),
    (([''], OK[1]), ValueError, 'ids must be 1 to 40 characters'),
    ((['a', 'a'], OK[1]), ValueError, 'assumption ids must be unique'),
    ((OK[0], [5]), ValueError, 'each claim must be (id, assumption_ids)'),
    ((OK[0], [('c',)]), ValueError, 'each claim must be (id, assumption_ids)'),
    ((OK[0], [('c', 'a')]), ValueError, 'assumption ids must be a list or tuple of at most 8 ids'),
    ((OK[0], [('c', ['a'] * 9)]), ValueError, 'assumption ids must be a list or tuple of at most 8 ids'),
    ((OK[0], [('c', ['a', 'a'])]), ValueError, 'a claim may list each assumption once'),
    ((OK[0], [(5, ['a'])]), TypeError, 'ids must be str'),
    ((OK[0], [('c', [5])]), TypeError, 'ids must be str'),
    ((OK[0], [('c', ['a']), ('c', [])]), ValueError, 'claim ids must be unique'),
    ((OK[0], [('c', ['z'])]), ValueError, 'claims may only depend on listed assumptions'),
])
def test_errors(args, error, message):
    with pytest.raises(error) as exc:
        solve(*args)
    assert type(exc.value) is error and str(exc.value) == message

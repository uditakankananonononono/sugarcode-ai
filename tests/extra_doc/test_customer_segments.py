from collections import Counter
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.customer_segments import identify_segments as solve, NOT_CLAIMED


def cust(i, **kw):
    return (i, dict(kw))


def oracle(customers, attrs):
    """Independent: Counter over value tuples, ordering by (-count, first index)."""
    keys = [tuple(c[1][a] for a in attrs) for c in customers]
    first = {}
    for i, k in enumerate(keys):
        first.setdefault(k, i)
    cnt = Counter(keys)
    return [(k, [customers[i][0] for i, kk in enumerate(keys) if kk == k], cnt[k]) for k in sorted(cnt, key=lambda k: (-cnt[k], first[k]))]


def test_hand_derived_literals():
    cs = [cust('u1', region='N', plan='free'), cust('u2', region='S', plan='pro'), cust('u3', region='N', plan='free'),
          cust('u4', region='S', plan='free'), cust('u5', region='N', plan='free'), cust('u6', region='S', plan='pro')]
    r = solve(cs, ['region', 'plan'], 2)
    assert [s['attributes'] for s in r['segments']] == [{'region': 'N', 'plan': 'free'}, {'region': 'S', 'plan': 'pro'}, {'region': 'S', 'plan': 'free'}]
    assert [s['members'] for s in r['segments']] == [['u1', 'u3', 'u5'], ['u2', 'u6'], ['u4']]
    assert [s['size'] for s in r['segments']] == [3, 2, 1] and [s['share'] for s in r['segments']] == [F(1, 2), F(1, 3), F(1, 6)]
    assert [s['qualifying'] for s in r['segments']] == [True, True, False]
    assert r['qualifying_count'] == 2 and r['qualifying_share'] == F(5, 6) and r['segment_count'] == 3 and r['customer_count'] == 6
    assert type(r['qualifying_share']) is F


def test_ties_keep_first_appearance_and_min_size_boundary():
    cs = [cust('a', t='x'), cust('b', t='y'), cust('c', t='y'), cust('d', t='x')]
    r = solve(cs, ['t'], 2)
    assert [s['attributes']['t'] for s in r['segments']] == ['x', 'y'] and all(s['qualifying'] for s in r['segments'])
    assert solve(cs, ['t'], 3)['qualifying_count'] == 0 and solve(cs, ['t'], 3)['qualifying_share'] == 0
    assert solve(cs, ['t'])['qualifying_count'] == 2                              # default min_size 1


def test_only_chosen_attributes_split_segments_and_extra_attributes_ignored():
    cs = [cust('a', t='x', z='1'), cust('b', t='x', z='2')]
    assert solve(cs, ['t'])['segment_count'] == 1 and solve(cs, ['t', 'z'])['segment_count'] == 2
    assert solve(cs, ['z', 't'])['segments'][0]['attributes'] == {'z': '1', 't': 'x'}


@pytest.mark.parametrize('cs,attrs', [
    ([cust('c%d' % i, a='x' if i % 3 else 'y', b='p' if i % 2 else 'q', c=str(i % 4)) for i in range(17)], ['a', 'b']),
    ([cust('c%d' % i, a=str((i * 7) % 5), b=str(i % 2), c='k', d=str(i % 3)) for i in range(40)], ['a', 'b', 'c', 'd']),
    ([cust('only', a='z')], ['a']),
])
def test_matches_independent_oracle(cs, attrs):
    want = oracle(cs, attrs)
    r = solve(cs, attrs)
    assert [(tuple(s['attributes'][a] for a in attrs), s['members'], s['size']) for s in r['segments']] == want
    assert sum(s['share'] for s in r['segments']) == 1


def test_flags_not_claimed_and_no_mutation():
    cs = [cust('a', t='x')]
    snap = [cust('a', t='x')]
    r = solve(cs, ['t'])
    assert cs == snap and r['target_market_validated'] is False and r['not_claimed'] is NOT_CLAIMED
    assert 'market size' in NOT_CLAIMED and 'legal or approval-gate clearance' in NOT_CLAIMED
    assert r == solve(tuple(cs), ('t',))


def test_cap_boundaries_accepted():
    cs = [cust('c%d' % i, a='v') for i in range(40)]
    r = solve(cs, ['a', 'b', 'c', 'd'][:1], 40)
    assert r['qualifying_count'] == 1 and r['qualifying_share'] == 1
    four = [cust('x' * 40, a='y' * 40, b='1', c='2', d='3')]
    assert solve(four, ['a', 'b', 'c', 'd'])['segment_count'] == 1


OK = ([cust('a', t='x')], ['t'])


@pytest.mark.parametrize('args,error,message', [
    ((None, OK[1]), TypeError, 'customers and attributes must be lists or tuples'),
    ((OK[0], 'ab'), TypeError, 'customers and attributes must be lists or tuples'),
    (([], OK[1]), ValueError, 'customer count must be between 1 and 40'),
    (([cust('c%d' % i, t='x') for i in range(41)], OK[1]), ValueError, 'customer count must be between 1 and 40'),
    ((OK[0], []), ValueError, 'attribute count must be between 1 and 4'),
    ((OK[0], ['a', 'b', 'c', 'd', 'e']), ValueError, 'attribute count must be between 1 and 4'),
    ((OK[0], OK[1], True), TypeError, 'min_size must be nonbool int'),
    ((OK[0], OK[1], 1.0), TypeError, 'min_size must be nonbool int'),
    ((OK[0], OK[1], 0), ValueError, 'min_size must be between 1 and 40'),
    ((OK[0], OK[1], 41), ValueError, 'min_size must be between 1 and 40'),
    ((OK[0], [5]), TypeError, 'attribute names must be str'),
    ((OK[0], ['']), ValueError, 'attribute names must be 1 to 40 characters'),
    ((OK[0], ['t', 't']), ValueError, 'attribute names must be unique'),
    (([5], OK[1]), ValueError, 'each customer must be (id, attributes)'),
    (([('a',)], OK[1]), ValueError, 'each customer must be (id, attributes)'),
    (([('a', 'x')], OK[1]), TypeError, 'customer attributes must be a dict'),
    (([(5, {'t': 'x'})], OK[1]), TypeError, 'customer ids must be str'),
    (([('', {'t': 'x'})], OK[1]), ValueError, 'customer ids must be 1 to 40 characters'),
    (([('a', {'u': 'x'})], OK[1]), ValueError, 'customer is missing attribute t'),
    (([('a', {'t': 5})], OK[1]), TypeError, 'attribute values must be str'),
    (([('a', {'t': ''})], OK[1]), ValueError, 'attribute values must be 1 to 40 characters'),
    (([('a', {'t': 'x' * 41})], OK[1]), ValueError, 'attribute values must be 1 to 40 characters'),
    (([cust('a', t='x'), cust('a', t='y')], OK[1]), ValueError, 'customer ids must be unique'),
])
def test_errors(args, error, message):
    with pytest.raises(error) as exc:
        solve(*args)
    assert type(exc.value) is error and str(exc.value) == message


def test_default_min_size_is_one_singletons_qualify():
    r = solve([cust('a', t='x'), cust('b', t='y'), cust('c', t='y')], ['t'])
    assert [s['qualifying'] for s in r['segments']] == [True, True] and r['qualifying_share'] == 1
    assert solve([cust('a', t='x'), cust('b', t='y'), cust('c', t='y')], ['t'], 2)['qualifying_share'] == F(2, 3)

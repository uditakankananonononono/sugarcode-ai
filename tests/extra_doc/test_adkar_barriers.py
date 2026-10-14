from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.adkar_barriers import adkar_barriers as solve, ELEMENTS, NOT_CLAIMED

P = [('p1', (5, 4, 2, 5, 5)), ('p2', (1, 5, 5, 5, 5)), ('p3', (5, 5, 5, 5, 5)), ('p4', (4, 3, 5, 1, 2))]


def test_hand_derived_literal():
    r = solve(P, 3)
    assert [(p['label'], p['barrier']) for p in r['people']] == [
        ('p1', 'Knowledge'), ('p2', 'Awareness'), ('p3', None), ('p4', 'Desire')]       # p4: 3 <= 3 on the edge
    assert [(e['element'], e['mean'], e['barrier_count']) for e in r['elements']] == [
        ('Awareness', F(15, 4), 1), ('Desire', F(17, 4), 1), ('Knowledge', F(17, 4), 1),
        ('Ability', 4, 0), ('Reinforcement', F(17, 4), 0)]
    assert r['most_common_barrier'] == 'Awareness' and type(r['elements'][0]['mean']) is F
    assert r['adkar_validated'] is False and r['not_claimed'] == NOT_CLAIMED
    assert ELEMENTS == ('Awareness', 'Desire', 'Knowledge', 'Ability', 'Reinforcement')


def test_first_low_element_wins_and_threshold_edges():
    r = solve([('a', (3, 1, 1, 1, 1))], 3)
    assert r['people'][0]['barrier'] == 'Awareness'
    assert solve([('a', (4, 1, 1, 1, 1))], 3)['people'][0]['barrier'] == 'Desire'
    assert solve([('a', (4, 4, 4, 4, 4))], 3)['people'][0]['barrier'] is None
    assert solve([('a', (1, 1, 1, 1, 1))], 1)['people'][0]['barrier'] == 'Awareness'
    assert solve([('a', (2, 2, 2, 2, 1))], 1)['people'][0]['barrier'] == 'Reinforcement'
    assert solve([('a', (5, 5, 5, 5, 5))], 5)['people'][0]['barrier'] == 'Awareness'


def test_most_common_barrier_tie_first_in_model_order_and_none():
    r = solve([('a', (5, 5, 1, 5, 5)), ('b', (5, 1, 5, 5, 5)), ('c', (5, 1, 5, 5, 5)), ('d', (5, 5, 5, 5, 1)),
               ('e', (5, 5, 5, 5, 1))], 2)
    assert r['most_common_barrier'] == 'Desire'
    r = solve([('a', (5, 5, 5, 1, 5)), ('b', (5, 5, 5, 5, 1)), ('c', (5, 5, 5, 5, 1))], 2)
    assert r['most_common_barrier'] == 'Reinforcement'
    assert solve([('a', (5,) * 5)], 2)['most_common_barrier'] is None


def test_caps():
    solve([('p%d' % i, (5,) * 5) for i in range(20)], 5)
    solve([('x' * 40, (1,) * 5)], 1)
    with pytest.raises(ValueError, match='people count'):
        solve([('p%d' % i, (5,) * 5) for i in range(21)], 3)
    with pytest.raises(ValueError, match='people count'):
        solve([], 3)
    for bad in (0, 6):
        with pytest.raises(ValueError, match='threshold must be between'):
            solve(P, bad)
        with pytest.raises(ValueError, match='scores must be between'):
            solve([('a', (bad, 1, 1, 1, 1))], 3)
    with pytest.raises(ValueError, match='1 to 40'):
        solve([('x' * 41, (1,) * 5)], 3)
    with pytest.raises(ValueError, match='1 to 40'):
        solve([('', (1,) * 5)], 3)
    with pytest.raises(ValueError, match='5 entries'):
        solve([('a', (1,) * 4)], 3)
    with pytest.raises(ValueError, match='5 entries'):
        solve([('a', [1] * 10 ** 6)], 3)


@pytest.mark.parametrize('args,exc,msg', [
    ((P, True), TypeError, 'threshold must be nonbool'),
    ((P, 3.0), TypeError, 'threshold must be nonbool'),
    (('x', 3), TypeError, 'list or tuple'),
    (([('a',)], 3), ValueError, 'each person'),
    (([{1: 1, 2: 2}], 3), ValueError, 'each person'),
    (([(1, (1,) * 5)], 3), TypeError, 'labels must be str'),
    (([('a', 'abcde')], 3), ValueError, '5 entries'),
    (([('a', (True, 1, 1, 1, 1))], 3), TypeError, 'scores must be nonbool'),
    (([('a', (1.0, 1, 1, 1, 1))], 3), TypeError, 'scores must be nonbool'),
    (([('a', (1,) * 5), ('a', (1,) * 5)], 3), ValueError, 'unique'),
])
def test_refusals(args, exc, msg):
    with pytest.raises(exc, match=msg):
        solve(*args)

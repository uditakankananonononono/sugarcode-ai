from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.scenario_matrix import analyse_scenarios as solve, NOT_CLAIMED

S = [('low', 1), ('mid', 1), ('high', 2)]
O = [('A', [10, 0, 4]), ('B', [6, 6, 2]), ('C', [-2, 12, 5])]


def test_hand_derived_literal():
    r = solve(S, O)
    assert r['probabilities'] == [F(1, 4), F(1, 4), F(1, 2)] and type(r['probabilities'][0]) is F
    # column maxima 10, 12, 5 -> regrets A [0,12,1], B [4,6,3], C [12,0,0]
    assert [(o['name'], o['expected'], o['worst'], o['max_regret']) for o in r['options']] == [
        ('A', F(9, 2), 0, 12), ('B', 4, 2, 6), ('C', 5, -2, 12)]
    assert (r['best_expected'], r['maximin'], r['minimax_regret']) == ('C', 'B', 'B')
    assert r['scenarios_validated'] is False and r['not_claimed'] == NOT_CLAIMED


def test_the_three_rules_can_disagree_and_ties_take_first():
    r = solve([('s', 1)], [('x', [5]), ('y', [5])])
    assert (r['best_expected'], r['maximin'], r['minimax_regret']) == ('x', 'x', 'x')
    r = solve([('s', 1), ('t', 1)], [('x', [1, 9]), ('y', [9, 1])])
    assert r['best_expected'] == 'x' and r['maximin'] == 'x' and r['minimax_regret'] == 'x'
    r = solve([('s', 1), ('t', 1)], [('x', [0, 10]), ('y', [4, 5])])
    # EV 5 vs 9/2, worst 0 vs 4, regrets [4,0] vs [0,5]: the rules disagree
    assert (r['best_expected'], r['maximin'], r['minimax_regret']) == ('x', 'y', 'x')
    assert [o['max_regret'] for o in r['options']] == [4, 5] and r['options'][1]['expected'] == F(9, 2)


def test_zero_weight_scenario_and_negatives():
    r = solve([('a', 0), ('b', 5)], [('x', [100, 1]), ('y', [-100, 2])])
    assert r['probabilities'] == [0, 1]
    assert (r['best_expected'], r['maximin'], r['minimax_regret']) == ('y', 'x', 'x')
    assert r['options'][0]['expected'] == 1 and r['options'][1]['expected'] == 2
    assert r['options'][0]['worst'] == 1 and r['options'][1]['worst'] == -100


def test_independent_recomputation():
    import random
    rnd = random.Random(12)
    for ns, no in ((1, 1), (4, 5), (6, 6)):
        w = [rnd.randint(0, 20) for _ in range(ns)]
        w[0] = max(w[0], 1)
        ops = [('o%d' % i, [rnd.randint(-50, 50) for _ in range(ns)]) for i in range(no)]
        r = solve([('s%d' % j, w[j]) for j in range(ns)], ops)
        for o, (_, pay) in zip(r['options'], ops):
            assert o['expected'] == F(sum(a * b for a, b in zip(w, pay)), sum(w))
            assert o['worst'] == min(pay)
            assert o['max_regret'] == max(max(p[j] for _, p in ops) - pay[j] for j in range(ns))


def test_caps():
    solve([('s%d' % i, 1000) for i in range(6)], [('o%d' % i, [10 ** 6] * 6) for i in range(6)])
    solve([('x' * 40, 1)], [('y' * 40, [-10 ** 6])])
    with pytest.raises(ValueError, match='scenario count'):
        solve([('s%d' % i, 1) for i in range(7)], [('o', [0] * 7)])
    with pytest.raises(ValueError, match='scenario count'):
        solve([], [('o', [])])
    with pytest.raises(ValueError, match='option count'):
        solve(S, [('o%d' % i, [0, 0, 0]) for i in range(7)])
    with pytest.raises(ValueError, match='option count'):
        solve(S, [])
    with pytest.raises(ValueError, match='weights must be between'):
        solve([('s', 1001)], [('o', [0])])
    with pytest.raises(ValueError, match='weights must be between'):
        solve([('s', -1)], [('o', [0])])
    with pytest.raises(ValueError, match='positive total'):
        solve([('s', 0), ('t', 0)], [('o', [0, 0])])
    for bad in (10 ** 6 + 1, -10 ** 6 - 1):
        with pytest.raises(ValueError, match='payoffs must be between'):
            solve([('s', 1)], [('o', [bad])])
    with pytest.raises(ValueError, match='1 to 40'):
        solve([('x' * 41, 1)], [('o', [0])])
    with pytest.raises(ValueError, match='1 to 40'):
        solve([('s', 1)], [('', [0])])
    with pytest.raises(ValueError, match='one payoff per scenario'):
        solve([('s', 1)], [('o', [0] * 10 ** 6)])


@pytest.mark.parametrize('args,exc,msg', [
    (('x', O), TypeError, 'list or tuple'),
    ((S, 'x'), TypeError, 'list or tuple'),
    (([('s',)], O), ValueError, 'each scenario'),
    (([{1: 1, 2: 2}], O), ValueError, 'each scenario'),
    (([(1, 1)], O), TypeError, 'names must be str'),
    (([('s', True)], [('o', [0])]), TypeError, 'weights must be nonbool'),
    (([('s', 1), ('s', 1)], [('o', [0, 0])]), ValueError, 'scenario names must be unique'),
    ((S, [('o',)]), ValueError, 'each option'),
    ((S, [{1: 1, 2: 2}]), ValueError, 'each option'),
    ((S, [('o', [0, 0])]), ValueError, 'one payoff per scenario'),
    ((S, [('o', 'abc')]), ValueError, 'one payoff per scenario'),
    ((S, [('o', [0, 0, True])]), TypeError, 'payoffs must be nonbool'),
    ((S, [('o', [0, 0, 1.0])]), TypeError, 'payoffs must be nonbool'),
    ((S, [('o', [0, 0, 0]), ('o', [0, 0, 0])]), ValueError, 'option names must be unique'),
])
def test_refusals(args, exc, msg):
    with pytest.raises(exc, match=msg):
        solve(*args)


def test_three_rules_give_three_distinct_winners_without_ties():
    r = solve([('a', 1), ('b', 1), ('c', 1)], [('x', [0, 0, 10]), ('y', [2, 2, 2]), ('z', [6, 6, 0])])
    # EV 10/3, 2, 4 ; worst 0, 2, 0 ; column maxima 6, 6, 10 give max regrets 6, 8, 10
    assert [(o['expected'], o['worst'], o['max_regret']) for o in r['options']] == [(F(10, 3), 0, 6), (2, 2, 8), (4, 0, 10)]
    assert (r['best_expected'], r['maximin'], r['minimax_regret']) == ('z', 'y', 'x')

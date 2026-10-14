import itertools
import random
import pytest
from sugarcode.extra_doc.action_plan import plan_actions as pa

T, V = TypeError, ValueError


def run(state, act):
    nm, needs, adds, rems = act
    if not set(needs) <= state:
        return None
    return (state - set(rems)) | set(adds)


def oracle(init, goal, acts, max_len=6):
    s0 = set(init)
    if set(goal) <= s0:
        return [], 0
    for L in range(1, max_len + 1):
        for seq in itertools.product(range(len(acts)), repeat=L):      # lexicographic by position
            s = set(init)
            for i in seq:
                s = run(s, acts[i])
                if s is None:
                    break
            if s is not None and set(goal) <= s:
                return [acts[i][0] for i in seq], L
    return None, None


EAT = [('eat', ['food'], ['fed'], ['hungry']), ('buy', ['money'], ['food'], []), ('work', [], ['money'], [])]


def test_hand_cases_exact():
    assert pa(['hungry'], ['fed'], EAT) == {'found': True, 'plan': ['work', 'buy', 'eat'], 'length': 3}
    assert pa(['hungry'], [], EAT) == {'found': True, 'plan': [], 'length': 0}
    assert pa(['fed', 'x'], ['fed'], EAT) == {'found': True, 'plan': [], 'length': 0}
    assert pa(['hungry'], ['fed'], EAT[:2]) == {'found': False, 'plan': None, 'length': None}
    assert pa(['hungry'], ['fed', 'hungry'], EAT) == {'found': False, 'plan': None, 'length': None}
    assert pa([], [], []) == {'found': True, 'plan': [], 'length': 0}


def test_ties_prefer_smaller_positions_and_shorter_wins():
    acts = [('slow1', [], ['m'], []), ('slow2', ['m'], ['g'], []), ('direct', [], ['g'], [])]
    assert pa([], ['g'], acts) == {'found': True, 'plan': ['direct'], 'length': 1}
    acts = [('b', [], ['g'], []), ('a', [], ['g'], [])]
    assert pa([], ['g'], acts)['plan'] == ['b']
    acts = [('x', [], ['p'], []), ('y', [], ['q'], []), ('z', ['p', 'q'], ['g'], [])]
    assert pa([], ['g'], acts)['plan'] == ['x', 'y', 'z']
    assert pa([], ['g'], [acts[1], acts[0], acts[2]])['plan'] == ['y', 'x', 'z']


def test_removal_then_addition_and_goal_must_hold_at_end():
    acts = [('flip', ['on'], ['off'], ['on']), ('flop', ['off'], ['on'], ['off'])]
    assert pa(['on'], ['off'], acts)['plan'] == ['flip']
    assert pa(['on'], ['on', 'off'], acts)['found'] is False
    # an add that is also true already is fine; a removed fact that was true is gone afterwards
    acts = [('go', ['a'], ['a2'], ['a'])]
    assert pa(['a'], ['a'], acts)['plan'] == []
    assert pa(['a'], ['a2'], acts)['plan'] == ['go']


def test_random_vs_oracle():
    rnd = random.Random(572)
    found = lens = unreachable = 0
    for _ in range(1500):
        facts = ['f%d' % i for i in range(rnd.randint(2, 6))]
        acts = []
        for k in range(rnd.randint(2, 5)):
            adds = rnd.sample(facts, 1)
            rems = [x for x in rnd.sample(facts, rnd.randint(0, min(2, len(facts)))) if x not in adds]
            acts.append(('a%d' % k, rnd.sample(facts, 1), adds, rems))
        if rnd.random() < 0.5:     # a shuffled chain f0 -> f1 -> ... so that longer plans occur
            acts = [('c%d' % i, [facts[i]], [facts[i + 1]], []) for i in range(len(facts) - 1)][:5]
            rnd.shuffle(acts)
        init = rnd.sample(facts, 1)
        goal = rnd.sample(facts, 1)
        want, wl = oracle(init, goal, acts, 5)
        got = pa(init, goal, acts)
        if want is None:
            unreachable += not got['found']
            # oracle bounded at 7 steps; with at most 2**5 states a plan, if any, has at most 31 steps
            if got['found']:
                assert got["length"] > 5
                s = set(init)
                for nm in got['plan']:
                    s = run(s, next(a for a in acts if a[0] == nm))
                    assert s is not None
                assert set(goal) <= s
        else:
            assert got == {'found': True, 'plan': want, 'length': wl}
            found += 1
            lens += wl >= 3
    assert found > 100 and lens > 20 and unreachable > 20


def test_long_plan_16_facts():
    acts = [('s%d' % i, ['f%d' % i], ['f%d' % (i + 1)], ['f%d' % i]) for i in range(15)]
    r = pa(['f0'], ['f15'], acts)
    assert r['length'] == 15 and r['plan'] == ['s%d' % i for i in range(15)]


def test_counter_state_space_is_searched_exhaustively():
    # 15 toggles: only the last order of switching reaches the goal; BFS must cover many states
    acts = [('t%d' % i, [], ['f%d' % i], []) for i in range(15)] + [('end', ['f%d' % i for i in range(6)], ['goal'], [])]
    r = pa([], ['goal'], acts)
    assert r['length'] == 7 and r['plan'] == ['t0', 't1', 't2', 't3', 't4', 't5', 'end']


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


NAME = 'must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -'
ACT = ('a', [], [], [])


def test_pins():
    err(pa, T, 'initial must be a list or tuple', 'ab', [], [])
    err(pa, T, 'goal must be a list or tuple', [], 'ab', [])
    err(pa, T, 'actions must be a list or tuple', [], [], 'ab')
    err(pa, V, 'initial count must be between 0 and 16', ['f%d' % i for i in range(17)], [], [])
    err(pa, V, 'goal count must be between 0 and 16', [], ['f%d' % i for i in range(17)], [])
    err(pa, V, 'action count must be between 0 and 40', [], [], [('a%d' % i, [], [], []) for i in range(41)])
    err(pa, T, 'fact must be a str', [1], [], [])
    err(pa, T, 'fact must be a str', [], [True], [])
    err(pa, V, 'fact ' + NAME, ['a b'], [], [])
    err(pa, V, 'fact ' + NAME, [], [''], [])
    err(pa, V, 'initial must not repeat', ['a', 'a'], [], [])
    err(pa, V, 'goal must not repeat', [], ['a', 'a'], [])
    for bad in ('abcd', 5, None, ('a', [], []), ('a', [], [], [], []), {'a': 1, 'b': 2, 'c': 3, 'd': 4}):
        err(pa, T, 'each action must be a (name, needs, adds, removes) quadruple', [], [], [ACT, bad])
    err(pa, T, 'action name must be a str', [], [], [(1, [], [], [])])
    err(pa, V, 'action name ' + NAME, [], [], [('a b', [], [], [])])
    err(pa, V, 'action names must not repeat', [], [], [ACT, ('a', [], ['x'], [])])
    for pos, key in enumerate(('needs', 'adds', 'removes'), 1):
        def mk(v):
            a = ['a', [], [], []]
            a[pos] = v
            return [tuple(a)]
        err(pa, T, key + ' must be a list or tuple', [], [], mk('ab'))
        err(pa, V, key + ' count must be between 0 and 6', [], [], mk(['p%d' % i for i in range(7)]))
        err(pa, T, 'fact must be a str', [], [], mk([1]))
        err(pa, V, 'fact ' + NAME, [], [], mk(['a b']))
        err(pa, V, key + ' must not repeat', [], [], mk(['p', 'p']))
    err(pa, V, 'an action cannot both add and remove the same fact', [], [], [('a', [], ['p'], ['p'])])


def test_caps_accepted_and_refused():
    pa(['f%d' % i for i in range(16)], ['f%d' % i for i in range(16)], [])
    pa([], [], [('a%d' % i, [], [], []) for i in range(40)])
    pa([], [], [('a', ['p%d' % i for i in range(6)], ['q%d' % i for i in range(6)], ['r%d' % i for i in range(4)])])
    pa(['x' * 30], ['A-z_9'], [])
    err(pa, V, 'at most 16 distinct fact names are supported', ['f%d' % i for i in range(16)], ['g'], [])
    err(pa, V, 'at most 16 distinct fact names are supported', [], ['f%d' % i for i in range(16)], [('a', ['z'], [], [])])
    err(pa, V, 'at most 16 distinct fact names are supported', [], [], [('a', ['n%d' % i for i in range(6)], ['m%d' % i for i in range(6)], ['k%d' % i for i in range(5)])])
    # action names do not count as facts
    pa(['f%d' % i for i in range(16)], [], [('only_an_action_name', [], [], [])])


def test_order_and_every_position():
    err(pa, V, 'initial must not repeat', ['a', 'a'], 'bad', 'bad')
    err(pa, T, 'goal must be a list or tuple', ['a'], 'bad', 'bad')
    err(pa, T, 'actions must be a list or tuple', ['a'], ['b'], 'bad')
    err(pa, T, 'each action must be a (name, needs, adds, removes) quadruple', [], [], [ACT, 5, ('a', ['q', 'q'], [], [])])
    err(pa, V, 'needs must not repeat', [], [], [('a', ['q', 'q'], 1, 1)])
    err(pa, T, 'adds must be a list or tuple', [], [], [('a', ['q'], 1, 1)])
    err(pa, V, 'an action cannot both add and remove the same fact', [], [], [('a', [], ['p'], ['p']), (1, 2, 3, 4)])
    for pos in range(3):
        acts = [('a', [], [], []), ('b', [], [], []), ('c', [], [], [])]
        acts[pos] = (7, [], [], [])
        err(pa, T, 'action name must be a str', [], [], acts)
        acts[pos] = ('x', [], [7], [])
        err(pa, T, 'fact must be a str', [], [], acts)
        acts[pos] = 7
        err(pa, T, 'each action must be a (name, needs, adds, removes) quadruple', [], [], acts)


def test_name_length_edges_for_facts_and_action_names():
    pa(['x' * 30], [], [('y' * 30, ['x' * 30], [], [])])
    err(pa, V, 'fact ' + NAME, ['x' * 31], [], [])
    err(pa, V, 'fact ' + NAME, [], ['x' * 31], [])
    err(pa, V, 'fact ' + NAME, [], [], [('a', ['x' * 31], [], [])])
    err(pa, V, 'action name ' + NAME, [], [], [('y' * 31, [], [], [])])
    err(pa, V, 'action name ' + NAME, [], [], [('', [], [], [])])
    assert pa(['x' * 30], ['z'], [('y' * 30, ['x' * 30], ['z'], [])])['plan'] == ['y' * 30]


def test_adding_an_already_true_fact_keeps_it_true():
    r = pa(['a'], ['a', 'b'], [('go', [], ['a', 'b'], [])])
    assert r == {'found': True, 'plan': ['go'], 'length': 1}
    # same for a fact that is already true and is also needed by the action
    assert pa(['a'], ['a', 'b'], [('go', ['a'], ['a', 'b'], [])])['plan'] == ['go']
    # an action that adds a fact twice over a run: the second run must not switch it off
    acts = [('one', [], ['a'], []), ('two', ['a'], ['a', 'b'], [])]
    assert pa([], ['a', 'b'], acts)['plan'] == ['one', 'two']
    assert pa(['a'], ['a', 'b'], acts)['plan'] == ['two']

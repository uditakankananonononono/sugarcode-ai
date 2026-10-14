"""Row572 hardening: exact-type subclass pins, full-message pins, brute-force
plan oracle, non-adjacent-order and mixed-validity witnesses, boundary
accepts, mutation sweep. Tests-only delta. No integer-typed slot exists (all
names are strings), so int-subclass/IntEnum pins are N/A; a str subclass with
lying __eq__/__hash__ is pinned instead. Containers, quadruples and name
lists accept BOTH exact list and exact tuple shape; subclasses are refused.

Equivalent mutants documented from the extended sweep (not chased):
  - 'm |= bit[n]' -> 'm ^= bit[n]': mask() only runs over repeat-free name
    lists (repeats are refused first), so no bit is set twice and OR == XOR.
  - 'facts = sorted(...)' -> 'facts = list(...)': bit positions change but
    stay internally consistent; state comparisons are pure equality, so the
    order of fact->bit assignment is not observable.
"""
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import action_plan as mod

SRC = pathlib.Path(mod.__file__).read_text()
T_, V_ = TypeError, ValueError


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


def _survives(battery, old, new):
    doc_end = SRC.index('"""', 3) + 3
    assert SRC.find(old) > doc_end, 'mutation target must be code, not the docstring'
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    code = compile(mutated, 'mutant', 'exec')  # a syntax error is not a kill
    def _timeout(*_):
        raise TimeoutError('mutant did not terminate')
    previous = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    return True


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class WeirdStr(str):
    def __eq__(self, other):
        return True

    def __hash__(self):
        return 0


NAME = 'must be 1 to 30 characters from A-Z, a-z, 0-9, _ and -'
ACT = ('a', [], [], [])
EAT = [('eat', ['food'], ['fed'], ['hungry']), ('buy', ['money'], ['food'], []), ('work', [], ['money'], [])]


def _apply(state, act):
    nm, needs, adds, rems = act
    if not set(needs) <= state:
        return None
    return (state - set(rems)) | set(adds)


def _oracle(init, goal, acts, max_len=5):
    s0 = set(init)
    if set(goal) <= s0:
        return {'found': True, 'plan': [], 'length': 0}
    for ln in range(1, max_len + 1):
        for seq in itertools.product(range(len(acts)), repeat=ln):
            s = set(init)
            for i in seq:
                s = _apply(s, acts[i])
                if s is None:
                    break
            if s is not None and set(goal) <= s:
                return {'found': True, 'plan': [acts[i][0] for i in seq], 'length': ln}
    return {'found': False, 'plan': None, 'length': None}


def _core(m):
    pa = m.plan_actions
    assert pa(['hungry'], ['fed'], EAT) == {'found': True, 'plan': ['work', 'buy', 'eat'], 'length': 3}
    assert pa(['hungry'], [], EAT) == {'found': True, 'plan': [], 'length': 0}
    assert pa(['hungry'], ['fed'], EAT[:2]) == {'found': False, 'plan': None, 'length': None}
    # tie break: equal-length plans prefer smaller positions from the left; shorter beats position
    assert pa([], ['g'], [('b1', [], ['g'], []), ('b2', [], ['g'], [])])['plan'] == ['b1']
    assert pa([], ['g'], [('slow', [], ['m'], []), ('mid', ['m'], ['g'], []), ('fast', [], ['g'], [])])['plan'] == ['fast']
    # removals happen before additions; goal must hold at the end, not midway
    assert pa(['y'], ['x'], [('a', [], ['x'], ['y'])]) == {'found': True, 'plan': ['a'], 'length': 1}
    assert pa(['hungry'], ['fed', 'hungry'], EAT)['found'] is False
    # exact chain: exhaustive state space, exact 7-step plan
    acts = [('s%d' % i, ['a%d' % i], ['a%d' % (i + 1)], []) for i in range(7)]
    assert pa(['a0'], ['a7'], acts) == {'found': True, 'plan': ['s%d' % i for i in range(7)], 'length': 7}
    # tuple-shaped containers, quadruples and name lists accepted
    assert pa(('hungry',), ('fed',), tuple(tuple(a) for a in EAT))['length'] == 3
    # boundary accepts
    pa(['f%d' % i for i in range(16)], ['f%d' % i for i in range(16)], [])
    pa([], [], [('a%d' % i, [], [], []) for i in range(40)])
    pa([], [], [('a', ['p%d' % i for i in range(6)], ['q%d' % i for i in range(6)], ['r%d' % i for i in range(4)])])
    pa(['x' * 30], ['A-z_9-0'], [])
    # seeded random oracle (brute force over action-position sequences)
    rng = random.Random(5721)
    for _ in range(150):
        names = ['f%d' % i for i in range(rng.randint(2, 5))]
        acts = []
        for j in range(rng.randint(0, 5)):
            acts.append(('a%d' % j,
                         rng.sample(names, rng.randint(0, 2)),
                         rng.sample(names, rng.randint(0, 2)),
                         rng.sample(names, rng.randint(0, 2))))
            while set(acts[-1][2]) & set(acts[-1][3]):
                acts[-1] = ('a%d' % j, acts[-1][1],
                            rng.sample(names, rng.randint(0, 2)), rng.sample(names, rng.randint(0, 2)))
        init = rng.sample(names, rng.randint(0, 2))
        goal = rng.sample(names, rng.randint(0, 2))
        assert pa(init, goal, acts) == _oracle(init, goal, acts)
    # full exact error messages
    _raises(T_, 'initial must be a list or tuple', pa, 'ab', [], [])
    _raises(T_, 'goal must be a list or tuple', pa, [], 'ab', [])
    _raises(T_, 'actions must be a list or tuple', pa, [], [], 'ab')
    _raises(V_, 'initial count must be between 0 and 16', pa, ['f%d' % i for i in range(17)], [], [])
    _raises(V_, 'goal count must be between 0 and 16', pa, [], ['f%d' % i for i in range(17)], [])
    _raises(V_, 'action count must be between 0 and 40', pa, [], [], [('a%d' % i, [], [], []) for i in range(41)])
    _raises(T_, 'fact must be a str', pa, [1], [], [])
    _raises(T_, 'fact must be a str', pa, [], [True], [])
    _raises(V_, 'fact ' + NAME, pa, ['a b'], [], [])
    _raises(V_, 'fact ' + NAME, pa, [], [''], [])
    _raises(V_, 'fact ' + NAME, pa, ['x' * 31], [], [])
    _raises(V_, 'fact ' + NAME, pa, [], ['x' * 31], [])
    _raises(V_, 'fact ' + NAME, pa, [], [], [('a', ['x' * 31], [], [])])
    _raises(V_, 'action name ' + NAME, pa, [], [], [('y' * 31, [], [], [])])
    _raises(V_, 'action name ' + NAME, pa, [], [], [('', [], [], [])])
    _raises(V_, 'initial must not repeat', pa, ['a', 'a'], [], [])
    _raises(V_, 'goal must not repeat', pa, [], ['a', 'a'], [])
    _raises(T_, 'each action must be a (name, needs, adds, removes) quadruple', pa, [], [], [('a', [], [])])
    _raises(T_, 'action name must be a str', pa, [], [], [(1, [], [], [])])
    _raises(V_, 'action name ' + NAME, pa, [], [], [('a b', [], [], [])])
    _raises(V_, 'action names must not repeat', pa, [], [], [ACT, ('a', [], ['x'], [])])
    for pos, key in enumerate(('needs', 'adds', 'removes'), 1):
        def mk(v):
            a = ['a', [], [], []]
            a[pos] = v
            return [tuple(a)]
        _raises(T_, key + ' must be a list or tuple', pa, [], [], mk('ab'))
        _raises(V_, key + ' count must be between 0 and 6', pa, [], [], mk(['p%d' % i for i in range(7)]))
        _raises(T_, 'fact must be a str', pa, [], [], mk([1]))
        _raises(V_, 'fact ' + NAME, pa, [], [], mk(['a b']))
        _raises(V_, key + ' must not repeat', pa, [], [], mk(['p', 'p']))
    _raises(V_, 'an action cannot both add and remove the same fact', pa, [], [], [('a', [], ['p'], ['p'])])
    _raises(V_, 'at most 16 distinct fact names are supported', pa, ['f%d' % i for i in range(16)], ['g'], [])


def _mix(m):
    pa = m.plan_actions
    # non-adjacent repeats (positions 0 and 3) and non-adjacent invalid entries
    _raises(V_, 'initial must not repeat', pa, ['a', 'b', 'c', 'a'], [], [])
    _raises(V_, 'goal must not repeat', pa, [], ['a', 'b', 'c', 'a'], [])
    _raises(V_, 'action names must not repeat', pa, [], [], [('a', [], [], []), ('b', [], [], []), ('c', [], [], []), ('a', [], ['x'], [])])
    _raises(V_, 'fact ' + NAME, pa, ['a', 'b', 'c!'], [], [])
    _raises(T_, 'fact must be a str', pa, [], [], [('a', ['p'], [], []), ('b', [2], [], [])])
    # mixed-validity: subclass and bad values in later entries after valid earlier entries
    _raises(T_, 'each action must be a (name, needs, adds, removes) quadruple', pa, [], [], [ACT, ('b', [], [], []), T(('c', [], [], []))])
    _raises(T_, 'action name must be a str', pa, [], [], [ACT, (S('b'), [], [], [])])
    _raises(T_, 'fact must be a str', pa, [], [], [ACT, ('b', [WeirdStr('p')], [], [])])
    _raises(T_, 'needs must be a list or tuple', pa, [], [], [ACT, ('b', L(['p']), [], [])])
    _raises(V_, 'an action cannot both add and remove the same fact', pa, [], [], [ACT, ('b', [], ['p'], ['p'])])
    # ordering: action validation precedes the fact cap
    _raises(V_, 'an action cannot both add and remove the same fact', pa, [], [],
            [('a', [], ['p'], ['p']), ('b', [], ['f%d' % i for i in range(6)], ['g%d' % i for i in range(6)])])
    _raises(V_, 'adds must not repeat', pa, ['f%d' % i for i in range(16)], ['g'], [('a', [], ['p', 'p'], [])])


def _late(m):
    pa = m.plan_actions
    _raises(T_, 'initial must be a list or tuple', pa, L(['a']), [], [])
    _raises(T_, 'initial must be a list or tuple', pa, T(('a',)), [], [])
    _raises(T_, 'goal must be a list or tuple', pa, [], L(['a']), [])
    _raises(T_, 'actions must be a list or tuple', pa, [], [], L([ACT]))
    _raises(T_, 'actions must be a list or tuple', pa, [], [], T((ACT,)))
    _raises(T_, 'each action must be a (name, needs, adds, removes) quadruple', pa, [], [], [L(['a', [], [], []])])
    _raises(T_, 'each action must be a (name, needs, adds, removes) quadruple', pa, [], [], [T(('a', [], [], []))])
    _raises(T_, 'needs must be a list or tuple', pa, [], [], [('a', L(['p']), [], [])])
    _raises(T_, 'adds must be a list or tuple', pa, [], [], [('a', [], T(('p',)), [])])
    _raises(T_, 'removes must be a list or tuple', pa, [], [], [('a', [], [], L(['p']))])
    _raises(T_, 'fact must be a str', pa, [S('a')], [], [])
    _raises(T_, 'fact must be a str', pa, [], [WeirdStr('a')], [])
    _raises(T_, 'action name must be a str', pa, [], [], [(S('a'), [], [], [])])
    # subclass refused before any cap
    _raises(T_, 'initial must be a list or tuple', pa, L(['f%d' % i for i in range(17)]), [], [])
    _raises(T_, 'actions must be a list or tuple', pa, [], [], L([ACT] * 41))
    _raises(T_, 'needs must be a list or tuple', pa, [], [], [('a', L(['p'] * 7), [], [])])
    _raises(T_, 'fact must be a str', pa, [S('x' * 31)], [], [])
    # exact list-shaped and tuple-shaped acceptance counterparts
    assert pa(list(['a']), list(['b']), [list(['go', list([]), list(['b']), list([])])])['plan'] == ['go']
    assert pa(tuple(['a']), tuple(['b']), [tuple(['go', tuple([]), tuple(['b']), tuple([])])])['plan'] == ['go']


def battery(m):
    _core(m)
    _mix(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('type(v) is not str', 'not isinstance(v, str)'),
    ('type(vals) not in (list, tuple)', 'not isinstance(vals, (list, tuple))'),
    ('type(actions) not in (list, tuple)', 'not isinstance(actions, (list, tuple))'),
    ('type(a) not in (list, tuple) or len(a) != 4', 'not isinstance(a, (list, tuple)) or len(a) != 4'),
    ('MAX_SET = 16', 'MAX_SET = 17'),
    ('MAX_ACTIONS = 40', 'MAX_ACTIONS = 41'),
    ('MAX_LIST = 6', 'MAX_LIST = 7'),
    ('MAX_FACTS = 16', 'MAX_FACTS = 17'),
    ('not 1 <= len(v) <= 30', 'not 1 <= len(v) <= 31'),
    ("frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')",
     "frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_')"),
    ('if n in out', 'if False'),
    ('if nm in used', 'if False'),
    ('if set(adds) & set(rems)', 'if False'),
    ('if len(facts) > MAX_FACTS', 'if len(facts) >= MAX_FACTS'),
    ('t = (s & ~r) | a', 't = s | a'),
    ('t = (s & ~r) | a', 't = s & ~r'),
    ('if s & n == n', 'if s & n'),
    ('for i, (n, a, r) in enumerate(ops)', 'for i, (n, a, r) in reversed(list(enumerate(ops)))'),
    ('s = queue.popleft()', 's = queue.pop()'),
    ('if start & want == want', 'if False'),
    ('if t not in came', 'if True'),
    ('seq.reverse()', 'pass'),
    ("return {'found': False, 'plan': None, 'length': None}", "return {'found': True, 'plan': [], 'length': 0}"),
    ("' must be a list or tuple'", "' must be a list'"),
    ("' count must be between 0 and %d' % limit", "' count must be at most %d' % limit"),
    ("' must not repeat'", "' must not repeat.'"),
    ("'an action cannot both add and remove the same fact'", "'an action cannot add and remove the same fact'"),
    ("'at most 16 distinct fact names are supported'", "'at most 16 fact names are supported'"),
    ("'each action must be a (name, needs, adds, removes) quadruple'", "'each action must be a quadruple'"),
    ("'action names must not repeat'", "'action names must not repeat themselves'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

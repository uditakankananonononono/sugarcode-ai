import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import whale_optimization as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


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


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingI(int):
    def __index__(self): return 1


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: bubble windowing over supplied rows, no real whales'
    assert len(mod.NOT_CLAIMED) >= 4 and 'bubble-net feeding' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_NAME, mod.MAX_BUBBLE) == (100, 8, 10)


def _oracle(rows):
    named = set()
    for whale, amount in rows:
        named.add(whale)
    nets = 0
    for i in range(len(rows) - 2):
        (first, one), (second, two), (third, three) = rows[i:i + 3]
        if first == second == third and one < two < three:
            nets += 1
    return {'total': len(rows), 'whales': len(named),
            'bubbles': sum(a for w, a in rows), 'nets': nets}


def _core(m):
    # three rising rows from one whale make a net
    assert m.bubble([('a', 1), ('a', 2), ('a', 3)])['nets'] == 1
    # overlapping windows each count
    assert m.bubble([('a', 1), ('a', 2), ('a', 3), ('a', 4)]) == {
        'total': 4, 'whales': 1, 'bubbles': 10, 'nets': 2}
    # the increase must be strict
    assert m.bubble([('a', 5), ('a', 5), ('a', 5)])['nets'] == 0
    assert m.bubble([('a', 1), ('a', 2), ('a', 2)])['nets'] == 0
    # one whale across all three rows, not two
    assert m.bubble([('a', 1), ('a', 2), ('b', 3)])['nets'] == 0
    assert m.bubble([('a', 1), ('b', 2), ('b', 3)])['nets'] == 0
    # a dip breaks the rise
    assert m.bubble([('a', 1), ('a', 3), ('a', 2)])['nets'] == 0
    # fewer than three rows cannot net
    assert m.bubble([('a', 1), ('a', 2)])['nets'] == 0
    # an empty record has nothing
    assert m.bubble([]) == {'total': 0, 'whales': 0, 'bubbles': 0, 'nets': 0}
    # tuples accepted
    assert m.bubble((('a', 1), ('a', 2), ('a', 3)))['nets'] == 1
    rng = random.Random(935)
    names = ['w%d' % i for i in range(3)]
    for _ in range(400):
        rows = [(rng.choice(names), rng.randint(0, 10))
                for _ in range(rng.randint(0, 7))]
        assert m.bubble(rows) == _oracle(rows)


def _late(m):
    STM = 'whales must be a list or tuple'
    CAP = 'whales must contain at most 100 entries'
    ROW = 'each row must be a (whale, bubble) row'
    NAM = 'whale must be a string of 1 to 8 characters'
    BUB = 'bubble must be an integer from 0 to 10'
    good = [('a', 1)]
    for bad in ('ab', None, 5.5, {}, {1}, L(good), T(tuple(good))):
        _raises(TypeError, STM, m.bubble, bad)
    _raises(TypeError, STM, m.bubble, L(good * 101))   # subclass refused before the cap
    _raises(ValueError, CAP, m.bubble, good * 101)
    assert m.bubble(good * 100)['total'] == 100
    for bad in ([0, 1], ['ab'], [('a',)], [('a', 1, 'x')],
                [L(['a', 1])], [T(('a', 1))]):
        _raises(ValueError, ROW, m.bubble, bad)
    for bad in (True, False, I(1), 1.0, None, ['a'], '', 'a' * 9):
        _raises(ValueError, NAM, m.bubble, [(bad, 1)])
        _raises(ValueError, NAM, m.bubble, [('a', 1), (bad, 1)])
    assert m.bubble([('a', 1)])['total'] == 1            # single char accepted
    assert m.bubble([('a' * 8, 1)])['total'] == 1        # 8 chars accepted
    for bad in (True, False, I(1), LyingI(1), S('1'), 1.0, None, 'x', [1],
                -1, 11, 100):
        _raises(ValueError, BUB, m.bubble, [('a', bad)])
        _raises(ValueError, BUB, m.bubble, [('b', 1), ('a', bad)])
    assert m.bubble([('a', 0)])['bubbles'] == 0          # 0 accepted
    assert m.bubble([('a', 10)])['bubbles'] == 10        # 10 accepted
    # order: container, cap, rows; first bad row reports first
    _raises(ValueError, CAP, m.bubble, [('zz', 'bogus')] * 101)
    _raises(ValueError, NAM, m.bubble, [('z' * 9, 'bogus'), ('a', 1)])
    _raises(ValueError, NAM, m.bubble,
            [('a', 1), ('z' * 9, 1), ('b', 'bogus')])
    _raises(ValueError, BUB, m.bubble, [('a', 1), ('b', 'bogus')])
    _raises(ValueError, NAM, m.bubble, [('a', 1), ('z' * 9, 'bogus')])
    _raises(ValueError, BUB, m.bubble, [('a', 1), ('b', 11)])
    # dynamic equal strings are accepted
    dyn = ''.join(['wha', 'le'])
    assert m.bubble([(dyn, 1), (dyn, 2), (dyn, 3)]) == {
        'total': 3, 'whales': 1, 'bubbles': 6, 'nets': 1}
    _raises(ValueError, NAM, m.bubble, [(LyingS('ab'), 1)])
    # 'zz' is a valid two-char whale name
    assert m.bubble([('zz', 5)]) == {'total': 1, 'whales': 1,
        'bubbles': 5, 'nets': 0}


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    rows = [('a', 1), ('a', 2), ('a', 3)]
    assert mod.bubble(rows)['nets'] == 1
    assert rows == [('a', 1), ('a', 2), ('a', 3)]
    assert mod.bubble([('a', 3), ('a', 2), ('a', 1)])['nets'] == 0


MUTANTS = [
    ("    if type(whales) not in (list, tuple):",
     "    if not isinstance(whales, (list, tuple)):"),
    ("    if len(whales) > MAX_ROWS:", "    if len(whales) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if type(row) not in (list, tuple) and len(row) != 2:"),
    ("        if type(whale) is not str or not 1 <= len(whale) <= MAX_NAME:",
     "        if type(whale) is not str or not 1 < len(whale) <= MAX_NAME:"),
    ("not 1 <= len(whale) <= MAX_NAME", "not 1 <= len(whale) < MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("        if type(amount) is not int or not 0 <= amount <= MAX_BUBBLE:",
     "        if not isinstance(amount, int) or not 0 <= amount <= MAX_BUBBLE:"),
    ("        if type(amount) is not int or not 0 <= amount <= MAX_BUBBLE:",
     "        if type(amount) is not int or not 0 < amount <= MAX_BUBBLE:"),
    ("not 0 <= amount <= MAX_BUBBLE", "not 0 <= amount < MAX_BUBBLE"),
    ("MAX_BUBBLE = 10", "MAX_BUBBLE = 11"),
    ("    rows = []", "    rows = [('zz', 5)]"),
    ("    named = set()", "    named = {'zz'}"),
    ("    nets = 0", "    nets = 1"),
    ("    for i in range(len(rows) - 2):", "    for i in range(len(rows) - 1):"),
    ("    for i in range(len(rows) - 2):", "    for i in range(len(rows) - 3):"),
    ("        if first == second == third and one < two < three:",
     "        if first == second and one < two < three:"),
    ("        if first == second == third and one < two < three:",
     "        if first == second == third and one <= two < three:"),
    ("        if first == second == third and one < two < three:",
     "        if first == second == third and one < two <= three:"),
    ("        if first == second == third and one < two < three:",
     "        if first == second == third and one < two:"),
    ("        if first == second == third and one < two < three:",
     "        if first == second == third and one > two > three:"),
    ("            nets += 1", "            nets += 2"),
    ("        (first, one), (second, two), (third, three) = rows[i:i + 3]",
     "        (first, one), (second, two), (third, three) = rows[i:i + 2]"),
    ("    return {'total': len(rows), 'whales': len(named),",
     "    return {'total': len(rows) + 1, 'whales': len(named),"),
    ("    return {'total': len(rows), 'whales': len(named),",
     "    return {'total': len(rows), 'whales': len(named) + 1,"),
    ("            'bubbles': sum(amount for whale, amount in rows),",
     "            'bubbles': sum(amount for whale, amount in rows) + 1,"),
    ("            'bubbles': sum(amount for whale, amount in rows),",
     "            'bubbles': len(rows),"),
    ("            'nets': nets}", "            'nets': nets + 1}"),
    ("            'nets': nets}", "            'nets': len(named)}"),
    ("        raise TypeError('whales must be a list or tuple')",
     "        raise ValueError('whales must be a list or tuple')"),
    ("        raise ValueError('whales must contain at most 100 entries')",
     "        raise ValueError('whales must contain at most 101 entries')"),
    ("        raise ValueError('whale must be a string of 1 to 8 characters')",
     "        raise ValueError('whale must be a string of 1 to 9 characters')"),
    ("        raise ValueError('bubble must be an integer from 0 to 10')",
     "        raise ValueError('bubble must be an integer from 0 to 11')"),
    ("    for row in whales:\n        if type(row) not in (list, tuple) or len(row) != 2:",
     "    for row in reversed(whales):\n        if type(row) not in (list, tuple) or len(row) != 2:"),
    ("        rows.append((whale, amount))", "        rows.append((amount, whale))"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutants_killed(old, new):
    assert not _survives(battery, old, new), 'SURVIVED: %s' % old

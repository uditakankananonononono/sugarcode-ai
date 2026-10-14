import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import artificial_life as mod

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
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: meal walking over supplied rows, no real life'
    assert len(mod.NOT_CLAIMED) >= 4 and 'living systems' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_NAME) == (100, 8)


def _oracle(rows):
    energy = {}
    starved = set()
    for cell, meal in rows:
        level = energy.get(cell, 0) + (1 if meal == 'feed' else -1)
        energy[cell] = level
        if level < 0:
            starved.add(cell)
    feed = sum(1 for c, m in rows if m == 'feed')
    return {'feed': feed, 'starve': len(rows) - feed, 'total': len(rows),
            'starved': sorted(starved)}


def _core(m):
    # energy below zero starves a cell
    assert m.live([('a', 'starve')]) == {
        'feed': 0, 'starve': 1, 'total': 1, 'starved': ['a']}
    # landing exactly on zero does not
    assert m.live([('a', 'feed'), ('a', 'starve')]) == {
        'feed': 1, 'starve': 1, 'total': 2, 'starved': []}
    # order matters: feed first can buffer a starve
    assert m.live([('a', 'feed'), ('a', 'starve'), ('a', 'starve')]) == {
        'feed': 1, 'starve': 2, 'total': 3, 'starved': ['a']}
    # recovery after starving still counts as starved
    assert m.live([('a', 'starve'), ('a', 'feed'), ('a', 'feed')]) == {
        'feed': 2, 'starve': 1, 'total': 3, 'starved': ['a']}
    # starved comes back sorted
    got = m.live([('b', 'starve'), ('a', 'starve'), ('c', 'feed')])
    assert got == {'feed': 1, 'starve': 2, 'total': 3, 'starved': ['a', 'b']}
    # an empty record has nothing
    assert m.live([]) == {'feed': 0, 'starve': 0, 'total': 0, 'starved': []}
    # tuples accepted
    assert m.live((('a', 'starve'),))['starved'] == ['a']
    rng = random.Random(937)
    names = ['c%d' % i for i in range(4)]
    meals = ['feed', 'starve']
    for _ in range(400):
        rows = [(rng.choice(names), rng.choice(meals))
                for _ in range(rng.randint(0, 7))]
        assert m.live(rows) == _oracle(rows)


def _late(m):
    STM = 'cells must be a list or tuple'
    CAP = 'cells must contain at most 100 entries'
    ROW = 'each row must be a (cell, meal) row'
    NAM = 'cell must be a string of 1 to 8 characters'
    MEA = "meal must be 'feed' or 'starve'"
    good = [('a', 'feed')]
    for bad in ('ab', None, 5.5, {}, {1}, L(good), T(tuple(good))):
        _raises(TypeError, STM, m.live, bad)
    _raises(TypeError, STM, m.live, L(good * 101))   # subclass refused before the cap
    _raises(ValueError, CAP, m.live, good * 101)
    assert m.live(good * 100)['total'] == 100
    for bad in ([0, 1], ['ab'], [('a',)], [('a', 'feed', 'x')],
                [L(['a', 'feed'])], [T(('a', 'feed'))]):
        _raises(ValueError, ROW, m.live, bad)
    for bad in (True, False, I(1), LyingI(2), S('a'), 1.0, None, ['a'], '',
                'a' * 9):
        _raises(ValueError, NAM, m.live, [(bad, 'feed')])
        _raises(ValueError, NAM, m.live, [('a', 'starve'), (bad, 'feed')])
    assert m.live([('a', 'starve')])['total'] == 1       # single char accepted
    assert m.live([('a' * 8, 'starve')])['total'] == 1    # 8 chars accepted
    for bad in (True, I(1), S('feed'), 1.0, None, 'FEED', 'feeds',
                'fed', 'starves', 'starved', ''):
        _raises(ValueError, MEA, m.live, [('a', bad)])
        _raises(ValueError, MEA, m.live, [('b', 'starve'), ('a', bad)])
    # order: container, cap, rows; first bad row reports first
    _raises(ValueError, CAP, m.live, [('zz', 'bogus')] * 101)
    _raises(ValueError, NAM, m.live, [('z' * 9, 'bogus'), ('a', 'feed')])
    _raises(ValueError, NAM, m.live,
            [('a', 'feed'), ('z' * 9, 'starve'), ('b', 'bogus')])
    _raises(ValueError, MEA, m.live, [('a', 'feed'), ('b', 'bogus')])
    _raises(ValueError, NAM, m.live, [('a', 'feed'), ('z' * 9, 'bogus')])
    # dynamic equal strings are accepted
    dyn_f = ''.join(['fe', 'ed'])
    dyn_s = ''.join(['star', 've'])
    got = m.live([('a', dyn_f), ('a', dyn_s), ('a', dyn_s)])
    assert got == {'feed': 1, 'starve': 2, 'total': 3, 'starved': ['a']}
    assert m.live([('a', dyn_f), ('a', dyn_f)]) == {'feed': 2, 'starve': 0,
        'total': 2, 'starved': []}
    _raises(ValueError, MEA, m.live, [('a', LyingS('feed'))])
    # 'zz' is a valid two-char cell name
    assert m.live([('zz', 'starve')]) == {'feed': 0, 'starve': 1,
        'total': 1, 'starved': ['zz']}
    assert m.live([('zz', 'feed')]) == {'feed': 1, 'starve': 0,
        'total': 1, 'starved': []}


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    rows = [('a', 'feed'), ('a', 'starve'), ('a', 'starve')]
    assert mod.live(rows)['starved'] == ['a']
    assert rows == [('a', 'feed'), ('a', 'starve'), ('a', 'starve')]
    got1 = mod.live(rows)
    got2 = mod.live([('a', 'feed'), ('a', 'feed'), ('a', 'starve')])
    assert got1['starved'] == ['a'] and got2['starved'] == []


MUTANTS = [
    ("    if type(cells) not in (list, tuple):",
     "    if not isinstance(cells, (list, tuple)):"),
    ("    if len(cells) > MAX_ROWS:", "    if len(cells) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if type(row) not in (list, tuple) and len(row) != 2:"),
    ("        if type(cell) is not str or not 1 <= len(cell) <= MAX_NAME:",
     "        if type(cell) is not str or not 1 < len(cell) <= MAX_NAME:"),
    ("not 1 <= len(cell) <= MAX_NAME", "not 1 <= len(cell) < MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("        if type(meal) is not str or meal not in MEALS:",
     "        if type(meal) is not str and meal not in MEALS:"),
    ("        if type(meal) is not str or meal not in MEALS:",
     "        if type(meal) is not str or meal not in ('feed',):"),
    ("    rows = []", "    rows = [('zz', 'feed')]"),
    ("    rows = []", "    rows = [('q', 'starve')]"),
    ("    energy = {}", "    energy = {'zz': 5}"),
    ("    energy = {}", "    energy = {'zz': -5}"),
    ("    starved = set()", "    starved = {'zz'}"),
    ("        level = energy.get(cell, 0) + (1 if meal == 'feed' else -1)",
     "        level = energy.get(cell, 0) + (-1 if meal == 'feed' else 1)"),
    ("        level = energy.get(cell, 0) + (1 if meal == 'feed' else -1)",
     "        level = energy.get(cell, 0) + (2 if meal == 'feed' else -1)"),
    ("        level = energy.get(cell, 0) + (1 if meal == 'feed' else -1)",
     "        level = energy.get(cell, 0) + (1 if meal == 'feed' else -2)"),
    ("        level = energy.get(cell, 0) + (1 if meal == 'feed' else -1)",
     "        level = energy.get(cell, 0) + (1 if meal is 'feed' else -1)"),
    ("        level = energy.get(cell, 0) + (1 if meal == 'feed' else -1)",
     "        level = energy.get(cell, 1) + (1 if meal == 'feed' else -1)"),
    ("        if level < 0:\n            starved.add(cell)",
     "        if level <= 0:\n            starved.add(cell)"),
    ("        if level < 0:\n            starved.add(cell)",
     "        if level < -1:\n            starved.add(cell)"),
    ("        if level < 0:\n            starved.add(cell)",
     "        if level < 0:\n            energy[cell] = 0"),
    ("    feed = sum(1 for cell, meal in rows if meal == 'feed')",
     "    feed = sum(1 for cell, meal in rows if meal == 'starve')"),
    ("    feed = sum(1 for cell, meal in rows if meal == 'feed')",
     "    feed = sum(1 for cell, meal in rows if meal is 'feed')"),
    ("    feed = sum(1 for cell, meal in rows if meal == 'feed')",
     "    feed = sum(1 for cell, meal in rows)"),
    ("    return {'feed': feed, 'starve': len(rows) - feed,",
     "    return {'feed': feed, 'starve': len(rows) - feed + 1,"),
    ("    return {'feed': feed, 'starve': len(rows) - feed,",
     "    return {'feed': len(rows) - feed, 'starve': feed,"),
    ("            'total': len(rows), 'starved': sorted(starved)}",
     "            'total': len(rows) + 1, 'starved': sorted(starved)}"),
    ("            'total': len(rows), 'starved': sorted(starved)}",
     "            'total': len(rows), 'starved': list(starved)}"),
    ("            'total': len(rows), 'starved': sorted(starved)}",
     "            'total': len(rows), 'starved': sorted(energy)}"),
    ("        raise TypeError('cells must be a list or tuple')",
     "        raise ValueError('cells must be a list or tuple')"),
    ("        raise ValueError('cells must contain at most 100 entries')",
     "        raise ValueError('cells must contain at most 101 entries')"),
    ("        raise ValueError('cell must be a string of 1 to 8 characters')",
     "        raise ValueError('cell must be a string of 1 to 9 characters')"),
    ("        raise ValueError(\"meal must be 'feed' or 'starve'\")",
     "        raise ValueError(\"meal must be 'feed' or 'starves'\")"),
    ("    for row in cells:\n        if type(row) not in (list, tuple) or len(row) != 2:",
     "    for row in reversed(cells):\n        if type(row) not in (list, tuple) or len(row) != 2:"),
    ("    for cell, meal in rows:\n        level = energy.get(cell, 0)",
     "    for cell, meal in reversed(rows):\n        level = energy.get(cell, 0)"),
    ("        rows.append((cell, meal))", "        rows.append((meal, cell))"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutants_killed(old, new):
    assert not _survives(battery, old, new), 'SURVIVED: %s' % old

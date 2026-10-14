import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import genetic_programming as mod

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
    assert mod.SCOPE == 'PARTIAL: fitness comparison over supplied rows, no real evolution'
    assert len(mod.NOT_CLAIMED) >= 4 and 'program synthesis' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_NAME, mod.MAX_FITNESS) == (100, 8, 10)


def _oracle(rows):
    firsts = {}
    lasts = {}
    for program, fitness in rows:
        if program not in firsts:
            firsts[program] = fitness
        lasts[program] = fitness
    return {'total': len(rows), 'programs': len(lasts),
            'fitness': sum(f for p, f in rows),
            'evolved': sorted(p for p in lasts if lasts[p] > firsts[p])}


def _core(m):
    # latest above first is evolved
    assert m.evolve([('a', 3), ('a', 7)]) == {
        'total': 2, 'programs': 1, 'fitness': 10, 'evolved': ['a']}
    # equal is not
    assert m.evolve([('a', 5), ('a', 5)]) == {
        'total': 2, 'programs': 1, 'fitness': 10, 'evolved': []}
    # lower is not
    assert m.evolve([('a', 9), ('a', 2)]) == {
        'total': 2, 'programs': 1, 'fitness': 11, 'evolved': []}
    # a single row is never evolved
    assert m.evolve([('a', 10)]) == {
        'total': 1, 'programs': 1, 'fitness': 10, 'evolved': []}
    # the middle rows do not decide, first and latest do
    assert m.evolve([('a', 3), ('a', 9), ('a', 4)]) == {
        'total': 3, 'programs': 1, 'fitness': 16, 'evolved': ['a']}
    # evolved comes back sorted
    got = m.evolve([('b', 1), ('b', 2), ('a', 5), ('a', 8), ('c', 9),
                    ('c', 1)])
    assert got == {'total': 6, 'programs': 3, 'fitness': 26,
                   'evolved': ['a', 'b']}
    # an empty record has nothing
    assert m.evolve([]) == {'total': 0, 'programs': 0, 'fitness': 0,
                            'evolved': []}
    # tuples accepted
    assert m.evolve((('a', 1), ('a', 2)))['evolved'] == ['a']
    rng = random.Random(938)
    names = ['p%d' % i for i in range(5)]
    for _ in range(400):
        rows = [(rng.choice(names), rng.randint(0, 10))
                for _ in range(rng.randint(0, 7))]
        assert m.evolve(rows) == _oracle(rows)


def _late(m):
    STM = 'programs must be a list or tuple'
    CAP = 'programs must contain at most 100 entries'
    ROW = 'each row must be a (program, fitness) row'
    NAM = 'program must be a string of 1 to 8 characters'
    FIT = 'fitness must be an integer from 0 to 10'
    good = [('a', 1)]
    for bad in ('ab', None, 5.5, {}, {1}, L(good), T(tuple(good))):
        _raises(TypeError, STM, m.evolve, bad)
    _raises(TypeError, STM, m.evolve, L(good * 101))   # subclass refused before the cap
    _raises(ValueError, CAP, m.evolve, good * 101)
    assert m.evolve(good * 100)['total'] == 100
    for bad in ([0, 1], ['ab'], [('a',)], [('a', 1, 'x')],
                [L(['a', 1])], [T(('a', 1))]):
        _raises(ValueError, ROW, m.evolve, bad)
    for bad in (True, False, I(1), 1.0, None, ['a'], '', 'a' * 9):
        _raises(ValueError, NAM, m.evolve, [(bad, 1)])
        _raises(ValueError, NAM, m.evolve, [('a', 1), (bad, 1)])
    assert m.evolve([('a', 1)])['total'] == 1            # single char accepted
    assert m.evolve([('a' * 8, 1)])['total'] == 1        # 8 chars accepted
    for bad in (True, False, I(1), LyingI(1), S('1'), 1.0, None, 'x', [1],
                -1, 11, 100):
        _raises(ValueError, FIT, m.evolve, [('a', bad)])
        _raises(ValueError, FIT, m.evolve, [('b', 1), ('a', bad)])
    assert m.evolve([('a', 0)])['fitness'] == 0          # 0 accepted
    assert m.evolve([('a', 10)])['fitness'] == 10        # 10 accepted
    # order: container, cap, rows; first bad row reports first
    _raises(ValueError, CAP, m.evolve, [('zz', 'bogus')] * 101)
    _raises(ValueError, NAM, m.evolve, [('z' * 9, 'bogus'), ('a', 1)])
    _raises(ValueError, NAM, m.evolve,
            [('a', 1), ('z' * 9, 1), ('b', 'bogus')])
    _raises(ValueError, FIT, m.evolve, [('a', 1), ('b', 'bogus')])
    _raises(ValueError, NAM, m.evolve, [('a', 1), ('z' * 9, 'bogus')])
    _raises(ValueError, FIT, m.evolve, [('a', 1), ('b', 11)])
    # dynamic equal strings are accepted
    dyn = ''.join(['pro', 'g'])
    assert m.evolve([(dyn, 2), (dyn, 6)]) == {
        'total': 2, 'programs': 1, 'fitness': 8, 'evolved': [dyn]}
    _raises(ValueError, NAM, m.evolve, [(LyingS('ab'), 1)])
    # 'zz' is a valid two-char program name
    assert m.evolve([('zz', 5), ('zz', 6)]) == {'total': 2, 'programs': 1,
        'fitness': 11, 'evolved': ['zz']}
    assert m.evolve([('zz', 6), ('zz', 5)]) == {'total': 2, 'programs': 1,
        'fitness': 11, 'evolved': []}


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    rows = [('a', 3), ('a', 7)]
    assert mod.evolve(rows)['evolved'] == ['a']
    assert rows == [('a', 3), ('a', 7)]
    got1 = mod.evolve(rows)
    got2 = mod.evolve([('a', 7), ('a', 3)])
    assert got1['evolved'] == ['a'] and got2['evolved'] == []


MUTANTS = [
    ("    if type(programs) not in (list, tuple):",
     "    if not isinstance(programs, (list, tuple)):"),
    ("    if len(programs) > MAX_ROWS:", "    if len(programs) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if type(row) not in (list, tuple) and len(row) != 2:"),
    ("        if type(program) is not str or not 1 <= len(program) <= MAX_NAME:",
     "        if type(program) is not str or not 1 < len(program) <= MAX_NAME:"),
    ("not 1 <= len(program) <= MAX_NAME", "not 1 <= len(program) < MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("        if type(fitness) is not int or not 0 <= fitness <= MAX_FITNESS:",
     "        if not isinstance(fitness, int) or not 0 <= fitness <= MAX_FITNESS:"),
    ("        if type(fitness) is not int or not 0 <= fitness <= MAX_FITNESS:",
     "        if type(fitness) is not int or not 0 < fitness <= MAX_FITNESS:"),
    ("not 0 <= fitness <= MAX_FITNESS", "not 0 <= fitness < MAX_FITNESS"),
    ("MAX_FITNESS = 10", "MAX_FITNESS = 11"),
    ("    rows = []", "    rows = [('zz', 5)]"),
    ("    firsts = {}", "    firsts = {'zz': 10}"),
    ("    firsts = {}", "    firsts = {'zz': 0}"),
    ("    lasts = {}", "    lasts = {'zz': 10}"),
    ("        if program not in firsts:\n            firsts[program] = fitness",
     "        if program in firsts:\n            firsts[program] = fitness"),
    ("        lasts[program] = fitness", "        lasts[fitness] = program"),
    ("    evolved = sorted(p for p in lasts if lasts[p] > firsts[p])",
     "    evolved = sorted(p for p in lasts if lasts[p] >= firsts[p])"),
    ("    evolved = sorted(p for p in lasts if lasts[p] > firsts[p])",
     "    evolved = sorted(p for p in lasts if lasts[p] < firsts[p])"),
    ("    evolved = sorted(p for p in lasts if lasts[p] > firsts[p])",
     "    evolved = sorted(p for p in lasts if firsts[p] > lasts[p])"),
    ("    evolved = sorted(p for p in lasts if lasts[p] > firsts[p])",
     "    evolved = list(p for p in lasts if lasts[p] > firsts[p])"),
    ("    evolved = sorted(p for p in lasts if lasts[p] > firsts[p])",
     "    evolved = sorted(lasts)"),
    ("    return {'total': len(rows), 'programs': len(lasts),",
     "    return {'total': len(rows) + 1, 'programs': len(lasts),"),
    ("    return {'total': len(rows), 'programs': len(lasts),",
     "    return {'total': len(rows), 'programs': len(lasts) + 1,"),
    ("            'fitness': sum(fitness for program, fitness in rows),",
     "            'fitness': sum(fitness for program, fitness in rows) + 1,"),
    ("            'fitness': sum(fitness for program, fitness in rows),",
     "            'fitness': len(rows),"),
    ("        raise TypeError('programs must be a list or tuple')",
     "        raise ValueError('programs must be a list or tuple')"),
    ("        raise ValueError('programs must contain at most 100 entries')",
     "        raise ValueError('programs must contain at most 101 entries')"),
    ("        raise ValueError('program must be a string of 1 to 8 characters')",
     "        raise ValueError('program must be a string of 1 to 9 characters')"),
    ("        raise ValueError('fitness must be an integer from 0 to 10')",
     "        raise ValueError('fitness must be an integer from 0 to 11')"),
    ("    for row in programs:\n        if type(row) not in (list, tuple) or len(row) != 2:",
     "    for row in reversed(programs):\n        if type(row) not in (list, tuple) or len(row) != 2:"),
    ("    for program, fitness in rows:\n        if program not in firsts:",
     "    for program, fitness in reversed(rows):\n        if program not in firsts:"),
    ("        rows.append((program, fitness))", "        rows.append((fitness, program))"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutants_killed(old, new):
    assert not _survives(battery, old, new), 'SURVIVED: %s' % old

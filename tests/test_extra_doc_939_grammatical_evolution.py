import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import grammatical_evolution as mod

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
    assert mod.SCOPE == 'PARTIAL: codon mapping over supplied rows, no real evolution'
    assert len(mod.NOT_CLAIMED) >= 4 and 'grammar design' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_NAME, mod.MAX_CODON,
            mod.PRODUCTIONS) == (100, 8, 10, 4)


def _oracle(rows):
    sums = {}
    for rule, codon in rows:
        sums[rule] = sums.get(rule, 0) + codon
    return {'total': len(rows), 'rules': len(sums),
            'codons': sum(c for r, c in rows),
            'choices': {r: t % 4 for r, t in sums.items()}}


def _core(m):
    # the choice is the codon sum modulo 4
    assert m.map_codons([('a', 3), ('a', 4)]) == {
        'total': 2, 'rules': 1, 'codons': 7, 'choices': {'a': 3}}
    # sums wrap around 4
    assert m.map_codons([('a', 10), ('a', 10)])['choices'] == {'a': 0}
    assert m.map_codons([('a', 10), ('a', 10), ('a', 1)])['choices'] == {'a': 1}
    # each rule gets its own choice
    got = m.map_codons([('a', 3), ('b', 10), ('a', 4), ('c', 2)])
    assert got == {'total': 4, 'rules': 3, 'codons': 19,
                   'choices': {'a': 3, 'b': 2, 'c': 2}}
    # a single codon maps directly
    assert m.map_codons([('a', 5)])['choices'] == {'a': 1}
    # an empty record has nothing
    assert m.map_codons([]) == {'total': 0, 'rules': 0, 'codons': 0,
                                'choices': {}}
    # tuples accepted
    assert m.map_codons((('a', 1), ('a', 2)))['choices'] == {'a': 3}
    rng = random.Random(939)
    names = ['r%d' % i for i in range(5)]
    for _ in range(400):
        rows = [(rng.choice(names), rng.randint(0, 10))
                for _ in range(rng.randint(0, 7))]
        assert m.map_codons(rows) == _oracle(rows)


def _late(m):
    STM = 'rules must be a list or tuple'
    CAP = 'rules must contain at most 100 entries'
    ROW = 'each row must be a (rule, codon) row'
    NAM = 'rule must be a string of 1 to 8 characters'
    COD = 'codon must be an integer from 0 to 10'
    good = [('a', 1)]
    for bad in ('ab', None, 5.5, {}, {1}, L(good), T(tuple(good))):
        _raises(TypeError, STM, m.map_codons, bad)
    _raises(TypeError, STM, m.map_codons, L(good * 101))   # subclass refused before the cap
    _raises(ValueError, CAP, m.map_codons, good * 101)
    assert m.map_codons(good * 100)['total'] == 100
    for bad in ([0, 1], ['ab'], [('a',)], [('a', 1, 'x')],
                [L(['a', 1])], [T(('a', 1))]):
        _raises(ValueError, ROW, m.map_codons, bad)
    for bad in (True, False, I(1), 1.0, None, ['a'], '', 'a' * 9):
        _raises(ValueError, NAM, m.map_codons, [(bad, 1)])
        _raises(ValueError, NAM, m.map_codons, [('a', 1), (bad, 1)])
    assert m.map_codons([('a', 1)])['total'] == 1            # single char accepted
    assert m.map_codons([('a' * 8, 1)])['total'] == 1        # 8 chars accepted
    for bad in (True, False, I(1), LyingI(1), S('1'), 1.0, None, 'x', [1],
                -1, 11, 100):
        _raises(ValueError, COD, m.map_codons, [('a', bad)])
        _raises(ValueError, COD, m.map_codons, [('b', 1), ('a', bad)])
    assert m.map_codons([('a', 0)])['codons'] == 0          # 0 accepted
    assert m.map_codons([('a', 10)])['codons'] == 10        # 10 accepted
    # order: container, cap, rows; first bad row reports first
    _raises(ValueError, CAP, m.map_codons, [('zz', 'bogus')] * 101)
    _raises(ValueError, NAM, m.map_codons, [('z' * 9, 'bogus'), ('a', 1)])
    _raises(ValueError, NAM, m.map_codons,
            [('a', 1), ('z' * 9, 1), ('b', 'bogus')])
    _raises(ValueError, COD, m.map_codons, [('a', 1), ('b', 'bogus')])
    _raises(ValueError, NAM, m.map_codons, [('a', 1), ('z' * 9, 'bogus')])
    _raises(ValueError, COD, m.map_codons, [('a', 1), ('b', 11)])
    # dynamic equal strings are accepted
    dyn = ''.join(['ru', 'le'])
    assert m.map_codons([(dyn, 2), (dyn, 6)]) == {
        'total': 2, 'rules': 1, 'codons': 8, 'choices': {dyn: 0}}
    _raises(ValueError, NAM, m.map_codons, [(LyingS('ab'), 1)])
    # 'zz' is a valid two-char rule name
    assert m.map_codons([('zz', 1)]) == {'total': 1, 'rules': 1,
        'codons': 1, 'choices': {'zz': 1}}


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    rows = [('a', 3), ('a', 4)]
    assert mod.map_codons(rows)['choices'] == {'a': 3}
    assert rows == [('a', 3), ('a', 4)]
    got1 = mod.map_codons(rows)
    got2 = mod.map_codons([('a', 4), ('a', 4)])
    assert got1['choices'] == {'a': 3} and got2['choices'] == {'a': 0}
    assert got1['choices'] is not mod.map_codons(rows)['choices']


MUTANTS = [
    ("    if type(rules) not in (list, tuple):",
     "    if not isinstance(rules, (list, tuple)):"),
    ("    if len(rules) > MAX_ROWS:", "    if len(rules) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if type(row) not in (list, tuple) and len(row) != 2:"),
    ("        if type(rule) is not str or not 1 <= len(rule) <= MAX_NAME:",
     "        if type(rule) is not str or not 1 < len(rule) <= MAX_NAME:"),
    ("not 1 <= len(rule) <= MAX_NAME", "not 1 <= len(rule) < MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("        if type(codon) is not int or not 0 <= codon <= MAX_CODON:",
     "        if not isinstance(codon, int) or not 0 <= codon <= MAX_CODON:"),
    ("        if type(codon) is not int or not 0 <= codon <= MAX_CODON:",
     "        if type(codon) is not int or not 0 < codon <= MAX_CODON:"),
    ("not 0 <= codon <= MAX_CODON", "not 0 <= codon < MAX_CODON"),
    ("MAX_CODON = 10", "MAX_CODON = 11"),
    ("    rows = []", "    rows = [('zz', 5)]"),
    ("    sums = {}", "    sums = {'zz': 3}"),
    ("    sums = {}", "    sums = {'zz': 1}"),
    ("        sums[rule] = sums.get(rule, 0) + codon",
     "        sums[rule] = sums.get(rule, 0) + 2 * codon"),
    ("        sums[rule] = sums.get(rule, 0) + codon",
     "        sums[rule] = sums.get(rule, 1) + codon"),
    ("        sums[rule] = sums.get(rule, 0) + codon",
     "        sums[rule] = sums.get(rule, 0)"),
    ("    choices = {rule: total % PRODUCTIONS for rule, total in sums.items()}",
     "    choices = {rule: total % 3 for rule, total in sums.items()}"),
    ("    choices = {rule: total % PRODUCTIONS for rule, total in sums.items()}",
     "    choices = {rule: total % 5 for rule, total in sums.items()}"),
    ("    choices = {rule: total % PRODUCTIONS for rule, total in sums.items()}",
     "    choices = {rule: total for rule, total in sums.items()}"),
    ("    choices = {rule: total % PRODUCTIONS for rule, total in sums.items()}",
     "    choices = {rule: total % PRODUCTIONS + 1 for rule, total in sums.items()}"),
    ("PRODUCTIONS = 4", "PRODUCTIONS = 5"),
    ("    return {'total': len(rows), 'rules': len(sums),",
     "    return {'total': len(rows) + 1, 'rules': len(sums),"),
    ("    return {'total': len(rows), 'rules': len(sums),",
     "    return {'total': len(rows), 'rules': len(sums) + 1,"),
    ("            'codons': sum(codon for rule, codon in rows),",
     "            'codons': sum(codon for rule, codon in rows) + 1,"),
    ("            'codons': sum(codon for rule, codon in rows),",
     "            'codons': len(rows),"),
    ("        raise TypeError('rules must be a list or tuple')",
     "        raise ValueError('rules must be a list or tuple')"),
    ("        raise ValueError('rules must contain at most 100 entries')",
     "        raise ValueError('rules must contain at most 101 entries')"),
    ("        raise ValueError('rule must be a string of 1 to 8 characters')",
     "        raise ValueError('rule must be a string of 1 to 9 characters')"),
    ("        raise ValueError('codon must be an integer from 0 to 10')",
     "        raise ValueError('codon must be an integer from 0 to 11')"),
    ("    for row in rules:\n        if type(row) not in (list, tuple) or len(row) != 2:",
     "    for row in reversed(rules):\n        if type(row) not in (list, tuple) or len(row) != 2:"),
    ("        rows.append((rule, codon))", "        rows.append((codon, rule))"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutants_killed(old, new):
    assert not _survives(battery, old, new), 'SURVIVED: %s' % old

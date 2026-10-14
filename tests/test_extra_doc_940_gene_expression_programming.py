import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import gene_expression_programming as mod

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
    assert mod.SCOPE == 'PARTIAL: operator folding over supplied rows, no real genes'
    assert len(mod.NOT_CLAIMED) >= 4 and 'expression synthesis' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_NAME, mod.EXPRESSED) == (100, 8, 6)


def _oracle(rows):
    values = {}
    for gene, operator in rows:
        level = values.get(gene, 1)
        values[gene] = level + 1 if operator == 'grow' else level * 2
    grow = sum(1 for g, o in rows if o == 'grow')
    return {'grow': grow, 'split': len(rows) - grow, 'total': len(rows),
            'expressed': sorted(g for g, v in values.items() if v >= 6)}


def _core(m):
    # grow adds 1, split doubles; 6 or more is expressed
    assert m.express([('a', 'grow'), ('a', 'grow'),
                      ('a', 'split')]) == {
        'grow': 2, 'split': 1, 'total': 3, 'expressed': ['a']}
    # operator order matters
    assert m.express([('a', 'split'), ('a', 'grow'),
                      ('a', 'grow')]) == {
        'grow': 2, 'split': 1, 'total': 3, 'expressed': []}
    # five grows from 1 reach exactly 6
    assert m.express([('a', 'grow')] * 5) == {
        'grow': 5, 'split': 0, 'total': 5, 'expressed': ['a']}
    # four grows stop at 5
    assert m.express([('a', 'grow')] * 4) == {
        'grow': 4, 'split': 0, 'total': 4, 'expressed': []}
    # splits alone grow fast
    assert m.express([('a', 'split')] * 3) == {
        'grow': 0, 'split': 3, 'total': 3, 'expressed': ['a']}
    # expressed comes back sorted
    got = m.express([('b', 'split'), ('b', 'split'), ('b', 'split'),
                     ('a', 'split'), ('a', 'split'), ('a', 'split'),
                     ('c', 'grow')])
    assert got['expressed'] == ['a', 'b']
    # an empty record has nothing
    assert m.express([]) == {'grow': 0, 'split': 0, 'total': 0,
                             'expressed': []}
    # tuples accepted
    assert m.express((('a', 'split'), ('a', 'split'),
                      ('a', 'split')))['expressed'] == ['a']
    rng = random.Random(940)
    names = ['g%d' % i for i in range(4)]
    operators = ['grow', 'split']
    for _ in range(400):
        rows = [(rng.choice(names), rng.choice(operators))
                for _ in range(rng.randint(0, 7))]
        assert m.express(rows) == _oracle(rows)


def _late(m):
    STM = 'genes must be a list or tuple'
    CAP = 'genes must contain at most 100 entries'
    ROW = 'each row must be a (gene, operator) row'
    NAM = 'gene must be a string of 1 to 8 characters'
    OPR = "operator must be 'grow' or 'split'"
    good = [('a', 'grow')]
    for bad in ('ab', None, 5.5, {}, {1}, L(good), T(tuple(good))):
        _raises(TypeError, STM, m.express, bad)
    _raises(TypeError, STM, m.express, L(good * 101))   # subclass refused before the cap
    _raises(ValueError, CAP, m.express, good * 101)
    assert m.express(good * 100)['total'] == 100
    for bad in ([0, 1], ['ab'], [('a',)], [('a', 'grow', 'x')],
                [L(['a', 'grow'])], [T(('a', 'grow'))]):
        _raises(ValueError, ROW, m.express, bad)
    for bad in (True, False, I(1), LyingI(2), S('a'), 1.0, None, ['a'], '',
                'a' * 9):
        _raises(ValueError, NAM, m.express, [(bad, 'grow')])
        _raises(ValueError, NAM, m.express, [('a', 'split'), (bad, 'grow')])
    assert m.express([('a', 'split')])['total'] == 1       # single char accepted
    assert m.express([('a' * 8, 'split')])['total'] == 1    # 8 chars accepted
    for bad in (True, I(1), S('grow'), 1.0, None, 'GROW', 'grows',
                'grown', 'splits', 'splitted', ''):
        _raises(ValueError, OPR, m.express, [('a', bad)])
        _raises(ValueError, OPR, m.express, [('b', 'split'), ('a', bad)])
    # order: container, cap, rows; first bad row reports first
    _raises(ValueError, CAP, m.express, [('zz', 'bogus')] * 101)
    _raises(ValueError, NAM, m.express, [('z' * 9, 'bogus'), ('a', 'grow')])
    _raises(ValueError, NAM, m.express,
            [('a', 'grow'), ('z' * 9, 'split'), ('b', 'bogus')])
    _raises(ValueError, OPR, m.express, [('a', 'grow'), ('b', 'bogus')])
    _raises(ValueError, NAM, m.express, [('a', 'grow'), ('z' * 9, 'bogus')])
    # dynamic equal strings are accepted
    dyn_g = ''.join(['gr', 'ow'])
    dyn_s = ''.join(['spl', 'it'])
    got = m.express([('a', dyn_s), ('a', dyn_s), ('a', dyn_g)])
    assert got == {'grow': 1, 'split': 2, 'total': 3, 'expressed': []}
    assert m.express([('a', dyn_s), ('a', dyn_g), ('a', dyn_g)]) == {
        'grow': 2, 'split': 1, 'total': 3, 'expressed': []}
    assert m.express([('a', dyn_g), ('a', dyn_g), ('a', dyn_s)]) == {
        'grow': 2, 'split': 1, 'total': 3, 'expressed': ['a']}
    _raises(ValueError, OPR, m.express, [('a', LyingS('grow'))])
    # 'zz' is a valid two-char gene name
    assert m.express([('zz', 'grow')]) == {'grow': 1, 'split': 0,
        'total': 1, 'expressed': []}
    assert m.express([('zz', 'split'), ('zz', 'split'),
                      ('zz', 'split')]) == {'grow': 0, 'split': 3,
        'total': 3, 'expressed': ['zz']}


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    rows = [('a', 'grow'), ('a', 'grow'), ('a', 'split')]
    assert mod.express(rows)['expressed'] == ['a']
    assert rows == [('a', 'grow'), ('a', 'grow'), ('a', 'split')]
    got1 = mod.express(rows)
    got2 = mod.express([('a', 'split'), ('a', 'grow'), ('a', 'grow')])
    assert got1['expressed'] == ['a'] and got2['expressed'] == []


MUTANTS = [
    ("    if type(genes) not in (list, tuple):",
     "    if not isinstance(genes, (list, tuple)):"),
    ("    if len(genes) > MAX_ROWS:", "    if len(genes) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if type(row) not in (list, tuple) and len(row) != 2:"),
    ("        if type(gene) is not str or not 1 <= len(gene) <= MAX_NAME:",
     "        if type(gene) is not str or not 1 < len(gene) <= MAX_NAME:"),
    ("not 1 <= len(gene) <= MAX_NAME", "not 1 <= len(gene) < MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("        if type(operator) is not str or operator not in OPERATORS:",
     "        if type(operator) is not str and operator not in OPERATORS:"),
    ("        if type(operator) is not str or operator not in OPERATORS:",
     "        if type(operator) is not str or operator not in ('grow',):"),
    ("    rows = []", "    rows = [('zz', 'grow')]"),
    ("    rows = []", "    rows = [('q', 'split')]"),
    ("    values = {}", "    values = {'zz': 100}"),
    ("    values = {}", "    values = {'zz': 0}"),
    ("        level = values.get(gene, 1)", "        level = values.get(gene, 0)"),
    ("        level = values.get(gene, 1)", "        level = values.get(gene, 2)"),
    ("        values[gene] = level + 1 if operator == 'grow' else level * 2",
     "        values[gene] = level + 2 if operator == 'grow' else level * 2"),
    ("        values[gene] = level + 1 if operator == 'grow' else level * 2",
     "        values[gene] = level + 1 if operator == 'grow' else level * 3"),
    ("        values[gene] = level + 1 if operator == 'grow' else level * 2",
     "        values[gene] = level * 2 if operator == 'grow' else level + 1"),
    ("        values[gene] = level + 1 if operator == 'grow' else level * 2",
     "        values[gene] = level + 1 if operator is 'grow' else level * 2"),
    ("    expressed = sorted(g for g, v in values.items() if v >= EXPRESSED)",
     "    expressed = sorted(g for g, v in values.items() if v > EXPRESSED)"),
    ("    expressed = sorted(g for g, v in values.items() if v >= EXPRESSED)",
     "    expressed = sorted(g for g, v in values.items() if v >= 5)"),
    ("    expressed = sorted(g for g, v in values.items() if v >= EXPRESSED)",
     "    expressed = list(g for g, v in values.items() if v >= EXPRESSED)"),
    ("    expressed = sorted(g for g, v in values.items() if v >= EXPRESSED)",
     "    expressed = sorted(values)"),
    ("EXPRESSED = 6", "EXPRESSED = 7"),
    ("    grow = sum(1 for gene, operator in rows if operator == 'grow')",
     "    grow = sum(1 for gene, operator in rows if operator == 'split')"),
    ("    grow = sum(1 for gene, operator in rows if operator == 'grow')",
     "    grow = sum(1 for gene, operator in rows if operator is 'grow')"),
    ("    grow = sum(1 for gene, operator in rows if operator == 'grow')",
     "    grow = sum(1 for gene, operator in rows)"),
    ("    return {'grow': grow, 'split': len(rows) - grow,",
     "    return {'grow': grow, 'split': len(rows) - grow + 1,"),
    ("    return {'grow': grow, 'split': len(rows) - grow,",
     "    return {'grow': len(rows) - grow, 'split': grow,"),
    ("            'total': len(rows), 'expressed': expressed}",
     "            'total': len(rows) + 1, 'expressed': expressed}"),
    ("        raise TypeError('genes must be a list or tuple')",
     "        raise ValueError('genes must be a list or tuple')"),
    ("        raise ValueError('genes must contain at most 100 entries')",
     "        raise ValueError('genes must contain at most 101 entries')"),
    ("        raise ValueError('gene must be a string of 1 to 8 characters')",
     "        raise ValueError('gene must be a string of 1 to 9 characters')"),
    ("        raise ValueError(\"operator must be 'grow' or 'split'\")",
     "        raise ValueError(\"operator must be 'grow' or 'splits'\")"),
    ("    for row in genes:\n        if type(row) not in (list, tuple) or len(row) != 2:",
     "    for row in reversed(genes):\n        if type(row) not in (list, tuple) or len(row) != 2:"),
    ("    for gene, operator in rows:\n        level = values.get(gene, 1)",
     "    for gene, operator in reversed(rows):\n        level = values.get(gene, 1)"),
    ("        rows.append((gene, operator))", "        rows.append((operator, gene))"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutants_killed(old, new):
    assert not _survives(battery, old, new), 'SURVIVED: %s' % old

import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import artificial_immune_systems as mod

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
    assert mod.SCOPE == 'PARTIAL: response selection over supplied rows, no real immunity'
    assert len(mod.NOT_CLAIMED) >= 4 and 'immunology' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_NAME) == (100, 8)


def _oracle(rows):
    attacks = {}
    for cell, response in rows:
        if response == 'attack':
            attacks[cell] = attacks.get(cell, 0) + 1
    attack = sum(1 for c, r in rows if r == 'attack')
    selected = (sorted(attacks, key=lambda c: (-attacks[c], c))[0]
                if attacks else None)
    return {'attack': attack, 'patrol': len(rows) - attack,
            'total': len(rows), 'selected': selected}


def _core(m):
    # the cell with the most attacks is selected
    got = m.select([('a', 'attack'), ('b', 'attack'), ('a', 'attack'),
                    ('b', 'patrol')])
    assert got == {'attack': 3, 'patrol': 1, 'total': 4, 'selected': 'a'}
    # ties break by name
    assert m.select([('b', 'attack'), ('a', 'attack')])['selected'] == 'a'
    # the tie-break is the name itself, not a transform of it
    assert m.select([('ba', 'attack'), ('ab', 'attack')])['selected'] == 'ab'
    assert m.select([('aA', 'attack'), ('Ba', 'attack')])['selected'] == 'Ba'
    # patrols do not count toward selection
    assert m.select([('a', 'attack'), ('b', 'patrol'),
                     ('b', 'patrol')])['selected'] == 'a'
    # no attack rows selects None
    assert m.select([('a', 'patrol')]) == {
        'attack': 0, 'patrol': 1, 'total': 1, 'selected': None}
    # an empty record selects None
    assert m.select([]) == {'attack': 0, 'patrol': 0, 'total': 0,
                            'selected': None}
    # tuples accepted
    assert m.select((('a', 'attack'), ('b', 'attack'),
                     ('b', 'attack')))['selected'] == 'b'
    rng = random.Random(936)
    names = ['c%d' % i for i in range(6)]
    responses = ['attack', 'patrol']
    for _ in range(400):
        rows = [(rng.choice(names), rng.choice(responses))
                for _ in range(rng.randint(0, 6))]
        assert m.select(rows) == _oracle(rows)


def _late(m):
    STM = 'cells must be a list or tuple'
    CAP = 'cells must contain at most 100 entries'
    ROW = 'each row must be a (cell, response) row'
    NAM = 'cell must be a string of 1 to 8 characters'
    RES = "response must be 'attack' or 'patrol'"
    good = [('a', 'attack')]
    for bad in ('ab', None, 5.5, {}, {1}, L(good), T(tuple(good))):
        _raises(TypeError, STM, m.select, bad)
    _raises(TypeError, STM, m.select, L(good * 101))   # subclass refused before the cap
    _raises(ValueError, CAP, m.select, good * 101)
    assert m.select(good * 100)['total'] == 100
    for bad in ([0, 1], ['ab'], [('a',)], [('a', 'attack', 'x')],
                [L(['a', 'attack'])], [T(('a', 'attack'))]):
        _raises(ValueError, ROW, m.select, bad)
    for bad in (True, False, I(1), LyingI(2), S('a'), 1.0, None, ['a'], '',
                'a' * 9):
        _raises(ValueError, NAM, m.select, [(bad, 'attack')])
        _raises(ValueError, NAM, m.select, [('a', 'patrol'), (bad, 'attack')])
    assert m.select([('a', 'patrol')])['total'] == 1       # single char accepted
    assert m.select([('a' * 8, 'patrol')])['total'] == 1    # 8 chars accepted
    for bad in (True, I(1), S('attack'), 1.0, None, 'ATTACK', 'attacks',
                'attacked', 'patrols', 'patrolled', ''):
        _raises(ValueError, RES, m.select, [('a', bad)])
        _raises(ValueError, RES, m.select, [('b', 'patrol'), ('a', bad)])
    # order: container, cap, rows; first bad row reports first
    _raises(ValueError, CAP, m.select, [('zz', 'bogus')] * 101)
    _raises(ValueError, NAM, m.select, [('z' * 9, 'bogus'), ('a', 'attack')])
    _raises(ValueError, NAM, m.select,
            [('a', 'attack'), ('z' * 9, 'patrol'), ('b', 'bogus')])
    _raises(ValueError, RES, m.select, [('a', 'attack'), ('b', 'bogus')])
    _raises(ValueError, NAM, m.select, [('a', 'attack'), ('z' * 9, 'bogus')])
    # dynamic equal strings are accepted
    dyn_a = ''.join(['att', 'ack'])
    dyn_p = ''.join(['pat', 'rol'])
    got = m.select([('a', dyn_a), ('b', dyn_p)])
    assert got == {'attack': 1, 'patrol': 1, 'total': 2, 'selected': 'a'}
    _raises(ValueError, RES, m.select, [('a', LyingS('attack'))])
    # 'zz' is a valid two-char cell name
    assert m.select([('zz', 'attack'), ('a', 'attack'),
                     ('a', 'attack')])['selected'] == 'a'
    assert m.select([('zz', 'attack'), ('zz', 'attack'),
                     ('a', 'attack')])['selected'] == 'zz'


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    rows = [('a', 'attack'), ('a', 'attack'), ('b', 'attack')]
    assert mod.select(rows)['selected'] == 'a'
    assert rows == [('a', 'attack'), ('a', 'attack'), ('b', 'attack')]
    assert mod.select([('b', 'attack'), ('b', 'attack'),
                       ('a', 'attack')])['selected'] == 'b'


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
    ("        if type(response) is not str or response not in RESPONSES:",
     "        if type(response) is not str and response not in RESPONSES:"),
    ("        if type(response) is not str or response not in RESPONSES:",
     "        if type(response) is not str or response not in ('attack',):"),
    ("    rows = []", "    rows = [('zz', 'attack')]"),
    ("    rows = []", "    rows = [('q', 'patrol')]"),
    ("    attacks = {}", "    attacks = {'zz': 5}"),
    ("    attacks = {}", "    attacks = {'zz': 1}"),
    ("        if response == 'attack':\n            attacks[cell] = attacks.get(cell, 0) + 1",
     "        if response == 'patrol':\n            attacks[cell] = attacks.get(cell, 0) + 1"),
    ("            attacks[cell] = attacks.get(cell, 0) + 1",
     "            attacks[cell] = attacks.get(cell, 0)"),
    ("        selected = sorted(attacks, key=lambda c: (-attacks[c], c))[0]",
     "        selected = sorted(attacks, key=lambda c: (attacks[c], c))[0]"),
    ("        selected = sorted(attacks, key=lambda c: (-attacks[c], c))[0]",
     "        selected = sorted(attacks, key=lambda c: -attacks[c])[0]"),
    ("        selected = sorted(attacks, key=lambda c: (-attacks[c], c))[0]",
     "        selected = sorted(attacks)[0]"),
    ("        selected = sorted(attacks, key=lambda c: (-attacks[c], c))[0]",
     "        selected = sorted(attacks, key=lambda c: (-attacks[c], c[::-1]))[0]"),
    ("        selected = sorted(attacks, key=lambda c: (-attacks[c], c))[0]",
     "        selected = sorted(attacks, key=lambda c: (-attacks[c], c.lower()))[0]"),
    ("        selected = sorted(attacks, key=lambda c: (-attacks[c], c))[0]",
     "        selected = sorted(attacks, key=lambda c: (-attacks[c], c))[-1]"),
    ("    if attacks:", "    if rows:"),
    ("        selected = None", "        selected = ''"),
    ("    attack = sum(1 for cell, response in rows if response == 'attack')",
     "    attack = sum(1 for cell, response in rows if response == 'patrol')"),
    ("    attack = sum(1 for cell, response in rows if response == 'attack')",
     "    attack = sum(1 for cell, response in rows if response is 'attack')"),
    ("    attack = sum(1 for cell, response in rows if response == 'attack')",
     "    attack = sum(1 for cell, response in rows)"),
    ("    return {'attack': attack, 'patrol': len(rows) - attack,",
     "    return {'attack': attack, 'patrol': len(rows) - attack + 1,"),
    ("    return {'attack': attack, 'patrol': len(rows) - attack,",
     "    return {'attack': len(rows) - attack, 'patrol': attack,"),
    ("            'total': len(rows), 'selected': selected}",
     "            'total': len(rows) + 1, 'selected': selected}"),
    ("            'total': len(rows), 'selected': selected}",
     "            'total': len(rows), 'selected': None}"),
    ("        raise TypeError('cells must be a list or tuple')",
     "        raise ValueError('cells must be a list or tuple')"),
    ("        raise ValueError('cells must contain at most 100 entries')",
     "        raise ValueError('cells must contain at most 101 entries')"),
    ("        raise ValueError('cell must be a string of 1 to 8 characters')",
     "        raise ValueError('cell must be a string of 1 to 9 characters')"),
    ("        raise ValueError(\"response must be 'attack' or 'patrol'\")",
     "        raise ValueError(\"response must be 'attack' or 'patrols'\")"),
    ("    for row in cells:\n        if type(row) not in (list, tuple) or len(row) != 2:",
     "    for row in reversed(cells):\n        if type(row) not in (list, tuple) or len(row) != 2:"),
    ("        rows.append((cell, response))", "        rows.append((response, cell))"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutants_killed(old, new):
    assert not _survives(battery, old, new), 'SURVIVED: %s' % old

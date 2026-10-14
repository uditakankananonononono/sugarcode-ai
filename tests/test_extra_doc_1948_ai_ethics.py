import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ai_ethics as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
DI = 'row 1: dilemma must be a string of 1 to 16 characters'
FR = 'row 1: framework must be a string of 1 to 16 characters'
WE = 'row 1: weight must be a nonbool integer between 1 and 9'


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
    code = compile(mutated, 'mutant', 'exec')
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


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def test_disclaimer_text_exact():
    section = ' '.join(mod.__doc__.split('NOT_CLAIMED:', 1)[1].split())
    assert section == ('dilemma curation, framework comparison, '
                       'moral reasoning, stakeholder input, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: revisit counting over supplied weights'
    assert mod.NOT_CLAIMED == ('dilemma curation', 'framework comparison',
                               'moral reasoning', 'stakeholder input',
                               'production readiness')


def _expected(rows):
    seen = set()
    revisits = {}
    revisited = set()
    for dilemma, framework, weight in rows:
        key = (dilemma, framework)
        if key in seen:
            revisits[framework] = revisits.get(framework, 0) + 1
            revisited.add(dilemma)
        seen.add(key)
    leader = None
    if revisits:
        top = max(revisits.values())
        order = list(dict.fromkeys(framework for _, framework, _ in rows))
        leader = next(f for f in order if revisits.get(f) == top)
    return {'total': len(rows), 'revisits': revisits,
            'revisited': sorted(revisited), 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1948
    assert m.count_revisits([('d', 'f', 1), ('d', 'g', 2),
                             ('d', 'f', 5)]) == {
        'total': 3, 'revisits': {'f': 1}, 'revisited': ['d'], 'leader': 'f'}
    # one row accepted with full expected output
    assert m.count_revisits([('d', 'f', 5)]) == {
        'total': 1, 'revisits': {}, 'revisited': [], 'leader': None}
    # the same dilemma from another framework is not a revisit
    assert m.count_revisits([('d', 'f', 1), ('d', 'g', 1)]) == {
        'total': 2, 'revisits': {}, 'revisited': [], 'leader': None}
    # the same framework on another dilemma is not a revisit
    assert m.count_revisits([('d', 'f', 1), ('e', 'f', 1)]) == {
        'total': 2, 'revisits': {}, 'revisited': [], 'leader': None}
    # a third weighing is a second revisit
    assert m.count_revisits([('d', 'f', 1), ('d', 'f', 2),
                             ('d', 'f', 3)]) == {
        'total': 3, 'revisits': {'f': 2}, 'revisited': ['d'], 'leader': 'f'}
    # revisited dilemmas come back sorted
    assert m.count_revisits([('z', 'f', 1), ('a', 'f', 1),
                             ('z', 'f', 2), ('a', 'f', 2)]) == {
        'total': 4, 'revisits': {'f': 2}, 'revisited': ['a', 'z'],
        'leader': 'f'}
    # a leader tie goes to the first supplied framework
    assert m.count_revisits([('d', 'b', 1), ('d', 'a', 1),
                             ('d', 'b', 2), ('d', 'a', 2)]) == {
        'total': 4, 'revisits': {'b': 1, 'a': 1},
        'revisited': ['d'], 'leader': 'b'}
    # non-ASCII frameworks follow the same rule
    assert m.count_revisits([('d', 'Üser-9!', 1), ('d', 'Üser-9!', 2),
                             ('d', 'q?7', 1)]) == {
        'total': 3, 'revisits': {'Üser-9!': 1}, 'revisited': ['d'],
        'leader': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.count_revisits([('m', 'f', 1), ('n', 'g', 1),
                             ('m', 'f', 2)]) == {
        'total': 3, 'revisits': {'f': 1}, 'revisited': ['m'], 'leader': 'f'}
    rng = random.Random(1948)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_revisits(rows) == _expected(rows)
    return True


def _late(m):
    P3 = 'row 2: expected a (dilemma, framework, weight) triple'
    _raises(TypeError, 'rows must be a list or tuple', m.count_revisits, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_revisits, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_revisits, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_revisits, [('a', 'b', 1)] * 61)
    _raises(TypeError, P3, m.count_revisits, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_revisits, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_revisits, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, DI, m.count_revisits, [(1, 'b', 1)])
    _raises(ValueError, DI, m.count_revisits, [('', 'b', 1)])
    _raises(ValueError, DI, m.count_revisits, [('x' * 17, 'b', 1)])
    _raises(ValueError, FR, m.count_revisits, [('a', 1, 1)])
    _raises(ValueError, FR, m.count_revisits, [('a', '', 1)])
    _raises(ValueError, FR, m.count_revisits, [('a', 'x' * 17, 1)])
    _raises(ValueError, WE, m.count_revisits, [('a', 'b', '1')])
    _raises(ValueError, WE, m.count_revisits, [('a', 'b', 0)])
    _raises(ValueError, WE, m.count_revisits, [('a', 'b', 10)])
    _raises(ValueError, WE, m.count_revisits, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: dilemma must be a string of 1 to 16 characters',
            m.count_revisits, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: weight must be a nonbool integer between 1 and 9',
            m.count_revisits, [('a', 'b', 1), ('c', 'd', 0)])
    # dilemma is validated before framework, framework before weight
    _raises(ValueError, DI, m.count_revisits, [('x' * 17, '', 0)])
    _raises(ValueError, FR, m.count_revisits, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_revisits, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_revisits((('a', 'b', 1),)) == m.count_revisits([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_revisits([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_revisits([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_revisits([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_revisits([('a', 'b', 9)])['revisits'] == {}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_revisits([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_revisits([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_revisits([('a', 'b', 5),
                             ('x' * 16, 'y' * 16, 5)])['total'] == 2
    return True


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


def _sym(m):
    P = 'rows must be a list or tuple'
    for K in (L, T):
        _raises(TypeError, P, m.count_revisits, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (dilemma, framework, weight) triple',
                m.count_revisits, [K(('a', 'b', 1))])
    _raises(ValueError, DI, m.count_revisits, [(S('a'), 'b', 1)])
    _raises(ValueError, FR, m.count_revisits, [('a', S('b'), 1)])
    _raises(ValueError, WE, m.count_revisits, [('a', 'b', I(1))])
    return True


def battery(m):
    _core(m)
    _late(m)
    _sym(m)
    return True


MUTANTS = [
    ('type(rows) not in (list, tuple)', 'not isinstance(rows, (list, tuple))'),
    ('not 1 <= len(rows) <= 60', 'not 1 <= len(rows) <= 61'),
    ('not 1 <= len(rows) <= 60', 'not 0 <= len(rows) <= 60'),
    ('type(row) not in (list, tuple)', 'not isinstance(row, (list, tuple))'),
    ('len(row) != 3', 'len(row) != 2'),
    ('type(dilemma) is not str', 'not isinstance(dilemma, str)'),
    ('type(framework) is not str', 'not isinstance(framework, str)'),
    ('type(weight) is not int', 'not isinstance(weight, int)'),
    ('not 1 <= len(dilemma) <= 16', 'not 1 <= len(dilemma) <= 17'),
    ('not 1 <= len(framework) <= 16', 'not 1 <= len(framework) <= 17'),
    ('not 1 <= weight <= 9', 'not 1 <= weight <= 10'),
    ('if key in seen:', 'if key not in seen:'),
    ('        key = (dilemma, framework)', '        key = dilemma'),
    ('revisits[framework] += 1', 'revisits[framework] += 2'),
    ('        seen[key] = True', '        pass'),
    ("'revisited': sorted(revisited)", "'revisited': revisited"),
    ("'revisits': revisits", "'revisits': {}"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(seen)"),
    ('for framework in order:', 'for framework in sorted(order):'),
    ('        dilemma, framework, weight = row',
     '        framework, dilemma, weight = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True

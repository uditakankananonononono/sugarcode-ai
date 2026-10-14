import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import text_to_3d_generation as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
AS = 'row 1: asset must be a string of 1 to 16 characters'
EN = 'row 1: engine must be a string of 1 to 16 characters'
ST = 'row 1: steps must be a nonbool integer between 1 and 9'


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
    assert section == ('mesh quality, texture synthesis, '
                       'geometry consistency, render cost, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: xor fusion over supplied step values'
    assert mod.NOT_CLAIMED == ('mesh quality', 'texture synthesis',
                               'geometry consistency', 'render cost',
                               'production readiness')


def _expected(rows):
    xors = {}
    for asset, engine, steps in rows:
        if engine not in xors:
            xors[engine] = 0
        xors[engine] ^= steps
    balanced = sorted(e for e in xors if xors[e] == 0)
    sharpest = None
    for engine in xors:
        if sharpest is None or xors[engine] > xors[sharpest]:
            sharpest = engine
    return {'total': len(rows), 'xors': xors,
            'balanced': balanced, 'sharpest': sharpest}


def _core(m):
    # fixed pins, oracle seeded with row number 1929
    assert m.fuse_steps([('a', 'e1', 3), ('a', 'e1', 5), ('a', 'e1', 6),
                         ('a', 'e2', 2), ('a', 'e2', 2)]) == {
        'total': 5, 'xors': {'e1': 0, 'e2': 0},
        'balanced': ['e1', 'e2'], 'sharpest': 'e1'}
    # one row: the xor is the value itself
    assert m.fuse_steps([('a', 'e', 7)]) == {
        'total': 1, 'xors': {'e': 7}, 'balanced': [], 'sharpest': 'e'}
    # unequal values never cancel
    assert m.fuse_steps([('a', 'x', 1), ('a', 'x', 2)]) == {
        'total': 2, 'xors': {'x': 3}, 'balanced': [], 'sharpest': 'x'}
    # equal pairs cancel
    assert m.fuse_steps([('a', 'x', 4), ('a', 'x', 4)])['balanced'] == ['x']
    # an odd triple does not cancel
    assert m.fuse_steps([('a', 'x', 5), ('a', 'x', 5), ('a', 'x', 5)])['xors'] == {'x': 5}
    # the sharpest tie goes to the first supplied engine
    r = m.fuse_steps([('a', 'Üser-9!', 9), ('a', 'q?7', 9)])
    assert r == {'total': 2, 'xors': {'Üser-9!': 9, 'q?7': 9},
                 'balanced': [], 'sharpest': 'Üser-9!'}
    # dicts keep first-touch order
    r = m.fuse_steps([('z', 'b', 7), ('a', 'a', 2)])
    assert r['xors'] == {'b': 7, 'a': 2} and r['sharpest'] == 'b'
    # a bigger xor beats an earlier smaller one
    r = m.fuse_steps([('a', 'p', 1), ('a', 'p', 2), ('a', 'q', 9)])
    assert r['xors'] == {'p': 3, 'q': 9} and r['sharpest'] == 'q'
    # pre-seed pin: fresh accumulators only
    assert m.fuse_steps([('a', 'a', 1), ('a', 'a', 1), ('a', 'b', 3)]) == {
        'total': 3, 'xors': {'a': 0, 'b': 3},
        'balanced': ['a'], 'sharpest': 'b'}
    rng = random.Random(1929)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.fuse_steps(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.fuse_steps, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.fuse_steps, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.fuse_steps, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.fuse_steps, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (asset, engine, steps) triple',
            m.fuse_steps, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.fuse_steps, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.fuse_steps, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, AS, m.fuse_steps, [(1, 'b', 1)])
    _raises(ValueError, AS, m.fuse_steps, [('', 'b', 1)])
    _raises(ValueError, AS, m.fuse_steps, [('x' * 17, 'b', 1)])
    _raises(ValueError, EN, m.fuse_steps, [('a', 1, 1)])
    _raises(ValueError, EN, m.fuse_steps, [('a', '', 1)])
    _raises(ValueError, EN, m.fuse_steps, [('a', 'x' * 17, 1)])
    _raises(ValueError, ST, m.fuse_steps, [('a', 'b', '1')])
    _raises(ValueError, ST, m.fuse_steps, [('a', 'b', 0)])
    _raises(ValueError, ST, m.fuse_steps, [('a', 'b', 10)])
    _raises(ValueError, ST, m.fuse_steps, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: asset must be a string of 1 to 16 characters',
            m.fuse_steps, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: steps must be a nonbool integer between 1 and 9',
            m.fuse_steps, [('a', 'b', 1), ('c', 'd', 0)])
    # asset is validated before engine, engine before steps
    _raises(ValueError, AS, m.fuse_steps, [('x' * 17, '', 0)])
    _raises(ValueError, EN, m.fuse_steps, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.fuse_steps, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.fuse_steps((('a', 'b', 1),)) == m.fuse_steps([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.fuse_steps([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.fuse_steps([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.fuse_steps([('a', 'b', 1)] * 60)['total'] == 60
    assert m.fuse_steps([('a', 'b', 9)])['xors'] == {'b': 9}
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
        _raises(TypeError, P, m.fuse_steps, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (asset, engine, steps) triple',
                m.fuse_steps, [K(('a', 'b', 1))])
    _raises(ValueError, AS, m.fuse_steps, [(S('a'), 'b', 1)])
    _raises(ValueError, EN, m.fuse_steps, [('a', S('b'), 1)])
    _raises(ValueError, ST, m.fuse_steps, [('a', 'b', I(1))])
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
    ('type(asset) is not str', 'not isinstance(asset, str)'),
    ('type(engine) is not str', 'not isinstance(engine, str)'),
    ('type(steps) is not int', 'not isinstance(steps, int)'),
    ('not 1 <= len(asset) <= 16', 'not 1 <= len(asset) <= 17'),
    ('not 1 <= len(engine) <= 16', 'not 1 <= len(engine) <= 17'),
    ('not 1 <= steps <= 9', 'not 1 <= steps <= 10'),
    ('            xors[engine] = 0', '            xors[engine] = 1'),
    ('        xors[engine] ^= steps', '        xors[engine] += steps'),
    ('        xors[engine] ^= steps', '        xors[engine] ^= 0'),
    ('xors[e] == 0', 'xors[e] != 0'),
    ('if sharpest is None or xors[engine] > xors[sharpest]:',
     'if sharpest is None or xors[engine] < xors[sharpest]:'),
    ("'xors': xors", "'xors': {}"),
    ("'balanced': balanced", "'balanced': []"),
    ("'sharpest': sharpest", "'sharpest': None"),
    ("'total': len(rows)", "'total': len(xors)"),
    ('        asset, engine, steps = row',
     '        engine, asset, steps = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True


def test_gap_pin_exact_cap_acceptance():
    # gap sweep: exact-cap 16-char labels accepted in each label
    # position, and on a late row
    assert mod.fuse_steps([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.fuse_steps([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.fuse_steps([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

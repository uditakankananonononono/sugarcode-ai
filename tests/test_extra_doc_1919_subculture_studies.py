import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import subculture_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SN = 'row 1: scene must be a string of 1 to 16 characters'
ZN = 'row 1: zine must be a string of 1 to 16 characters'
BZ = 'row 1: buzz must be a nonbool integer between 1 and 9'


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
    assert section == ('gatekeeping, fashion history, music criticism, '
                       'online moderation, production readiness.')
    assert mod.SCOPE == 'PARTIAL: scene reading over supplied buzzes'
    assert mod.NOT_CLAIMED == ('gatekeeping', 'fashion history',
                               'music criticism', 'online moderation',
                               'production readiness')


def _expected(rows):
    values = {}
    for scene, zine, buzz in rows:
        if scene not in values:
            values[scene] = {}
        values[scene][buzz] = True
    overlap = sorted(b for b in range(1, 10)
                     if sum(1 for s in values if b in values[s]) >= 2)
    signature = {}
    for scene in values:
        signature[scene] = sorted(b for b in values[scene]
                                  if sum(1 for s in values if b in values[s]) == 1)
    most_signed = None
    for scene in signature:
        if most_signed is None or len(signature[scene]) > len(signature[most_signed]):
            most_signed = scene
    return {'total': len(rows), 'overlap': overlap,
            'signature': signature, 'most_signed': most_signed}


def _core(m):
    # fixed pins, oracle seeded with row number 1919
    assert m.read_scenes([('s1', 'z', 3), ('s2', 'z', 3),
                          ('s1', 'y', 7), ('s3', 'x', 7)]) == {
        'total': 4, 'overlap': [3, 7],
        'signature': {'s1': [], 's2': [], 's3': []}, 'most_signed': 's1'}
    # a lone scene signs everything it uses
    assert m.read_scenes([('s', 'z', 5)]) == {
        'total': 1, 'overlap': [], 'signature': {'s': [5]}, 'most_signed': 's'}
    # a shared value is nobody's signature
    r = m.read_scenes([('a', 'x', 1), ('b', 'y', 2), ('c', 'z', 2)])
    assert r == {'total': 3, 'overlap': [2],
                 'signature': {'a': [1], 'b': [], 'c': []}, 'most_signed': 'a'}
    # repeats of a value within one scene still count once
    r = m.read_scenes([('a', 'x', 9), ('b', 'y', 1), ('a', 'z', 1)])
    assert r == {'total': 3, 'overlap': [1],
                 'signature': {'a': [9], 'b': []}, 'most_signed': 'a'}
    # dicts keep first-touch order
    r = m.read_scenes([('z', 'b', 2), ('a', 'a', 4)])
    assert r['signature'] == {'z': [2], 'a': [4]}
    # non-ASCII scenes follow the same rule
    r = m.read_scenes([('Üser-9!', 'a', 2), ('q?7', 'b', 2), ('Üser-9!', 'c', 8)])
    assert r == {'total': 3, 'overlap': [2],
                 'signature': {'Üser-9!': [8], 'q?7': []},
                 'most_signed': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.read_scenes([('p', 'a', 5), ('q', 'b', 5),
                          ('p', 'c', 6), ('q', 'd', 7)]) == {
        'total': 4, 'overlap': [5],
        'signature': {'p': [6], 'q': [7]}, 'most_signed': 'p'}
    rng = random.Random(1919)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.read_scenes(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.read_scenes, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.read_scenes, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.read_scenes, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.read_scenes, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (scene, zine, buzz) triple',
            m.read_scenes, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.read_scenes, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.read_scenes, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SN, m.read_scenes, [(1, 'b', 1)])
    _raises(ValueError, SN, m.read_scenes, [('', 'b', 1)])
    _raises(ValueError, SN, m.read_scenes, [('x' * 17, 'b', 1)])
    _raises(ValueError, ZN, m.read_scenes, [('a', 1, 1)])
    _raises(ValueError, ZN, m.read_scenes, [('a', '', 1)])
    _raises(ValueError, ZN, m.read_scenes, [('a', 'x' * 17, 1)])
    _raises(ValueError, BZ, m.read_scenes, [('a', 'b', '1')])
    _raises(ValueError, BZ, m.read_scenes, [('a', 'b', 0)])
    _raises(ValueError, BZ, m.read_scenes, [('a', 'b', 10)])
    _raises(ValueError, BZ, m.read_scenes, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: scene must be a string of 1 to 16 characters',
            m.read_scenes, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: buzz must be a nonbool integer between 1 and 9',
            m.read_scenes, [('a', 'b', 1), ('c', 'd', 0)])
    # scene is validated before zine, zine before buzz
    _raises(ValueError, SN, m.read_scenes, [('x' * 17, '', 0)])
    _raises(ValueError, ZN, m.read_scenes, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.read_scenes, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.read_scenes((('a', 'b', 1),)) == m.read_scenes([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.read_scenes([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.read_scenes([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.read_scenes([('a', 'b', 1)] * 60)['total'] == 60
    assert m.read_scenes([('a', 'b', 9)])['signature'] == {'a': [9]}
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
        _raises(TypeError, P, m.read_scenes, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (scene, zine, buzz) triple',
                m.read_scenes, [K(('a', 'b', 1))])
    _raises(ValueError, SN, m.read_scenes, [(S('a'), 'b', 1)])
    _raises(ValueError, ZN, m.read_scenes, [('a', S('b'), 1)])
    _raises(ValueError, BZ, m.read_scenes, [('a', 'b', I(1))])
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
    ('type(scene) is not str', 'not isinstance(scene, str)'),
    ('type(zine) is not str', 'not isinstance(zine, str)'),
    ('type(buzz) is not int', 'not isinstance(buzz, int)'),
    ('not 1 <= len(scene) <= 16', 'not 1 <= len(scene) <= 17'),
    ('not 1 <= len(zine) <= 16', 'not 1 <= len(zine) <= 17'),
    ('not 1 <= buzz <= 9', 'not 1 <= buzz <= 10'),
    ('        values[scene][buzz] = True', '        values[scene] = {}'),
    ('if sum(1 for s in values if b in values[s]) >= 2',
     'if sum(1 for s in values if b in values[s]) >= 3'),
    ('if sum(1 for s in values if b in values[s]) == 1',
     'if sum(1 for s in values if b in values[s]) == 2'),
    ('overlap = sorted(b for b in range(1, 10)',
     'overlap = sorted(b for b in range(1, 9)'),
    ('if most_signed is None or len(signature[scene]) > len(signature[most_signed]):',
     'if most_signed is None or len(signature[scene]) < len(signature[most_signed]):'),
    ("'overlap': overlap", "'overlap': []"),
    ("'signature': signature", "'signature': {}"),
    ("'most_signed': most_signed", "'most_signed': None"),
    ("'total': len(rows)", "'total': len(values)"),
    ('        scene, zine, buzz = row', '        zine, scene, buzz = row'),
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
    assert mod.read_scenes([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.read_scenes([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.read_scenes([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

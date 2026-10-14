import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import drama as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PM = 'row 1: play must be a string of 1 to 16 characters'
SM = 'row 1: scene must be a string of 1 to 16 characters'
LM = 'row 1: lines must be a nonbool integer between 1 and 99'


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
    assert section == ('real dramaturgy, staging quality, performance '
                       'success, playwright intent, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: scene pacing over supplied line counts'
    assert mod.NOT_CLAIMED == ('real dramaturgy', 'staging quality',
                               'performance success',
                               'playwright intent',
                               'production readiness')


def _expected(rows):
    scenes = {}
    rises = {}
    falls = {}
    previous = {}
    for play, scene, lines in rows:
        if play not in scenes:
            scenes[play] = 0
            rises[play] = 0
            falls[play] = 0
        scenes[play] += 1
        if play in previous:
            if lines > previous[play]:
                rises[play] += 1
            elif lines < previous[play]:
                falls[play] += 1
        previous[play] = lines
    building = sorted(p for p in scenes if rises[p] > falls[p])
    falling = sorted(p for p in scenes if falls[p] > rises[p])
    steadiest = None
    for play in scenes:
        if scenes[play] < 2:
            continue
        if (steadiest is None
                or rises[play] + falls[play]
                < rises[steadiest] + falls[steadiest]):
            steadiest = play
    return {'total': len(rows), 'scenes': scenes, 'rises': rises,
            'falls': falls, 'building': building, 'falling': falling,
            'steadiest': steadiest}


def _core(m):
    # fixed pins, oracle seeded with row number 1869
    assert m.pace_scenes([('pl1', 's1', 10), ('pl1', 's2', 20),
                          ('pl1', 's3', 15), ('pl2', 's1', 30),
                          ('pl2', 's2', 10), ('pl3', 's1', 5)]) == {
        'total': 6, 'scenes': {'pl1': 3, 'pl2': 2, 'pl3': 1},
        'rises': {'pl1': 1, 'pl2': 0, 'pl3': 0},
        'falls': {'pl1': 1, 'pl2': 1, 'pl3': 0},
        'building': [], 'falling': ['pl2'], 'steadiest': 'pl2'}
    # one scene: no rises, no falls, never steadiest
    assert m.pace_scenes([('p', 'a', 50)]) == {
        'total': 1, 'scenes': {'p': 1}, 'rises': {'p': 0},
        'falls': {'p': 0}, 'building': [], 'falling': [],
        'steadiest': None}
    # equal scenes: no rise, no fall
    r = m.pace_scenes([('p', 'a', 5), ('p', 'b', 5)])
    assert r['rises'] == {'p': 0} and r['falls'] == {'p': 0}
    assert r['steadiest'] == 'p'
    # more rises than falls is building
    r = m.pace_scenes([('p', 'a', 1), ('p', 'b', 2), ('p', 'c', 3),
                       ('p', 'd', 2)])
    assert r['building'] == ['p'] and r['falling'] == []
    # equal rises and falls is neither
    r = m.pace_scenes([('p', 'a', 1), ('p', 'b', 2), ('p', 'c', 1)])
    assert r['building'] == [] and r['falling'] == []
    # interleaved plays keep separate runs
    r = m.pace_scenes([('a', 'x', 1), ('b', 'y', 9), ('a', 'z', 2)])
    assert r['rises'] == {'a': 1, 'b': 0}
    # a one-scene play is never steadiest
    r = m.pace_scenes([('a', 'x', 9), ('b', 'y', 1), ('b', 'z', 1)])
    assert r['steadiest'] == 'b'
    # a perfectly flat play beats any moving one
    r = m.pace_scenes([('a', 'x', 1), ('a', 'y', 9),
                       ('b', 'w', 5), ('b', 'z', 5)])
    assert r['steadiest'] == 'b'
    # the steadiest tie goes to the first supplied
    r = m.pace_scenes([('a', 'x', 1), ('a', 'y', 2),
                       ('b', 'w', 1), ('b', 'z', 3)])
    assert r['steadiest'] == 'a'
    # building and falling are sorted
    r = m.pace_scenes([('z', 'a', 1), ('z', 'b', 9),
                       ('a', 'c', 1), ('a', 'd', 9),
                       ('y', 'e', 9), ('y', 'f', 1),
                       ('b', 'g', 9), ('b', 'h', 1)])
    assert r['building'] == ['a', 'z'] and r['falling'] == ['b', 'y']
    # dicts keep first-touch order
    r = m.pace_scenes([('b', 'x', 1), ('a', 'y', 2)])
    assert r['scenes'] == {'b': 1, 'a': 1}
    # non-ASCII plays follow the same rule
    r = m.pace_scenes([('Üser-9!', 'Ω-1', 10), ('Üser-9!', 'q?7', 90)])
    assert r == {'total': 2, 'scenes': {'Üser-9!': 2},
                 'rises': {'Üser-9!': 1}, 'falls': {'Üser-9!': 0},
                 'building': ['Üser-9!'], 'falling': [],
                 'steadiest': 'Üser-9!'}
    rng = random.Random(1869)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 99))
                for _ in range(rng.randint(1, 60))]
        assert m.pace_scenes(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.pace_scenes, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.pace_scenes, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.pace_scenes, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.pace_scenes, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (play, scene, lines) triple',
            m.pace_scenes, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.pace_scenes, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.pace_scenes, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PM, m.pace_scenes, [(1, 'b', 1)])
    _raises(ValueError, PM, m.pace_scenes, [('', 'b', 1)])
    _raises(ValueError, PM, m.pace_scenes, [('x' * 17, 'b', 1)])
    _raises(ValueError, SM, m.pace_scenes, [('a', 1, 1)])
    _raises(ValueError, SM, m.pace_scenes, [('a', '', 1)])
    _raises(ValueError, SM, m.pace_scenes, [('a', 'x' * 17, 1)])
    _raises(ValueError, LM, m.pace_scenes, [('a', 'b', '1')])
    _raises(ValueError, LM, m.pace_scenes, [('a', 'b', 0)])
    _raises(ValueError, LM, m.pace_scenes, [('a', 'b', 100)])
    _raises(ValueError, LM, m.pace_scenes, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: play must be a string of 1 to 16 characters',
            m.pace_scenes, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: lines must be a nonbool integer between 1 and 99',
            m.pace_scenes, [('a', 'b', 1), ('c', 'd', 0)])
    # play is validated before scene, scene before lines
    _raises(ValueError, PM, m.pace_scenes, [('x' * 17, '', 0)])
    _raises(ValueError, SM, m.pace_scenes, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.pace_scenes, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.pace_scenes((('a', 'b', 1),)) == m.pace_scenes([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.pace_scenes([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.pace_scenes([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.pace_scenes([('a', 'b', 1)] * 60)['total'] == 60
    assert m.pace_scenes([('a', 'b', 99), ('a', 'c', 1)])['falls'] == {'a': 1}
    # pre-seed pin: fresh accumulators only
    assert m.pace_scenes([('a', 'x', 5), ('b', 'y', 9), ('a', 'z', 1)]) == {
        'total': 3, 'scenes': {'a': 2, 'b': 1},
        'rises': {'a': 0, 'b': 0}, 'falls': {'a': 1, 'b': 0},
        'building': [], 'falling': ['a'], 'steadiest': 'a'}
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
        _raises(TypeError, P, m.pace_scenes, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (play, scene, lines) triple',
                m.pace_scenes, [K(('a', 'b', 1))])
    _raises(ValueError, PM, m.pace_scenes, [(S('a'), 'b', 1)])
    _raises(ValueError, SM, m.pace_scenes, [('a', S('b'), 1)])
    _raises(ValueError, LM, m.pace_scenes, [('a', 'b', I(1))])
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
    ('type(play) is not str', 'not isinstance(play, str)'),
    ('type(scene) is not str', 'not isinstance(scene, str)'),
    ('type(lines) is not int', 'not isinstance(lines, int)'),
    ('not 1 <= len(play) <= 16', 'not 1 <= len(play) <= 17'),
    ('not 1 <= len(scene) <= 16', 'not 1 <= len(scene) <= 17'),
    ('not 1 <= lines <= 99', 'not 1 <= lines <= 100'),
    ('        scenes[play] += 1', '        scenes[play] += 0'),
    ('            if lines > previous[play]:',
     '            if lines < previous[play]:'),
    ('            elif lines < previous[play]:',
     '            elif lines > previous[play]:'),
    ('        previous[play] = lines', '        previous[play] = 0'),
    ('building = sorted(p for p in scenes if rises[p] > falls[p])',
     'building = sorted(p for p in scenes if rises[p] >= falls[p])'),
    ('        if scenes[play] < 2:', '        if scenes[play] < 1:'),
    ("'building': building", "'building': falling"),
    ("'total': len(rows)", "'total': len(scenes)"),
    ('        play, scene, lines = row',
     '        scene, play, lines = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True

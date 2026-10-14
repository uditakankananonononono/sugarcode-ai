import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import film_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SC = 'row 1: scene must be a string of 1 to 16 characters'
RE = 'row 1: reel must be a string of 1 to 16 characters'
SO = 'row 1: score must be a nonbool integer between 1 and 9'


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
    assert section == ('cinematography, editing, sound design, '
                       'festival strategy, production readiness.')
    assert mod.SCOPE == 'PARTIAL: take screening over supplied scores'
    assert mod.NOT_CLAIMED == ('cinematography', 'editing', 'sound design',
                               'festival strategy', 'production readiness')


def _expected(rows):
    firsts = {}
    bests = {}
    counts = {}
    for scene, reel, score in rows:
        if scene not in bests:
            firsts[scene] = score
            bests[scene] = score
            counts[scene] = 0
        if score > bests[scene]:
            bests[scene] = score
        counts[scene] += 1
    natural = sorted(s for s in bests if firsts[s] == bests[s])
    climber = None
    for scene in bests:
        if counts[scene] < 2:
            continue
        if climber is None or bests[scene] - firsts[scene] > bests[climber] - firsts[climber]:
            climber = scene
    return {'total': len(rows), 'bests': bests,
            'natural': natural, 'climber': climber}


def _core(m):
    # fixed pins, oracle seeded with row number 1912
    assert m.screen_takes([('s1', 'a', 3), ('s2', 'a', 7), ('s1', 'b', 3),
                           ('s2', 'b', 9), ('s3', 'a', 9)]) == {
        'total': 5, 'bests': {'s1': 3, 's2': 9, 's3': 9},
        'natural': ['s1', 's3'], 'climber': 's2'}
    # a lone take is always natural, and there is no climber
    assert m.screen_takes([('s', 'r', 5)]) == {
        'total': 1, 'bests': {'s': 5}, 'natural': ['s'], 'climber': None}
    # no scene with 2 takes means no climber at all
    assert m.screen_takes([('a', 'r', 1), ('b', 'r', 2)]) == {
        'total': 2, 'bests': {'a': 1, 'b': 2},
        'natural': ['a', 'b'], 'climber': None}
    # the climber tie goes to the first supplied scene
    r = m.screen_takes([('a', 'r', 1), ('a', 'r', 5),
                        ('b', 'r', 2), ('b', 'r', 6)])
    assert r['climber'] == 'a'
    # a scene can climb even to a tie at the top score
    r = m.screen_takes([('a', 'r', 1), ('a', 'r', 9), ('b', 'r', 9)])
    assert r['bests'] == {'a': 9, 'b': 9} and r['climber'] == 'a'
    assert r['natural'] == ['b']
    # dicts keep first-touch order
    r = m.screen_takes([('z', 'r', 1), ('a', 'r', 2)])
    assert r['bests'] == {'z': 1, 'a': 2}
    # non-ASCII scenes follow the same rule
    r = m.screen_takes([('Üser-9!', 'a', 4), ('q?7', 'b', 4), ('Üser-9!', 'c', 4)])
    assert r == {'total': 3, 'bests': {'Üser-9!': 4, 'q?7': 4},
                 'natural': ['q?7', 'Üser-9!'], 'climber': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.screen_takes([('p', 'a', 2), ('p', 'b', 8),
                           ('p', 'c', 5), ('q', 'a', 9)]) == {
        'total': 4, 'bests': {'p': 8, 'q': 9},
        'natural': ['q'], 'climber': 'p'}
    rng = random.Random(1912)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.screen_takes(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.screen_takes, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.screen_takes, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.screen_takes, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.screen_takes, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (scene, reel, score) triple',
            m.screen_takes, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.screen_takes, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.screen_takes, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SC, m.screen_takes, [(1, 'b', 1)])
    _raises(ValueError, SC, m.screen_takes, [('', 'b', 1)])
    _raises(ValueError, SC, m.screen_takes, [('x' * 17, 'b', 1)])
    _raises(ValueError, RE, m.screen_takes, [('a', 1, 1)])
    _raises(ValueError, RE, m.screen_takes, [('a', '', 1)])
    _raises(ValueError, RE, m.screen_takes, [('a', 'x' * 17, 1)])
    _raises(ValueError, SO, m.screen_takes, [('a', 'b', '1')])
    _raises(ValueError, SO, m.screen_takes, [('a', 'b', 0)])
    _raises(ValueError, SO, m.screen_takes, [('a', 'b', 10)])
    _raises(ValueError, SO, m.screen_takes, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: scene must be a string of 1 to 16 characters',
            m.screen_takes, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.screen_takes, [('a', 'b', 1), ('c', 'd', 0)])
    # scene is validated before reel, reel before score
    _raises(ValueError, SC, m.screen_takes, [('x' * 17, '', 0)])
    _raises(ValueError, RE, m.screen_takes, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.screen_takes, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.screen_takes((('a', 'b', 1),)) == m.screen_takes([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.screen_takes([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.screen_takes([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.screen_takes([('a', 'b', 1)] * 60)['total'] == 60
    assert m.screen_takes([('a', 'b', 9)])['bests'] == {'a': 9}
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
        _raises(TypeError, P, m.screen_takes, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (scene, reel, score) triple',
                m.screen_takes, [K(('a', 'b', 1))])
    _raises(ValueError, SC, m.screen_takes, [(S('a'), 'b', 1)])
    _raises(ValueError, RE, m.screen_takes, [('a', S('b'), 1)])
    _raises(ValueError, SO, m.screen_takes, [('a', 'b', I(1))])
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
    ('type(reel) is not str', 'not isinstance(reel, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(scene) <= 16', 'not 1 <= len(scene) <= 17'),
    ('not 1 <= len(reel) <= 16', 'not 1 <= len(reel) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('        if score > bests[scene]:', '        if score < bests[scene]:'),
    ('        counts[scene] += 1', '        counts[scene] += 2'),
    ('if firsts[s] == bests[s]', 'if firsts[s] != bests[s]'),
    ('        if counts[scene] < 2:', '        if counts[scene] < 3:'),
    ('if climber is None or bests[scene] - firsts[scene] > bests[climber] - firsts[climber]:',
     'if climber is None or bests[scene] - firsts[scene] < bests[climber] - firsts[climber]:'),
    ("'bests': bests", "'bests': firsts"),
    ("'natural': natural", "'natural': []"),
    ("'climber': climber", "'climber': None"),
    ("'total': len(rows)", "'total': len(bests)"),
    ('        scene, reel, score = row', '        reel, scene, score = row'),
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
    assert mod.screen_takes([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.screen_takes([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.screen_takes([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

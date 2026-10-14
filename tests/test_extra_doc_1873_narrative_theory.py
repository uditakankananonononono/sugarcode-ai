import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import narrative_theory as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SM = 'row 1: scene must be a string of 1 to 16 characters'
VM = 'row 1: voice must be a string of 1 to 16 characters'
IM = 'row 1: intensity must be a nonbool integer between 1 and 9'


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
    assert section == ('real narration, focalization theory, authorial '
                       'intent, reader interpretation, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: voice tracking over supplied scenes'
    assert mod.NOT_CLAIMED == ('real narration', 'focalization theory',
                               'authorial intent',
                               'reader interpretation',
                               'production readiness')


def _expected(rows):
    scenes = {}
    switches = 0
    longest = 0
    streak = 0
    previous = None
    for scene, voice, intensity in rows:
        if voice not in scenes:
            scenes[voice] = 0
        scenes[voice] += 1
        if previous is None or voice == previous:
            streak += 1
        else:
            switches += 1
            streak = 1
        if streak > longest:
            longest = streak
        previous = voice
    dominant = None
    if scenes:
        top = max(scenes.values())
        supply = list(dict.fromkeys(v for _s, v, _i in rows))
        dominant = next(v for v in supply if scenes.get(v) == top)
    return {'total': len(rows), 'scenes': scenes, 'switches': switches,
            'longest': longest, 'dominant': dominant}


def _core(m):
    # fixed pins, oracle seeded with row number 1873
    assert m.track_voices([('s1', 'v1', 1), ('s2', 'v1', 2),
                           ('s3', 'v2', 3), ('s4', 'v1', 4)]) == {
        'total': 4, 'scenes': {'v1': 3, 'v2': 1},
        'switches': 2, 'longest': 2, 'dominant': 'v1'}
    # one scene: no switches, a run of one
    assert m.track_voices([('s', 'v', 5)]) == {
        'total': 1, 'scenes': {'v': 1}, 'switches': 0,
        'longest': 1, 'dominant': 'v'}
    # alternating voices switch at every boundary
    r = m.track_voices([('a', 'x', 1), ('b', 'y', 1),
                        ('c', 'x', 1), ('d', 'y', 1)])
    assert r['switches'] == 3 and r['longest'] == 1
    # one voice throughout: no switches, full-length run
    r = m.track_voices([('a', 'x', 1), ('b', 'x', 2), ('c', 'x', 3)])
    assert r['switches'] == 0 and r['longest'] == 3
    # a return to an earlier voice still switches
    r = m.track_voices([('a', 'x', 1), ('b', 'y', 1), ('c', 'x', 1)])
    assert r['switches'] == 2
    # a late long run sets the longest
    r = m.track_voices([('a', 'x', 1), ('b', 'y', 1),
                        ('c', 'y', 1), ('d', 'y', 1)])
    assert r['longest'] == 3 and r['switches'] == 1
    # a dominant tie ignores alphabetical order
    r = m.track_voices([('s1', 'z', 1), ('s2', 'a', 1)])
    assert r['dominant'] == 'z'
    # the dominant tie goes to the first supplied
    r = m.track_voices([('a', 'x', 1), ('b', 'y', 1)])
    assert r['dominant'] == 'x'
    # a strictly busier voice replaces the dominant
    r = m.track_voices([('a', 'x', 1), ('b', 'y', 1), ('c', 'y', 1)])
    assert r['dominant'] == 'y'
    # intensity never changes the tracking
    r = m.track_voices([('a', 'x', 9), ('b', 'x', 1)])
    assert r == {'total': 2, 'scenes': {'x': 2}, 'switches': 0,
                 'longest': 2, 'dominant': 'x'}
    # dicts keep first-touch order
    r = m.track_voices([('s1', 'b', 1), ('s2', 'a', 2)])
    assert r['scenes'] == {'b': 1, 'a': 1}
    # non-ASCII voices follow the same rule
    r = m.track_voices([('s1', 'Üser-9!', 1), ('s2', 'Ω-1', 2),
                        ('s3', 'Ω-1', 3)])
    assert r == {'total': 3, 'scenes': {'Üser-9!': 1, 'Ω-1': 2},
                 'switches': 1, 'longest': 2, 'dominant': 'Ω-1'}
    rng = random.Random(1873)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.track_voices(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.track_voices, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.track_voices, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_voices, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_voices, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (scene, voice, intensity) triple',
            m.track_voices, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.track_voices, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.track_voices, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SM, m.track_voices, [(1, 'b', 1)])
    _raises(ValueError, SM, m.track_voices, [('', 'b', 1)])
    _raises(ValueError, SM, m.track_voices, [('x' * 17, 'b', 1)])
    _raises(ValueError, VM, m.track_voices, [('a', 1, 1)])
    _raises(ValueError, VM, m.track_voices, [('a', '', 1)])
    _raises(ValueError, VM, m.track_voices, [('a', 'x' * 17, 1)])
    _raises(ValueError, IM, m.track_voices, [('a', 'b', '1')])
    _raises(ValueError, IM, m.track_voices, [('a', 'b', 0)])
    _raises(ValueError, IM, m.track_voices, [('a', 'b', 10)])
    _raises(ValueError, IM, m.track_voices, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: scene must be a string of 1 to 16 characters',
            m.track_voices, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: intensity must be a nonbool integer between 1 and 9',
            m.track_voices, [('a', 'b', 1), ('c', 'd', 0)])
    # scene is validated before voice, voice before intensity
    _raises(ValueError, SM, m.track_voices, [('x' * 17, '', 0)])
    _raises(ValueError, VM, m.track_voices, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.track_voices, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.track_voices((('a', 'b', 1),)) == m.track_voices([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.track_voices([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.track_voices([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.track_voices([('a', 'b', 1)] * 60)['total'] == 60
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.track_voices([('x' * 16, 'b', 5)])['total'] == 1
    assert m.track_voices([('a', 'y' * 16, 5)])['total'] == 1
    assert m.track_voices([('a', 'b', 5),
                           ('x' * 16, 'y' * 16, 5)])['total'] == 2
    assert m.track_voices([('a', 'b', 9), ('c', 'b', 9)])['switches'] == 0
    # pre-seed pin: fresh accumulators only
    assert m.track_voices([('a', 'x', 1), ('b', 'x', 2), ('c', 'y', 3)]) == {
        'total': 3, 'scenes': {'x': 2, 'y': 1}, 'switches': 1,
        'longest': 2, 'dominant': 'x'}
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
        _raises(TypeError, P, m.track_voices, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (scene, voice, intensity) triple',
                m.track_voices, [K(('a', 'b', 1))])
    _raises(ValueError, SM, m.track_voices, [(S('a'), 'b', 1)])
    _raises(ValueError, VM, m.track_voices, [('a', S('b'), 1)])
    _raises(ValueError, IM, m.track_voices, [('a', 'b', I(1))])
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
    ('type(voice) is not str', 'not isinstance(voice, str)'),
    ('type(intensity) is not int', 'not isinstance(intensity, int)'),
    ('not 1 <= len(scene) <= 16', 'not 1 <= len(scene) <= 17'),
    ('not 1 <= len(voice) <= 16', 'not 1 <= len(voice) <= 17'),
    ('not 1 <= intensity <= 9', 'not 1 <= intensity <= 10'),
    ('        scenes[voice] += 1', '        scenes[voice] += 0'),
    ('        if previous is None or voice == previous:',
     '        if previous is None or voice != previous:'),
    ('            switches += 1', '            switches += 0'),
    ('            streak = 1', '            streak = 0'),
    ('        if streak > longest:', '        if streak < longest:'),
    ('        previous = voice', '        previous = scene'),
    ("'switches': switches", "'switches': longest"),
    ("'total': len(rows)", "'total': len(scenes)"),
    ('        scene, voice, intensity = row',
     '        voice, scene, intensity = row'),
    ('if dominant is None or scenes[voice] > scenes[dominant]:',
     'if dominant is None or scenes[voice] < scenes[dominant]:'),
    ('    for voice in scenes:', '    for voice in sorted(scenes):'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True

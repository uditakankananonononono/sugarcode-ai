import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import text_to_video_generation as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
CL = 'row 1: clip must be a string of 1 to 16 characters'
EN = 'row 1: engine must be a string of 1 to 16 characters'
FR = 'row 1: frames must be a nonbool integer between 1 and 9'


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
    assert section == ('temporal coherence, motion modeling, '
                       'rendering cost, content policy, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: frame mirroring over supplied counts'
    assert mod.NOT_CLAIMED == ('temporal coherence', 'motion modeling',
                               'rendering cost', 'content policy',
                               'production readiness')


def _expected(rows):
    seqs = {}
    for clip, engine, frames in rows:
        if engine not in seqs:
            seqs[engine] = []
        seqs[engine].append(frames)
    lengths = {}
    mirrored = []
    for engine in seqs:
        seq = seqs[engine]
        lengths[engine] = len(seq)
        if seq == seq[::-1]:
            mirrored.append(engine)
    longest = None
    for engine in mirrored:
        if longest is None or lengths[engine] > lengths[longest]:
            longest = engine
    return {'total': len(rows), 'lengths': lengths,
            'mirrored': sorted(mirrored), 'longest': longest}


def _core(m):
    # fixed pins, oracle seeded with row number 1928
    assert m.mirror_frames([('c', 'e1', 1), ('c', 'e1', 5), ('c', 'e1', 1),
                            ('c', 'e2', 3), ('c', 'e2', 4)]) == {
        'total': 5, 'lengths': {'e1': 3, 'e2': 2},
        'mirrored': ['e1'], 'longest': 'e1'}
    # one row always mirrors
    assert m.mirror_frames([('c', 'e', 5)]) == {
        'total': 1, 'lengths': {'e': 1}, 'mirrored': ['e'], 'longest': 'e'}
    # unequal pairs do not mirror
    assert m.mirror_frames([('a', 'x', 1), ('a', 'x', 2)]) == {
        'total': 2, 'lengths': {'x': 2}, 'mirrored': [], 'longest': None}
    # equal pairs do
    assert m.mirror_frames([('a', 'x', 2), ('a', 'x', 2)])['mirrored'] == ['x']
    # a near-miss in the middle still fails
    assert m.mirror_frames([('a', 'x', 1), ('a', 'x', 2), ('a', 'x', 3)]) == {
        'total': 3, 'lengths': {'x': 3}, 'mirrored': [], 'longest': None}
    # the longest tie goes to the first supplied engine
    r = m.mirror_frames([('c', 'Üser-9!', 1), ('c', 'q?7', 9),
                         ('c', 'Üser-9!', 1), ('c', 'q?7', 9)])
    assert r == {'total': 4, 'lengths': {'Üser-9!': 2, 'q?7': 2},
                 'mirrored': ['q?7', 'Üser-9!'], 'longest': 'Üser-9!'}
    # dicts keep first-touch order
    r = m.mirror_frames([('z', 'b', 7), ('a', 'a', 2)])
    assert r['lengths'] == {'b': 1, 'a': 1}
    # a longer mirror beats an earlier shorter one
    r = m.mirror_frames([('c', 'q', 2), ('c', 'p', 1),
                         ('c', 'p', 3), ('c', 'p', 1)])
    assert r['mirrored'] == ['p', 'q'] and r['longest'] == 'p'
    # pre-seed pin: fresh accumulators only
    assert m.mirror_frames([('c', 'p', 4), ('c', 'p', 4),
                            ('c', 'q', 1), ('c', 'q', 2)]) == {
        'total': 4, 'lengths': {'p': 2, 'q': 2},
        'mirrored': ['p'], 'longest': 'p'}
    rng = random.Random(1928)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.mirror_frames(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.mirror_frames, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.mirror_frames, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.mirror_frames, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.mirror_frames, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (clip, engine, frames) triple',
            m.mirror_frames, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.mirror_frames, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.mirror_frames, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, CL, m.mirror_frames, [(1, 'b', 1)])
    _raises(ValueError, CL, m.mirror_frames, [('', 'b', 1)])
    _raises(ValueError, CL, m.mirror_frames, [('x' * 17, 'b', 1)])
    _raises(ValueError, EN, m.mirror_frames, [('a', 1, 1)])
    _raises(ValueError, EN, m.mirror_frames, [('a', '', 1)])
    _raises(ValueError, EN, m.mirror_frames, [('a', 'x' * 17, 1)])
    _raises(ValueError, FR, m.mirror_frames, [('a', 'b', '1')])
    _raises(ValueError, FR, m.mirror_frames, [('a', 'b', 0)])
    _raises(ValueError, FR, m.mirror_frames, [('a', 'b', 10)])
    _raises(ValueError, FR, m.mirror_frames, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: clip must be a string of 1 to 16 characters',
            m.mirror_frames, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: frames must be a nonbool integer between 1 and 9',
            m.mirror_frames, [('a', 'b', 1), ('c', 'd', 0)])
    # clip is validated before engine, engine before frames
    _raises(ValueError, CL, m.mirror_frames, [('x' * 17, '', 0)])
    _raises(ValueError, EN, m.mirror_frames, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.mirror_frames, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.mirror_frames((('a', 'b', 1),)) == m.mirror_frames([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.mirror_frames([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.mirror_frames([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.mirror_frames([('a', 'b', 1)] * 60)['total'] == 60
    assert m.mirror_frames([('a', 'b', 9)])['lengths'] == {'b': 1}
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
        _raises(TypeError, P, m.mirror_frames, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (clip, engine, frames) triple',
                m.mirror_frames, [K(('a', 'b', 1))])
    _raises(ValueError, CL, m.mirror_frames, [(S('a'), 'b', 1)])
    _raises(ValueError, EN, m.mirror_frames, [('a', S('b'), 1)])
    _raises(ValueError, FR, m.mirror_frames, [('a', 'b', I(1))])
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
    ('type(clip) is not str', 'not isinstance(clip, str)'),
    ('type(engine) is not str', 'not isinstance(engine, str)'),
    ('type(frames) is not int', 'not isinstance(frames, int)'),
    ('not 1 <= len(clip) <= 16', 'not 1 <= len(clip) <= 17'),
    ('not 1 <= len(engine) <= 16', 'not 1 <= len(engine) <= 17'),
    ('not 1 <= frames <= 9', 'not 1 <= frames <= 10'),
    ('        seqs[engine].append(frames)', '        seqs[engine].append(1)'),
    ('        lengths[engine] = len(seq)', '        lengths[engine] = len(seq) + 1'),
    ('        if seq == seq[::-1]:', '        if seq != seq[::-1]:'),
    ('        if seq == seq[::-1]:', '        if seq == sorted(seq):'),
    ('if longest is None or lengths[engine] > lengths[longest]:',
     'if longest is None or lengths[engine] < lengths[longest]:'),
    ("'lengths': lengths", "'lengths': {}"),
    ("'mirrored': sorted(mirrored)", "'mirrored': []"),
    ("'longest': longest", "'longest': None"),
    ("'total': len(rows)", "'total': len(lengths)"),
    ('        clip, engine, frames = row',
     '        engine, clip, frames = row'),
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
    assert mod.mirror_frames([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.mirror_frames([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.mirror_frames([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

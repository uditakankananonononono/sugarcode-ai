import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import voice_cloning as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SA = 'row 1: sample must be a string of 1 to 16 characters'
VO = 'row 1: voice must be a string of 1 to 16 characters'
GA = 'row 1: gain must be a nonbool integer between 1 and 9'


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
    assert section == ('speaker similarity, prosody transfer, '
                       'artifact control, consent compliance, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: split-half gain drop over supplied rows'
    assert mod.NOT_CLAIMED == ('speaker similarity', 'prosody transfer',
                               'artifact control', 'consent compliance',
                               'production readiness')


def _expected(rows):
    seqs = {}
    for sample, voice, gain in rows:
        if voice not in seqs:
            seqs[voice] = []
        seqs[voice].append(gain)
    drops = {}
    for voice in seqs:
        seq = seqs[voice]
        half = len(seq) // 2
        drops[voice] = sum(seq[:half]) - sum(seq[half:])
    fading = sorted(v for v in drops if drops[v] > 0)
    steepest = None
    for voice in drops:
        if drops[voice] > 0 and (steepest is None or drops[voice] > drops[steepest]):
            steepest = voice
    return {'total': len(rows), 'drops': drops,
            'fading': fading, 'steepest': steepest}


def _core(m):
    # fixed pins, oracle seeded with row number 1932
    assert m.split_fade([('s', 'v1', 9), ('s', 'v1', 9), ('s', 'v1', 1),
                         ('s', 'v1', 1), ('s', 'v2', 1), ('s', 'v2', 9)]) == {
        'total': 6, 'drops': {'v1': 16, 'v2': -8},
        'fading': ['v1'], 'steepest': 'v1'}
    # a single row lands in the back half only
    assert m.split_fade([('s', 'v', 5)]) == {
        'total': 1, 'drops': {'v': -5}, 'fading': [], 'steepest': None}
    # equal halves do not fade
    assert m.split_fade([('s', 'x', 3), ('s', 'x', 3)])['drops'] == {'x': 0}
    assert m.split_fade([('s', 'x', 3), ('s', 'x', 3)])['fading'] == []
    # odd length: the middle gain counts toward the back
    assert m.split_fade([('s', 'x', 9), ('s', 'x', 1), ('s', 'x', 1)]) == {
        'total': 3, 'drops': {'x': 7}, 'fading': ['x'], 'steepest': 'x'}
    # the steepest tie goes to the first supplied voice
    r = m.split_fade([('s', 'Üser-9!', 9), ('s', 'Üser-9!', 1),
                      ('s', 'q?7', 9), ('s', 'q?7', 1)])
    assert r == {'total': 4, 'drops': {'Üser-9!': 8, 'q?7': 8},
                 'fading': ['q?7', 'Üser-9!'], 'steepest': 'Üser-9!'}
    # and the tie is not settled alphabetically
    r = m.split_fade([('s', 'b', 9), ('s', 'b', 1), ('s', 'a', 9), ('s', 'a', 1)])
    assert r['steepest'] == 'b' and r['fading'] == ['a', 'b']
    # dicts keep first-touch order
    r = m.split_fade([('z', 'b', 7), ('a', 'a', 2)])
    assert r['drops'] == {'b': -7, 'a': -2} and r['steepest'] is None
    # a rising voice never fades
    r = m.split_fade([('s', 'p', 5), ('s', 'q', 9), ('s', 'q', 1), ('s', 'q', 1)])
    assert r['drops'] == {'p': -5, 'q': 7}
    assert r['fading'] == ['q'] and r['steepest'] == 'q'
    # a bigger drop beats an earlier smaller one
    r = m.split_fade([('s', 'p', 5), ('s', 'p', 4), ('s', 'q', 9), ('s', 'q', 1)])
    assert r['fading'] == ['p', 'q'] and r['steepest'] == 'q'
    # pre-seed pin: fresh accumulators only
    assert m.split_fade([('s', 'a', 9), ('s', 'a', 2),
                         ('s', 'b', 1), ('s', 'b', 9)]) == {
        'total': 4, 'drops': {'a': 7, 'b': -8},
        'fading': ['a'], 'steepest': 'a'}
    rng = random.Random(1932)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.split_fade(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.split_fade, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.split_fade, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.split_fade, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.split_fade, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (sample, voice, gain) triple',
            m.split_fade, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.split_fade, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.split_fade, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SA, m.split_fade, [(1, 'b', 1)])
    _raises(ValueError, SA, m.split_fade, [('', 'b', 1)])
    _raises(ValueError, SA, m.split_fade, [('x' * 17, 'b', 1)])
    _raises(ValueError, VO, m.split_fade, [('a', 1, 1)])
    _raises(ValueError, VO, m.split_fade, [('a', '', 1)])
    _raises(ValueError, VO, m.split_fade, [('a', 'x' * 17, 1)])
    _raises(ValueError, GA, m.split_fade, [('a', 'b', '1')])
    _raises(ValueError, GA, m.split_fade, [('a', 'b', 0)])
    _raises(ValueError, GA, m.split_fade, [('a', 'b', 10)])
    _raises(ValueError, GA, m.split_fade, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: sample must be a string of 1 to 16 characters',
            m.split_fade, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: gain must be a nonbool integer between 1 and 9',
            m.split_fade, [('a', 'b', 1), ('c', 'd', 0)])
    # sample is validated before voice, voice before gain
    _raises(ValueError, SA, m.split_fade, [('x' * 17, '', 0)])
    _raises(ValueError, VO, m.split_fade, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.split_fade, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.split_fade((('a', 'b', 1),)) == m.split_fade([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.split_fade([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.split_fade([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.split_fade([('a', 'b', 1)] * 60)['total'] == 60
    assert m.split_fade([('a', 'b', 9)])['drops'] == {'b': -9}
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
        _raises(TypeError, P, m.split_fade, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (sample, voice, gain) triple',
                m.split_fade, [K(('a', 'b', 1))])
    _raises(ValueError, SA, m.split_fade, [(S('a'), 'b', 1)])
    _raises(ValueError, VO, m.split_fade, [('a', S('b'), 1)])
    _raises(ValueError, GA, m.split_fade, [('a', 'b', I(1))])
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
    ('type(sample) is not str', 'not isinstance(sample, str)'),
    ('type(voice) is not str', 'not isinstance(voice, str)'),
    ('type(gain) is not int', 'not isinstance(gain, int)'),
    ('not 1 <= len(sample) <= 16', 'not 1 <= len(sample) <= 17'),
    ('not 1 <= len(voice) <= 16', 'not 1 <= len(voice) <= 17'),
    ('not 1 <= gain <= 9', 'not 1 <= gain <= 10'),
    ('        seqs[voice].append(gain)', '        seqs[voice].append(1)'),
    ('        half = len(seq) // 2', '        half = len(seq) // 3'),
    ('drops[voice] = sum(seq[:half]) - sum(seq[half:])',
     'drops[voice] = sum(seq[:half]) + sum(seq[half:])'),
    ('drops[v] > 0', 'drops[v] >= 0'),
    ('drops[voice] > 0 and (steepest is None or drops[voice] > drops[steepest])',
     'drops[voice] > 0 and (steepest is None or drops[voice] < drops[steepest])'),
    ("'drops': drops", "'drops': {}"),
    ("'fading': fading", "'fading': []"),
    ("'steepest': steepest", "'steepest': None"),
    ("'total': len(rows)", "'total': len(drops)"),
    ('        sample, voice, gain = row',
     '        voice, sample, gain = row'),
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
    assert mod.split_fade([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.split_fade([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.split_fade([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

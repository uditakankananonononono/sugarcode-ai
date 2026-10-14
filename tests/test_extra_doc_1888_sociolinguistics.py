import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import sociolinguistics as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SM = 'row 1: speaker must be a string of 1 to 16 characters'
VM = 'row 1: variant must be a string of 1 to 16 characters'
FM = 'row 1: frequency must be a nonbool integer between 1 and 9'


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
    assert section == ('speech communities, social class, register, '
                       'accommodation theory, production readiness.')
    assert mod.SCOPE == 'PARTIAL: variant tracking over supplied frequencies'
    assert mod.NOT_CLAIMED == ('speech communities', 'social class',
                               'register', 'accommodation theory',
                               'production readiness')


def _expected(rows):
    first = {}
    latest = {}
    variants_of = {}
    total = {}
    for speaker, variant, frequency in rows:
        if speaker not in first:
            first[speaker] = variant
            variants_of[speaker] = {}
        latest[speaker] = variant
        variants_of[speaker][variant] = True
        if variant not in total:
            total[variant] = 0
        total[variant] += frequency
    shifters = sorted(speaker for speaker in first
                      if latest[speaker] != first[speaker])
    stable = sorted(speaker for speaker in variants_of
                    if len(variants_of[speaker]) == 1)
    prestige = None
    for variant in total:
        if prestige is None or total[variant] > total[prestige]:
            prestige = variant
    return {'total': len(rows), 'shifters': shifters, 'stable': stable,
            'frequency': total, 'prestige': prestige}


def _core(m):
    # fixed pins, oracle seeded with row number 1888
    assert m.track_variants([('ann', 'in', 5), ('bob', 'ing', 3),
                             ('ann', 'ing', 7)]) == {
        'total': 3, 'shifters': ['ann'], 'stable': ['bob'],
        'frequency': {'in': 5, 'ing': 10}, 'prestige': 'ing'}
    # one row: the only speaker is stable on the only variant
    assert m.track_variants([('s', 'v', 5)]) == {
        'total': 1, 'shifters': [], 'stable': ['s'],
        'frequency': {'v': 5}, 'prestige': 'v'}
    # returning to the first variant is neither shifter nor stable
    r = m.track_variants([('s', 'a', 1), ('s', 'b', 1), ('s', 'a', 1)])
    assert r['shifters'] == [] and r['stable'] == []
    # two variants, never returning: shifter and not stable
    r = m.track_variants([('s', 'a', 1), ('s', 'b', 1)])
    assert r['shifters'] == ['s'] and r['stable'] == []
    # same variant twice keeps the speaker stable
    r = m.track_variants([('s', 'a', 1), ('s', 'a', 9)])
    assert r['shifters'] == [] and r['stable'] == ['s']
    # the prestige tie goes to the first supplied
    r = m.track_variants([('s1', 'a', 5), ('s2', 'b', 5)])
    assert r['prestige'] == 'a'
    # frequency piles up across speakers on one variant
    r = m.track_variants([('s1', 'v', 2), ('s2', 'v', 3)])
    assert r['frequency'] == {'v': 5}
    # dicts keep first-touch order
    r = m.track_variants([('s', 'z', 1), ('s', 'a', 2)])
    assert r['frequency'] == {'z': 1, 'a': 2}
    # non-ASCII speakers and variants follow the same rule
    r = m.track_variants([('Üser-9!', 'Ω-1', 9), ('q?7', 'Ω-1', 1)])
    assert r == {'total': 2, 'shifters': [], 'stable': ['q?7', 'Üser-9!'],
                 'frequency': {'Ω-1': 10}, 'prestige': 'Ω-1'}
    rng = random.Random(1888)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.track_variants(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.track_variants, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.track_variants, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_variants, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_variants, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (speaker, variant, frequency) triple',
            m.track_variants, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.track_variants, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.track_variants, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SM, m.track_variants, [(1, 'b', 1)])
    _raises(ValueError, SM, m.track_variants, [('', 'b', 1)])
    _raises(ValueError, SM, m.track_variants, [('x' * 17, 'b', 1)])
    _raises(ValueError, VM, m.track_variants, [('a', 1, 1)])
    _raises(ValueError, VM, m.track_variants, [('a', '', 1)])
    _raises(ValueError, VM, m.track_variants, [('a', 'x' * 17, 1)])
    _raises(ValueError, FM, m.track_variants, [('a', 'b', '1')])
    _raises(ValueError, FM, m.track_variants, [('a', 'b', 0)])
    _raises(ValueError, FM, m.track_variants, [('a', 'b', 10)])
    _raises(ValueError, FM, m.track_variants, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: speaker must be a string of 1 to 16 characters',
            m.track_variants, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: frequency must be a nonbool integer between 1 and 9',
            m.track_variants, [('a', 'b', 1), ('c', 'd', 0)])
    # speaker is validated before variant, variant before frequency
    _raises(ValueError, SM, m.track_variants, [('x' * 17, '', 0)])
    _raises(ValueError, VM, m.track_variants, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.track_variants, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.track_variants((('a', 'b', 1),)) == m.track_variants([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.track_variants([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.track_variants([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.track_variants([('a', 'b', 1)] * 60)['total'] == 60
    assert m.track_variants([('a', 'b', 9)])['frequency'] == {'b': 9}
    # pre-seed pin: fresh accumulators only
    assert m.track_variants([('p', 'a', 9), ('q', 'b', 1), ('p', 'b', 2)]) == {
        'total': 3, 'shifters': ['p'], 'stable': ['q'],
        'frequency': {'a': 9, 'b': 3}, 'prestige': 'a'}
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
        _raises(TypeError, P, m.track_variants, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (speaker, variant, frequency) triple',
                m.track_variants, [K(('a', 'b', 1))])
    _raises(ValueError, SM, m.track_variants, [(S('a'), 'b', 1)])
    _raises(ValueError, VM, m.track_variants, [('a', S('b'), 1)])
    _raises(ValueError, FM, m.track_variants, [('a', 'b', I(1))])
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
    ('type(speaker) is not str', 'not isinstance(speaker, str)'),
    ('type(variant) is not str', 'not isinstance(variant, str)'),
    ('type(frequency) is not int', 'not isinstance(frequency, int)'),
    ('not 1 <= len(speaker) <= 16', 'not 1 <= len(speaker) <= 17'),
    ('not 1 <= len(variant) <= 16', 'not 1 <= len(variant) <= 17'),
    ('not 1 <= frequency <= 9', 'not 1 <= frequency <= 10'),
    ('        latest[speaker] = variant', '        latest[speaker] = first[speaker]'),
    ('        total[variant] += frequency', '        total[variant] += 1'),
    ('if latest[speaker] != first[speaker]',
     'if latest[speaker] == first[speaker]'),
    ('if len(variants_of[speaker]) == 1', 'if len(variants_of[speaker]) == 2'),
    ('if prestige is None or total[variant] > total[prestige]:',
     'if prestige is None or total[variant] < total[prestige]:'),
    ("'shifters': shifters", "'shifters': stable"),
    ("'frequency': total", "'frequency': variants_of"),
    ("'total': len(rows)", "'total': len(total)"),
    ('        speaker, variant, frequency = row',
     '        variant, speaker, frequency = row'),
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
    assert mod.track_variants([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.track_variants([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.track_variants([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

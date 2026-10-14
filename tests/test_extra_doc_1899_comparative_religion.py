import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import comparative_religion as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
TD = 'row 1: tradition must be a string of 1 to 16 characters'
RT = 'row 1: ritual must be a string of 1 to 16 characters'
FQ = 'row 1: frequency must be a nonbool integer between 1 and 9'


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
    assert section == ('phenomenology, fieldwork, sacred texts, '
                       'anthropology of religion, production readiness.')
    assert mod.SCOPE == 'PARTIAL: ritual comparison over supplied frequencies'
    assert mod.NOT_CLAIMED == ('phenomenology', 'fieldwork', 'sacred texts',
                               'anthropology of religion',
                               'production readiness')


def _expected(rows):
    hist = {}
    for tradition, ritual, frequency in rows:
        if tradition not in hist:
            hist[tradition] = {}
        hist[tradition][frequency] = hist[tradition].get(frequency, 0) + 1
    modes = {}
    for tradition in hist:
        best_value = None
        best_count = 0
        for frequency in sorted(hist[tradition]):
            if hist[tradition][frequency] > best_count:
                best_value = frequency
                best_count = hist[tradition][frequency]
        modes[tradition] = best_value
    canonical = sorted(t for t in hist if max(hist[t].values()) >= 3)
    unrepeated = sorted(t for t in hist if len(hist[t]) >= 2 and max(hist[t].values()) == 1)
    typical = None
    for tradition in hist:
        if typical is None or max(hist[tradition].values()) > max(hist[typical].values()):
            typical = tradition
    return {'total': len(rows), 'modes': modes, 'canonical': canonical,
            'unrepeated': unrepeated, 'typical': typical}


def _core(m):
    # fixed pins, oracle seeded with row number 1899
    assert m.compare_rituals([('a', 'r', 5), ('a', 's', 5), ('a', 't', 5),
                              ('b', 'u', 1), ('b', 'v', 2), ('b', 'w', 3)]) == {
        'total': 6, 'modes': {'a': 5, 'b': 1}, 'canonical': ['a'],
        'unrepeated': ['b'], 'typical': 'a'}
    # one row: its frequency is the mode, nothing else qualifies
    assert m.compare_rituals([('t', 'r', 5)]) == {
        'total': 1, 'modes': {'t': 5}, 'canonical': [],
        'unrepeated': [], 'typical': 't'}
    # a mode tie goes to the smallest frequency
    r = m.compare_rituals([('t', 'a', 9), ('t', 'b', 1),
                           ('t', 'c', 9), ('t', 'd', 1)])
    assert r['modes'] == {'t': 1}
    # a repeat count of exactly 3 is canonical, 2 is not
    assert m.compare_rituals([('t', 'a', 7), ('t', 'b', 7),
                              ('t', 'c', 7)])['canonical'] == ['t']
    r = m.compare_rituals([('t', 'a', 7), ('t', 'b', 7)])
    assert r['canonical'] == [] and r['unrepeated'] == []
    # two rows with distinct frequencies are unrepeated
    assert m.compare_rituals([('t', 'a', 1), ('t', 'b', 2)])['unrepeated'] == ['t']
    # the typical tie goes to the first supplied tradition
    r = m.compare_rituals([('a', 'r', 5), ('a', 's', 5),
                           ('b', 't', 9), ('b', 'u', 9)])
    assert r['typical'] == 'a'
    # dicts keep first-touch order
    r = m.compare_rituals([('z', 'r', 1), ('a', 's', 2)])
    assert r['modes'] == {'z': 1, 'a': 2}
    # non-ASCII traditions follow the same rule
    r = m.compare_rituals([('Üser-9!', 'a', 9), ('Üser-9!', 'b', 9),
                           ('Üser-9!', 'c', 9), ('q?7', 'd', 1), ('q?7', 'e', 2)])
    assert r == {'total': 5, 'modes': {'Üser-9!': 9, 'q?7': 1},
                 'canonical': ['Üser-9!'], 'unrepeated': ['q?7'],
                 'typical': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.compare_rituals([('p', 'a', 4), ('p', 'b', 4), ('p', 'c', 4),
                              ('q', 'd', 1), ('q', 'e', 2)]) == {
        'total': 5, 'modes': {'p': 4, 'q': 1}, 'canonical': ['p'],
        'unrepeated': ['q'], 'typical': 'p'}
    rng = random.Random(1899)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.compare_rituals(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.compare_rituals, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.compare_rituals, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.compare_rituals, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.compare_rituals, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (tradition, ritual, frequency) triple',
            m.compare_rituals, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.compare_rituals, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.compare_rituals, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, TD, m.compare_rituals, [(1, 'b', 1)])
    _raises(ValueError, TD, m.compare_rituals, [('', 'b', 1)])
    _raises(ValueError, TD, m.compare_rituals, [('x' * 17, 'b', 1)])
    _raises(ValueError, RT, m.compare_rituals, [('a', 1, 1)])
    _raises(ValueError, RT, m.compare_rituals, [('a', '', 1)])
    _raises(ValueError, RT, m.compare_rituals, [('a', 'x' * 17, 1)])
    _raises(ValueError, FQ, m.compare_rituals, [('a', 'b', '1')])
    _raises(ValueError, FQ, m.compare_rituals, [('a', 'b', 0)])
    _raises(ValueError, FQ, m.compare_rituals, [('a', 'b', 10)])
    _raises(ValueError, FQ, m.compare_rituals, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: tradition must be a string of 1 to 16 characters',
            m.compare_rituals, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: frequency must be a nonbool integer between 1 and 9',
            m.compare_rituals, [('a', 'b', 1), ('c', 'd', 0)])
    # tradition is validated before ritual, ritual before frequency
    _raises(ValueError, TD, m.compare_rituals, [('x' * 17, '', 0)])
    _raises(ValueError, RT, m.compare_rituals, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.compare_rituals, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.compare_rituals((('a', 'b', 1),)) == m.compare_rituals([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.compare_rituals([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.compare_rituals([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.compare_rituals([('a', 'b', 1)] * 60)['total'] == 60
    assert m.compare_rituals([('a', 'b', 9)])['modes'] == {'a': 9}
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
        _raises(TypeError, P, m.compare_rituals, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (tradition, ritual, frequency) triple',
                m.compare_rituals, [K(('a', 'b', 1))])
    _raises(ValueError, TD, m.compare_rituals, [(S('a'), 'b', 1)])
    _raises(ValueError, RT, m.compare_rituals, [('a', S('b'), 1)])
    _raises(ValueError, FQ, m.compare_rituals, [('a', 'b', I(1))])
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
    ('type(tradition) is not str', 'not isinstance(tradition, str)'),
    ('type(ritual) is not str', 'not isinstance(ritual, str)'),
    ('type(frequency) is not int', 'not isinstance(frequency, int)'),
    ('not 1 <= len(tradition) <= 16', 'not 1 <= len(tradition) <= 17'),
    ('not 1 <= len(ritual) <= 16', 'not 1 <= len(ritual) <= 17'),
    ('not 1 <= frequency <= 9', 'not 1 <= frequency <= 10'),
    ('        if tradition not in hist:', '        if tradition in hist:'),
    ('hist[tradition].get(frequency, 0) + 1',
     'hist[tradition].get(frequency, 1) + 1'),
    ('        for frequency in sorted(hist[tradition]):',
     '        for frequency in sorted(hist[tradition], reverse=True):'),
    ('            if hist[tradition][frequency] > best_count:',
     '            if hist[tradition][frequency] >= best_count:'),
    ('if max(hist[t].values()) >= 3', 'if max(hist[t].values()) >= 4'),
    ('if len(hist[t]) >= 2 and max(hist[t].values()) == 1',
     'if len(hist[t]) >= 2 and max(hist[t].values()) == 2'),
    ('if len(hist[t]) >= 2 and max(hist[t].values()) == 1',
     'if len(hist[t]) >= 3 and max(hist[t].values()) == 1'),
    ('or max(hist[tradition].values()) > max(hist[typical].values())',
     'or max(hist[tradition].values()) >= max(hist[typical].values())'),
    ("'modes': modes", "'modes': hist"),
    ("'canonical': canonical", "'canonical': unrepeated"),
    ("'total': len(rows)", "'total': len(modes)"),
    ('        tradition, ritual, frequency = row',
     '        ritual, tradition, frequency = row'),
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
    assert mod.compare_rituals([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.compare_rituals([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.compare_rituals([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import translation_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PS = 'row 1: passage must be a string of 1 to 16 characters'
TR = 'row 1: translator must be a string of 1 to 16 characters'
FD = 'row 1: fidelity must be a nonbool integer between 1 and 9'


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
    assert section == ('translation quality judgment, fluency measurement, '
                       'adequacy testing, machine translation, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: translation assessment over supplied fidelities'
    assert mod.NOT_CLAIMED == ('translation quality judgment',
                               'fluency measurement',
                               'adequacy testing', 'machine translation',
                               'production readiness')


def _expected(rows):
    counts = {}
    low = {}
    high = {}
    for passage, translator, fidelity in rows:
        if passage not in counts:
            counts[passage] = 0
            low[passage] = fidelity
            high[passage] = fidelity
        counts[passage] += 1
        if fidelity < low[passage]:
            low[passage] = fidelity
        if fidelity > high[passage]:
            high[passage] = fidelity
    consensus = sorted(p for p in counts if counts[p] >= 2 and high[p] == low[p])
    disputed = sorted(p for p in counts if high[p] - low[p] >= 6)
    polarizing = None
    for p in counts:
        if polarizing is None or high[p] - low[p] > high[polarizing] - low[polarizing]:
            polarizing = p
    return {'total': len(rows), 'counts': counts, 'consensus': consensus,
            'disputed': disputed, 'polarizing': polarizing}


def _core(m):
    # fixed pins, oracle seeded with row number 1895
    assert m.assess_translations([('p1', 'ann', 5), ('p1', 'bob', 5),
                                  ('p2', 'ann', 1), ('p2', 'bob', 9)]) == {
        'total': 4, 'counts': {'p1': 2, 'p2': 2}, 'consensus': ['p1'],
        'disputed': ['p2'], 'polarizing': 'p2'}
    # one translation is never a consensus
    assert m.assess_translations([('p', 't', 5)]) == {
        'total': 1, 'counts': {'p': 1}, 'consensus': [],
        'disputed': [], 'polarizing': 'p'}
    # two agreeing translations make a consensus
    r = m.assess_translations([('p', 'a', 4), ('p', 'b', 4)])
    assert r['consensus'] == ['p'] and r['disputed'] == []
    # a spread of exactly 6 disputes, 5 does not
    r = m.assess_translations([('p', 'a', 1), ('p', 'b', 7)])
    assert r['disputed'] == ['p'] and r['consensus'] == []
    r = m.assess_translations([('p', 'a', 1), ('p', 'b', 6)])
    assert r['disputed'] == []
    r = m.assess_translations([('p', 'a', 2), ('p', 'b', 8)])
    assert r['disputed'] == ['p']
    # consensus and dispute lists are sorted, not first-touch order
    r = m.assess_translations([('b', 'a', 3), ('b', 'c', 3),
                               ('a', 'd', 3), ('a', 'e', 3)])
    assert r['consensus'] == ['a', 'b']
    # the polarizing tie goes to the first supplied passage
    r = m.assess_translations([('p1', 'a', 1), ('p1', 'b', 9),
                               ('p2', 'c', 1), ('p2', 'd', 9)])
    assert r['disputed'] == ['p1', 'p2'] and r['polarizing'] == 'p1'
    # a single translator may assess a passage more than once
    r = m.assess_translations([('p', 't', 3), ('p', 't', 3)])
    assert r['counts'] == {'p': 2} and r['consensus'] == ['p']
    # dicts keep first-touch order
    r = m.assess_translations([('z', 't', 1), ('a', 't', 2)])
    assert r['counts'] == {'z': 1, 'a': 1}
    # non-ASCII passages sort by codepoint
    r = m.assess_translations([('Ü', 'a', 1), ('Ü', 'b', 9),
                               ('q', 'c', 1), ('q', 'd', 9)])
    assert r == {'total': 4, 'counts': {'Ü': 2, 'q': 2}, 'consensus': [],
                 'disputed': ['q', 'Ü'], 'polarizing': 'Ü'}
    rng = random.Random(1895)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.assess_translations(rows) == _expected(rows)
    return True


def _late(m):
    P = 'rows must be a list or tuple'
    _raises(TypeError, P, m.assess_translations, 'ab')
    _raises(TypeError, P, m.assess_translations, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.assess_translations, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.assess_translations, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (passage, translator, fidelity) triple',
            m.assess_translations, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.assess_translations, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.assess_translations, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PS, m.assess_translations, [(1, 'b', 1)])
    _raises(ValueError, PS, m.assess_translations, [('', 'b', 1)])
    _raises(ValueError, PS, m.assess_translations, [('x' * 17, 'b', 1)])
    _raises(ValueError, TR, m.assess_translations, [('a', 1, 1)])
    _raises(ValueError, TR, m.assess_translations, [('a', '', 1)])
    _raises(ValueError, TR, m.assess_translations, [('a', 'x' * 17, 1)])
    _raises(ValueError, FD, m.assess_translations, [('a', 'b', '1')])
    _raises(ValueError, FD, m.assess_translations, [('a', 'b', 0)])
    _raises(ValueError, FD, m.assess_translations, [('a', 'b', 10)])
    _raises(ValueError, FD, m.assess_translations, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: passage must be a string of 1 to 16 characters',
            m.assess_translations, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: fidelity must be a nonbool integer between 1 and 9',
            m.assess_translations, [('a', 'b', 1), ('c', 'd', 0)])
    # passage is validated before translator, translator before fidelity
    _raises(ValueError, PS, m.assess_translations, [('x' * 17, '', 0)])
    _raises(ValueError, TR, m.assess_translations, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, P, m.assess_translations, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.assess_translations((('a', 'b', 1),)) == m.assess_translations([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.assess_translations([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.assess_translations([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.assess_translations([('a', 'b', 1)] * 60)['total'] == 60
    assert m.assess_translations([('a', 'b', 9)])['counts'] == {'a': 1}
    # pre-seed pin: fresh accumulators only
    assert m.assess_translations([('p', 'a', 1), ('p', 'b', 9),
                                  ('q', 'c', 5)]) == {
        'total': 3, 'counts': {'p': 2, 'q': 1}, 'consensus': [],
        'disputed': ['p'], 'polarizing': 'p'}
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
        _raises(TypeError, P, m.assess_translations, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (passage, translator, fidelity) triple',
                m.assess_translations, [K(('a', 'b', 1))])
    _raises(ValueError, PS, m.assess_translations, [(S('a'), 'b', 1)])
    _raises(ValueError, TR, m.assess_translations, [('a', S('b'), 1)])
    _raises(ValueError, FD, m.assess_translations, [('a', 'b', I(1))])
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
    ('type(passage) is not str', 'not isinstance(passage, str)'),
    ('type(translator) is not str', 'not isinstance(translator, str)'),
    ('type(fidelity) is not int', 'not isinstance(fidelity, int)'),
    ('not 1 <= len(passage) <= 16', 'not 1 <= len(passage) <= 17'),
    ('not 1 <= len(translator) <= 16', 'not 1 <= len(translator) <= 17'),
    ('not 1 <= fidelity <= 9', 'not 1 <= fidelity <= 10'),
    ('        counts[passage] += 1', '        counts[passage] += 2'),
    ('if counts[p] >= 2 and high[p] == low[p]',
     'if counts[p] >= 2 and high[p] != low[p]'),
    ('if counts[p] >= 2 and high[p] == low[p]',
     'if counts[p] >= 3 and high[p] == low[p]'),
    ('if high[p] - low[p] >= 6', 'if high[p] - low[p] >= 7'),
    ('or high[p] - low[p] > high[polarizing] - low[polarizing]',
     'or high[p] - low[p] >= high[polarizing] - low[polarizing]'),
    ('or high[p] - low[p] > high[polarizing] - low[polarizing]',
     'or high[p] - low[p] < high[polarizing] - low[polarizing]'),
    ("'consensus': consensus", "'consensus': disputed"),
    ("'counts': counts", "'counts': low"),
    ("'total': len(rows)", "'total': len(counts)"),
    ('        passage, translator, fidelity = row',
     '        translator, passage, fidelity = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
    ('        if fidelity < low[passage]:', '        if fidelity > low[passage]:'),
    ('        if fidelity > high[passage]:', '        if fidelity < high[passage]:'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True


def test_gap_pin_exact_cap_acceptance():
    # gap sweep: exact-cap 16-char labels accepted in each label
    # position, and on a late row
    assert mod.assess_translations([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.assess_translations([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.assess_translations([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

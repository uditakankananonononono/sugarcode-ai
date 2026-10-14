import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import interpretation_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
TX = 'row 1: text must be a string of 1 to 16 characters'
RD = 'row 1: reader must be a string of 1 to 16 characters'
CL = 'row 1: clarity must be a nonbool integer between 1 and 9'


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
    assert section == ('hermeneutic method, authorial intent, reader '
                       'psychology, meaning determination, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: clarity gauging over supplied readings'
    assert mod.NOT_CLAIMED == ('hermeneutic method', 'authorial intent',
                               'reader psychology',
                               'meaning determination',
                               'production readiness')


def _expected(rows):
    readings = {}
    for text, reader, clarity in rows:
        if text not in readings:
            readings[text] = []
        readings[text].append(clarity)
    medians = {}
    for text in readings:
        vals = sorted(readings[text])
        medians[text] = vals[(len(vals) - 1) // 2]
    lucid = sorted(t for t in medians if medians[t] >= 7)
    murky = sorted(t for t in medians if medians[t] <= 3)
    clearest = None
    for text in medians:
        if clearest is None or medians[text] > medians[clearest]:
            clearest = text
    return {'total': len(rows), 'medians': medians, 'lucid': lucid,
            'murky': murky, 'clearest': clearest}


def _core(m):
    # fixed pins, oracle seeded with row number 1896
    assert m.gauge_clarity([('t1', 'a', 3), ('t1', 'b', 9),
                            ('t2', 'c', 7), ('t2', 'd', 8)]) == {
        'total': 4, 'medians': {'t1': 3, 't2': 7}, 'lucid': ['t2'],
        'murky': ['t1'], 'clearest': 't2'}
    # the median is the lower middle of the sorted values
    assert m.gauge_clarity([('t1', 'a', 9), ('t1', 'b', 3)]) == {
        'total': 2, 'medians': {'t1': 3}, 'lucid': [],
        'murky': ['t1'], 'clearest': 't1'}
    # one reading is its own median, neither lucid nor murky
    assert m.gauge_clarity([('t', 'a', 5)]) == {
        'total': 1, 'medians': {'t': 5}, 'lucid': [],
        'murky': [], 'clearest': 't'}
    # a median of exactly 7 is lucid, 6 is not
    assert m.gauge_clarity([('t', 'a', 7)])['lucid'] == ['t']
    assert m.gauge_clarity([('t', 'a', 6)])['lucid'] == []
    # a median of exactly 3 is murky, 4 is not
    assert m.gauge_clarity([('t', 'a', 3)])['murky'] == ['t']
    assert m.gauge_clarity([('t', 'a', 4)])['murky'] == []
    # the clearest tie goes to the first supplied text
    r = m.gauge_clarity([('a', 'r', 7), ('b', 'r', 7)])
    assert r['lucid'] == ['a', 'b'] and r['clearest'] == 'a'
    # dicts keep first-touch order
    r = m.gauge_clarity([('z', 'r', 4), ('a', 'r', 6)])
    assert r['medians'] == {'z': 4, 'a': 6} and r['clearest'] == 'a'
    # non-ASCII texts sort by codepoint
    r = m.gauge_clarity([('Üser-9!', 'a', 9), ('q?7', 'b', 8), ('q?7', 'c', 9)])
    assert r == {'total': 3, 'medians': {'Üser-9!': 9, 'q?7': 8},
                 'lucid': ['q?7', 'Üser-9!'], 'murky': [],
                 'clearest': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.gauge_clarity([('p', 'a', 7), ('p', 'b', 2), ('q', 'c', 5)]) == {
        'total': 3, 'medians': {'p': 2, 'q': 5}, 'lucid': [],
        'murky': ['p'], 'clearest': 'q'}
    rng = random.Random(1896)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.gauge_clarity(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.gauge_clarity, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.gauge_clarity, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.gauge_clarity, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.gauge_clarity, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (text, reader, clarity) triple',
            m.gauge_clarity, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.gauge_clarity, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.gauge_clarity, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, TX, m.gauge_clarity, [(1, 'b', 1)])
    _raises(ValueError, TX, m.gauge_clarity, [('', 'b', 1)])
    _raises(ValueError, TX, m.gauge_clarity, [('x' * 17, 'b', 1)])
    _raises(ValueError, RD, m.gauge_clarity, [('a', 1, 1)])
    _raises(ValueError, RD, m.gauge_clarity, [('a', '', 1)])
    _raises(ValueError, RD, m.gauge_clarity, [('a', 'x' * 17, 1)])
    _raises(ValueError, CL, m.gauge_clarity, [('a', 'b', '1')])
    _raises(ValueError, CL, m.gauge_clarity, [('a', 'b', 0)])
    _raises(ValueError, CL, m.gauge_clarity, [('a', 'b', 10)])
    _raises(ValueError, CL, m.gauge_clarity, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: text must be a string of 1 to 16 characters',
            m.gauge_clarity, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: clarity must be a nonbool integer between 1 and 9',
            m.gauge_clarity, [('a', 'b', 1), ('c', 'd', 0)])
    # text is validated before reader, reader before clarity
    _raises(ValueError, TX, m.gauge_clarity, [('x' * 17, '', 0)])
    _raises(ValueError, RD, m.gauge_clarity, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.gauge_clarity, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.gauge_clarity((('a', 'b', 1),)) == m.gauge_clarity([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.gauge_clarity([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.gauge_clarity([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.gauge_clarity([('a', 'b', 1)] * 60)['total'] == 60
    assert m.gauge_clarity([('a', 'b', 9)])['medians'] == {'a': 9}
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
        _raises(TypeError, P, m.gauge_clarity, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (text, reader, clarity) triple',
                m.gauge_clarity, [K(('a', 'b', 1))])
    _raises(ValueError, TX, m.gauge_clarity, [(S('a'), 'b', 1)])
    _raises(ValueError, RD, m.gauge_clarity, [('a', S('b'), 1)])
    _raises(ValueError, CL, m.gauge_clarity, [('a', 'b', I(1))])
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
    ('type(text) is not str', 'not isinstance(text, str)'),
    ('type(reader) is not str', 'not isinstance(reader, str)'),
    ('type(clarity) is not int', 'not isinstance(clarity, int)'),
    ('not 1 <= len(text) <= 16', 'not 1 <= len(text) <= 17'),
    ('not 1 <= len(reader) <= 16', 'not 1 <= len(reader) <= 17'),
    ('not 1 <= clarity <= 9', 'not 1 <= clarity <= 10'),
    ('        readings[text].append(clarity)',
     '        readings[text].append(1)'),
    ('medians[text] = vals[(len(vals) - 1) // 2]',
     'medians[text] = vals[len(vals) // 2]'),
    ('if medians[t] >= 7', 'if medians[t] >= 8'),
    ('if medians[t] <= 3', 'if medians[t] <= 2'),
    ('if clearest is None or medians[text] > medians[clearest]:',
     'if clearest is None or medians[text] >= medians[clearest]:'),
    ('if clearest is None or medians[text] > medians[clearest]:',
     'if clearest is None or medians[text] < medians[clearest]:'),
    ("'lucid': lucid", "'lucid': murky"),
    ("'medians': medians", "'medians': readings"),
    ("'total': len(rows)", "'total': len(medians)"),
    ('        text, reader, clarity = row',
     '        reader, text, clarity = row'),
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
    assert mod.gauge_clarity([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.gauge_clarity([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.gauge_clarity([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

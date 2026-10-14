import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import historical_linguistics as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
WM = 'row 1: word must be a string of 1 to 16 characters'
TM = 'row 1: stage must be a string of 1 to 16 characters'
SM = 'row 1: score must be a nonbool integer between 1 and 9'


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
    assert section == ('sound laws, reconstruction, cognate judgment, '
                       'language change, production readiness.')
    assert mod.SCOPE == 'PARTIAL: shift tracing over supplied scores'
    assert mod.NOT_CLAIMED == ('sound laws', 'reconstruction',
                               'cognate judgment', 'language change',
                               'production readiness')


def _expected(rows):
    first = {}
    latest = {}
    for word, stage, score in rows:
        if word not in first:
            first[word] = score
        latest[word] = score
    drift = {}
    for word in first:
        drift[word] = latest[word] - first[word]
    risen = sorted(word for word in drift if drift[word] >= 3)
    fallen = sorted(word for word in drift if drift[word] <= -3)
    volatile = None
    for word in drift:
        if volatile is None or abs(drift[word]) > abs(drift[volatile]):
            volatile = word
    return {'total': len(rows), 'drift': drift, 'risen': risen,
            'fallen': fallen, 'volatile': volatile}


def _core(m):
    # fixed pins, oracle seeded with row number 1891
    assert m.trace_shifts([('hus', 'old', 3), ('hus', 'mid', 9),
                           ('cat', 'old', 8), ('cat', 'mid', 2)]) == {
        'total': 4, 'drift': {'hus': 6, 'cat': -6}, 'risen': ['hus'],
        'fallen': ['cat'], 'volatile': 'hus'}
    # one row: no drift at all
    assert m.trace_shifts([('w', 's', 5)]) == {
        'total': 1, 'drift': {'w': 0}, 'risen': [], 'fallen': [],
        'volatile': 'w'}
    # boundary drifts: 3 risen, 2 neither, -3 fallen, -2 neither
    r = m.trace_shifts([('a', 's', 1), ('a', 't', 4),
                        ('b', 's', 1), ('b', 't', 3),
                        ('c', 's', 9), ('c', 't', 6),
                        ('d', 's', 9), ('d', 't', 7)])
    assert r['risen'] == ['a'] and r['fallen'] == ['c']
    assert r['drift'] == {'a': 3, 'b': 2, 'c': -3, 'd': -2}
    # the middle stages never matter, only first and latest
    r = m.trace_shifts([('w', 'a', 5), ('w', 'b', 9), ('w', 'c', 1)])
    assert r['drift'] == {'w': -4}
    # the volatile tie goes to the first supplied
    r = m.trace_shifts([('a', 's', 1), ('a', 't', 5),
                        ('b', 's', 9), ('b', 't', 5)])
    assert r['volatile'] == 'a'
    # a fall outweighs a smaller rise for volatility
    r = m.trace_shifts([('a', 's', 1), ('a', 't', 4),
                        ('b', 's', 9), ('b', 't', 3)])
    assert r['volatile'] == 'b'
    # dicts keep first-touch order
    r = m.trace_shifts([('z', 's', 1), ('a', 's', 2)])
    assert r['drift'] == {'z': 0, 'a': 0}
    # non-ASCII words and stages follow the same rule
    r = m.trace_shifts([('Üser-9!', 'Ω-1', 1), ('Üser-9!', 'q?7', 9)])
    assert r == {'total': 2, 'drift': {'Üser-9!': 8}, 'risen': ['Üser-9!'],
                 'fallen': [], 'volatile': 'Üser-9!'}
    rng = random.Random(1891)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.trace_shifts(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.trace_shifts, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.trace_shifts, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.trace_shifts, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.trace_shifts, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (word, stage, score) triple',
            m.trace_shifts, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.trace_shifts, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.trace_shifts, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, WM, m.trace_shifts, [(1, 'b', 1)])
    _raises(ValueError, WM, m.trace_shifts, [('', 'b', 1)])
    _raises(ValueError, WM, m.trace_shifts, [('x' * 17, 'b', 1)])
    _raises(ValueError, TM, m.trace_shifts, [('a', 1, 1)])
    _raises(ValueError, TM, m.trace_shifts, [('a', '', 1)])
    _raises(ValueError, TM, m.trace_shifts, [('a', 'x' * 17, 1)])
    _raises(ValueError, SM, m.trace_shifts, [('a', 'b', '1')])
    _raises(ValueError, SM, m.trace_shifts, [('a', 'b', 0)])
    _raises(ValueError, SM, m.trace_shifts, [('a', 'b', 10)])
    _raises(ValueError, SM, m.trace_shifts, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: word must be a string of 1 to 16 characters',
            m.trace_shifts, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.trace_shifts, [('a', 'b', 1), ('c', 'd', 0)])
    # word is validated before stage, stage before score
    _raises(ValueError, WM, m.trace_shifts, [('x' * 17, '', 0)])
    _raises(ValueError, TM, m.trace_shifts, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.trace_shifts, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.trace_shifts((('a', 'b', 1),)) == m.trace_shifts([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.trace_shifts([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.trace_shifts([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.trace_shifts([('a', 'b', 1)] * 60)['total'] == 60
    assert m.trace_shifts([('a', 'b', 9)])['drift'] == {'a': 0}
    # pre-seed pin: fresh accumulators only
    assert m.trace_shifts([('p', 'a', 2), ('p', 'b', 9), ('q', 'c', 5)]) == {
        'total': 3, 'drift': {'p': 7, 'q': 0}, 'risen': ['p'],
        'fallen': [], 'volatile': 'p'}
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
        _raises(TypeError, P, m.trace_shifts, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (word, stage, score) triple',
                m.trace_shifts, [K(('a', 'b', 1))])
    _raises(ValueError, WM, m.trace_shifts, [(S('a'), 'b', 1)])
    _raises(ValueError, TM, m.trace_shifts, [('a', S('b'), 1)])
    _raises(ValueError, SM, m.trace_shifts, [('a', 'b', I(1))])
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
    ('type(word) is not str', 'not isinstance(word, str)'),
    ('type(stage) is not str', 'not isinstance(stage, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(word) <= 16', 'not 1 <= len(word) <= 17'),
    ('not 1 <= len(stage) <= 16', 'not 1 <= len(stage) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('        latest[word] = score', '        latest[word] = first[word]'),
    ('drift[word] = latest[word] - first[word]',
     'drift[word] = first[word] - latest[word]'),
    ('if drift[word] >= 3', 'if drift[word] >= 4'),
    ('if drift[word] <= -3', 'if drift[word] <= -4'),
    ('if volatile is None or abs(drift[word]) > abs(drift[volatile]):',
     'if volatile is None or abs(drift[word]) < abs(drift[volatile]):'),
    ("'risen': risen", "'risen': fallen"),
    ("'drift': drift", "'drift': first"),
    ("'total': len(rows)", "'total': len(drift)"),
    ('        word, stage, score = row',
     '        stage, word, score = row'),
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
    assert mod.trace_shifts([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.trace_shifts([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.trace_shifts([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

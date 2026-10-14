import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import deepfakes as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
FR = 'row 1: frame must be a string of 1 to 16 characters'
MO = 'row 1: model must be a string of 1 to 16 characters'
SC = 'row 1: score must be a nonbool integer between 1 and 9'


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
    assert section == ('face-swap fidelity, lip-sync accuracy, '
                       'detection evasion, consent compliance, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: debut-anchor counting over supplied rows'
    assert mod.NOT_CLAIMED == ('face-swap fidelity', 'lip-sync accuracy',
                               'detection evasion', 'consent compliance',
                               'production readiness')


def _expected(rows):
    firsts = {}
    anchors = {}
    supplied = {}
    for frame, model, score in rows:
        if model not in firsts:
            firsts[model] = score
            anchors[model] = 0
            supplied[model] = 0
        supplied[model] += 1
        if score == firsts[model]:
            anchors[model] += 1
    steady = sorted(m for m in anchors if anchors[m] == supplied[m])
    firmest = None
    for model in anchors:
        if firmest is None or anchors[model] > anchors[firmest]:
            firmest = model
    return {'total': len(rows), 'anchors': anchors,
            'steady': steady, 'firmest': firmest}


def _core(m):
    # fixed pins, oracle seeded with row number 1933
    assert m.anchor_counts([('f', 'm1', 5), ('f', 'm1', 2), ('f', 'm1', 5),
                            ('f', 'm2', 3), ('f', 'm2', 3)]) == {
        'total': 5, 'anchors': {'m1': 2, 'm2': 2},
        'steady': ['m2'], 'firmest': 'm1'}
    # a single row is its own anchor
    assert m.anchor_counts([('f', 'm', 7)]) == {
        'total': 1, 'anchors': {'m': 1}, 'steady': ['m'], 'firmest': 'm'}
    # a changed score breaks steadiness
    assert m.anchor_counts([('f', 'x', 4), ('f', 'x', 5)]) == {
        'total': 2, 'anchors': {'x': 1}, 'steady': [], 'firmest': 'x'}
    # a repeated debut holds steady
    assert m.anchor_counts([('f', 'x', 4), ('f', 'x', 4)])['steady'] == ['x']
    # non-contiguous returns to the debut still count
    assert m.anchor_counts([('f', 'x', 5), ('f', 'x', 1),
                            ('f', 'x', 1), ('f', 'x', 5)])['anchors'] == {'x': 2}
    # the firmest tie goes to the first supplied model
    r = m.anchor_counts([('f', 'Üser-9!', 9), ('f', 'q?7', 9)])
    assert r == {'total': 2, 'anchors': {'Üser-9!': 1, 'q?7': 1},
                 'steady': ['q?7', 'Üser-9!'], 'firmest': 'Üser-9!'}
    # dicts keep first-touch order
    r = m.anchor_counts([('z', 'b', 7), ('a', 'a', 2)])
    assert r['anchors'] == {'b': 1, 'a': 1}
    # a bigger anchor count beats an earlier steady single
    r = m.anchor_counts([('f', 'p', 1), ('f', 'q', 1), ('f', 'q', 1)])
    assert r['anchors'] == {'p': 1, 'q': 2}
    assert r['steady'] == ['p', 'q'] and r['firmest'] == 'q'
    # pre-seed pin: fresh accumulators only
    assert m.anchor_counts([('f', 'a', 1), ('f', 'a', 2),
                            ('f', 'b', 9), ('f', 'b', 9)]) == {
        'total': 4, 'anchors': {'a': 1, 'b': 2},
        'steady': ['b'], 'firmest': 'b'}
    rng = random.Random(1933)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.anchor_counts(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.anchor_counts, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.anchor_counts, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.anchor_counts, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.anchor_counts, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (frame, model, score) triple',
            m.anchor_counts, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.anchor_counts, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.anchor_counts, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, FR, m.anchor_counts, [(1, 'b', 1)])
    _raises(ValueError, FR, m.anchor_counts, [('', 'b', 1)])
    _raises(ValueError, FR, m.anchor_counts, [('x' * 17, 'b', 1)])
    _raises(ValueError, MO, m.anchor_counts, [('a', 1, 1)])
    _raises(ValueError, MO, m.anchor_counts, [('a', '', 1)])
    _raises(ValueError, MO, m.anchor_counts, [('a', 'x' * 17, 1)])
    _raises(ValueError, SC, m.anchor_counts, [('a', 'b', '1')])
    _raises(ValueError, SC, m.anchor_counts, [('a', 'b', 0)])
    _raises(ValueError, SC, m.anchor_counts, [('a', 'b', 10)])
    _raises(ValueError, SC, m.anchor_counts, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: frame must be a string of 1 to 16 characters',
            m.anchor_counts, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.anchor_counts, [('a', 'b', 1), ('c', 'd', 0)])
    # frame is validated before model, model before score
    _raises(ValueError, FR, m.anchor_counts, [('x' * 17, '', 0)])
    _raises(ValueError, MO, m.anchor_counts, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.anchor_counts, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.anchor_counts((('a', 'b', 1),)) == m.anchor_counts([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.anchor_counts([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.anchor_counts([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.anchor_counts([('a', 'b', 1)] * 60)['total'] == 60
    assert m.anchor_counts([('a', 'b', 9)])['anchors'] == {'b': 1}
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
        _raises(TypeError, P, m.anchor_counts, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (frame, model, score) triple',
                m.anchor_counts, [K(('a', 'b', 1))])
    _raises(ValueError, FR, m.anchor_counts, [(S('a'), 'b', 1)])
    _raises(ValueError, MO, m.anchor_counts, [('a', S('b'), 1)])
    _raises(ValueError, SC, m.anchor_counts, [('a', 'b', I(1))])
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
    ('type(frame) is not str', 'not isinstance(frame, str)'),
    ('type(model) is not str', 'not isinstance(model, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(frame) <= 16', 'not 1 <= len(frame) <= 17'),
    ('not 1 <= len(model) <= 16', 'not 1 <= len(model) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('            firsts[model] = score', '            firsts[model] = 1'),
    ('            anchors[model] = 0', '            anchors[model] = 1'),
    ('        supplied[model] += 1', '        supplied[model] += 2'),
    ('        if score == firsts[model]:', '        if score != firsts[model]:'),
    ('anchors[m] == supplied[m]', 'anchors[m] != supplied[m]'),
    ('if firmest is None or anchors[model] > anchors[firmest]:',
     'if firmest is None or anchors[model] < anchors[firmest]:'),
    ("'anchors': anchors", "'anchors': {}"),
    ("'steady': steady", "'steady': []"),
    ("'firmest': firmest", "'firmest': None"),
    ("'total': len(rows)", "'total': len(anchors)"),
    ('        frame, model, score = row',
     '        model, frame, score = row'),
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
    assert mod.anchor_counts([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.anchor_counts([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.anchor_counts([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import vision_language_models as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
CP = 'row 1: caption must be a string of 1 to 16 characters'
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
    assert section == ('image encoding, tokenization, benchmark design, '
                       'safety filtering, production readiness.')
    assert mod.SCOPE == 'PARTIAL: solo counting over supplied scores'
    assert mod.NOT_CLAIMED == ('image encoding', 'tokenization',
                               'benchmark design', 'safety filtering',
                               'production readiness')


def _expected(rows):
    best = {}
    holders = {}
    for caption, model, score in rows:
        if caption not in best or score > best[caption]:
            best[caption] = score
            holders[caption] = {model: True}
        elif score == best[caption]:
            holders[caption][model] = True
    wins = {}
    tied = []
    for caption in holders:
        if len(holders[caption]) == 1:
            for model in holders[caption]:
                if model not in wins:
                    wins[model] = 0
                wins[model] += 1
        else:
            tied.append(caption)
    if wins:
        top = max(wins.values())
        order = list(dict.fromkeys(model for _, model, _ in rows))
        leader = next(m for m in order if wins.get(m) == top)
    else:
        leader = None
    return {'total': len(rows), 'wins': wins,
            'tied': sorted(tied), 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1926
    assert m.count_solos([('c1', 'm1', 9), ('c1', 'm2', 5),
                          ('c2', 'm2', 8), ('c2', 'm1', 8)]) == {
        'total': 4, 'wins': {'m1': 1}, 'tied': ['c2'], 'leader': 'm1'}
    # a lone row is a solo win
    assert m.count_solos([('c', 'm', 5)]) == {
        'total': 1, 'wins': {'m': 1}, 'tied': [], 'leader': 'm'}
    # a shared best ties the caption and wins nobody anything
    assert m.count_solos([('c', 'a', 9), ('c', 'b', 9)]) == {
        'total': 2, 'wins': {}, 'tied': ['c'], 'leader': None}
    # repeat rows by one model are still a solo
    assert m.count_solos([('c', 'a', 1), ('c', 'a', 2)]) == {
        'total': 2, 'wins': {'a': 1}, 'tied': [], 'leader': 'a'}
    # the leader tie goes to the model supplied first
    r = m.count_solos([('z', 'b', 1), ('a', 'a', 2)])
    assert r['wins'] == {'b': 1, 'a': 1} and r['leader'] == 'b'
    # auditor-21 witness: first supplied, not first winning
    assert m.count_solos([('c1', 'A', 1), ('c2', 'A', 9),
                          ('c1', 'B', 9)]) == {
        'total': 3, 'wins': {'B': 1, 'A': 1}, 'tied': [], 'leader': 'A'}
    # first supplied beats alphabetical on leader ties
    assert m.count_solos([('c1', 'm2', 9), ('c2', 'm1', 9)]) == {
        'total': 2, 'wins': {'m2': 1, 'm1': 1}, 'tied': [], 'leader': 'm2'}
    # non-ASCII models follow the same rule
    r = m.count_solos([('c', 'Üser-9!', 9), ('c', 'q?7', 8), ('d', 'q?7', 9)])
    assert r == {'total': 3, 'wins': {'Üser-9!': 1, 'q?7': 1},
                 'tied': [], 'leader': 'Üser-9!'}
    # a new best erases earlier holders
    r = m.count_solos([('c', 'a', 5), ('c', 'b', 5), ('c', 'c', 9)])
    assert r == {'total': 3, 'wins': {'c': 1}, 'tied': [], 'leader': 'c'}
    # pre-seed pin: fresh accumulators only
    assert m.count_solos([('p', 'a', 5), ('p', 'b', 5),
                          ('q', 'a', 9), ('r', 'b', 7)]) == {
        'total': 4, 'wins': {'a': 1, 'b': 1}, 'tied': ['p'], 'leader': 'a'}
    rng = random.Random(1926)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_solos(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_solos, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_solos, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_solos, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_solos, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (caption, model, score) triple',
            m.count_solos, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_solos, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_solos, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, CP, m.count_solos, [(1, 'b', 1)])
    _raises(ValueError, CP, m.count_solos, [('', 'b', 1)])
    _raises(ValueError, CP, m.count_solos, [('x' * 17, 'b', 1)])
    _raises(ValueError, MO, m.count_solos, [('a', 1, 1)])
    _raises(ValueError, MO, m.count_solos, [('a', '', 1)])
    _raises(ValueError, MO, m.count_solos, [('a', 'x' * 17, 1)])
    _raises(ValueError, SC, m.count_solos, [('a', 'b', '1')])
    _raises(ValueError, SC, m.count_solos, [('a', 'b', 0)])
    _raises(ValueError, SC, m.count_solos, [('a', 'b', 10)])
    _raises(ValueError, SC, m.count_solos, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: caption must be a string of 1 to 16 characters',
            m.count_solos, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.count_solos, [('a', 'b', 1), ('c', 'd', 0)])
    # caption is validated before model, model before score
    _raises(ValueError, CP, m.count_solos, [('x' * 17, '', 0)])
    _raises(ValueError, MO, m.count_solos, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_solos, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_solos((('a', 'b', 1),)) == m.count_solos([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_solos([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_solos([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_solos([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_solos([('a', 'b', 9)])['wins'] == {'b': 1}
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
        _raises(TypeError, P, m.count_solos, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (caption, model, score) triple',
                m.count_solos, [K(('a', 'b', 1))])
    _raises(ValueError, CP, m.count_solos, [(S('a'), 'b', 1)])
    _raises(ValueError, MO, m.count_solos, [('a', S('b'), 1)])
    _raises(ValueError, SC, m.count_solos, [('a', 'b', I(1))])
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
    ('type(caption) is not str', 'not isinstance(caption, str)'),
    ('type(model) is not str', 'not isinstance(model, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(caption) <= 16', 'not 1 <= len(caption) <= 17'),
    ('not 1 <= len(model) <= 16', 'not 1 <= len(model) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('if caption not in best or score > best[caption]:',
     'if caption not in best or score < best[caption]:'),
    ('            holders[caption] = {model: True}',
     '            holders[caption][model] = True'),
    ('        elif score == best[caption]:', '        elif score != best[caption]:'),
    ('        if len(holders[caption]) == 1:', '        if len(holders[caption]) == 2:'),
    ('                wins[model] += 1', '                wins[model] += 2'),
    ('if leader is None or wins[model] > wins[leader]:',
     'if leader is None or wins[model] < wins[leader]:'),
    ('for model in order:', 'for model in wins:'),
    ('for model in order:', 'for model in sorted(order):'),
    ('if model not in order:', 'if model in order:'),
    ('        if model not in wins:\n            continue',
     '        if model in wins:\n            continue'),
    ("'wins': wins", "'wins': {}"),
    ("'tied': sorted(tied)", "'tied': []"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(wins)"),
    ('        caption, model, score = row',
     '        model, caption, score = row'),
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
    assert mod.count_solos([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.count_solos([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.count_solos([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ai_safety as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
HA = 'row 1: hazard must be a string of 1 to 16 characters'
GU = 'row 1: guard must be a string of 1 to 16 characters'
LE = 'row 1: level must be a nonbool integer between 1 and 9'


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
    assert section == ('hazard modeling, containment design, '
                       'monitoring infrastructure, incident response, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: inversion counting over supplied levels'
    assert mod.NOT_CLAIMED == ('hazard modeling', 'containment design',
                               'monitoring infrastructure',
                               'incident response', 'production readiness')


def _expected(rows):
    seqs = {}
    for hazard, guard, level in rows:
        seqs.setdefault(guard, []).append(level)
    inversions = {}
    for guard, seq in seqs.items():
        count = sum(1 for i in range(len(seq)) for j in range(i + 1, len(seq))
                    if seq[i] > seq[j])
        if count:
            inversions[guard] = count
    leader = None
    if inversions:
        top = max(inversions.values())
        order = list(dict.fromkeys(guard for _, guard, _ in rows))
        leader = next(g for g in order if inversions.get(g) == top)
    return {'total': len(rows), 'inversions': inversions,
            'pairs': sum(inversions.values()), 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1947
    assert m.count_inversions([('h', 'a', 3), ('h', 'a', 1),
                               ('h', 'a', 2)]) == {
        'total': 3, 'inversions': {'a': 2}, 'pairs': 2, 'leader': 'a'}
    # one row accepted with full expected output
    assert m.count_inversions([('h', 'g', 5)]) == {
        'total': 1, 'inversions': {}, 'pairs': 0, 'leader': None}
    # ascending levels invert nothing
    assert m.count_inversions([('h', 'a', 1), ('h', 'a', 2),
                               ('h', 'a', 3)]) == {
        'total': 3, 'inversions': {}, 'pairs': 0, 'leader': None}
    # equal levels are not inversions
    assert m.count_inversions([('h', 'a', 5), ('h', 'a', 5)]) == {
        'total': 2, 'inversions': {}, 'pairs': 0, 'leader': None}
    # a full descent inverts every pair
    assert m.count_inversions([('h', 'a', 3), ('h', 'a', 2),
                               ('h', 'a', 1)]) == {
        'total': 3, 'inversions': {'a': 3}, 'pairs': 3, 'leader': 'a'}
    # inversions are counted within each guard only
    assert m.count_inversions([('h', 'a', 9), ('h', 'b', 1),
                               ('h', 'b', 2), ('h', 'a', 1)]) == {
        'total': 4, 'inversions': {'a': 1}, 'pairs': 1, 'leader': 'a'}
    # a leader tie goes to the first supplied guard
    assert m.count_inversions([('h', 'b', 2), ('h', 'a', 9),
                               ('h', 'b', 1), ('h', 'a', 1)]) == {
        'total': 4, 'inversions': {'b': 1, 'a': 1}, 'pairs': 2, 'leader': 'b'}
    # non-ASCII guards follow the same rule
    assert m.count_inversions([('h', 'Üser-9!', 2), ('h', 'Üser-9!', 1),
                               ('h', 'q?7', 1)]) == {
        'total': 3, 'inversions': {'Üser-9!': 1}, 'pairs': 1,
        'leader': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.count_inversions([('h', 'm', 2), ('h', 'n', 5),
                               ('h', 'm', 1), ('h', 'n', 4)]) == {
        'total': 4, 'inversions': {'m': 1, 'n': 1}, 'pairs': 2, 'leader': 'm'}
    rng = random.Random(1947)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_inversions(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_inversions, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_inversions, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_inversions, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_inversions, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (hazard, guard, level) triple',
            m.count_inversions, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_inversions, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_inversions, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, HA, m.count_inversions, [(1, 'b', 1)])
    _raises(ValueError, HA, m.count_inversions, [('', 'b', 1)])
    _raises(ValueError, HA, m.count_inversions, [('x' * 17, 'b', 1)])
    _raises(ValueError, GU, m.count_inversions, [('a', 1, 1)])
    _raises(ValueError, GU, m.count_inversions, [('a', '', 1)])
    _raises(ValueError, GU, m.count_inversions, [('a', 'x' * 17, 1)])
    _raises(ValueError, LE, m.count_inversions, [('a', 'b', '1')])
    _raises(ValueError, LE, m.count_inversions, [('a', 'b', 0)])
    _raises(ValueError, LE, m.count_inversions, [('a', 'b', 10)])
    _raises(ValueError, LE, m.count_inversions, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: hazard must be a string of 1 to 16 characters',
            m.count_inversions, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: level must be a nonbool integer between 1 and 9',
            m.count_inversions, [('a', 'b', 1), ('c', 'd', 0)])
    # hazard is validated before guard, guard before level
    _raises(ValueError, HA, m.count_inversions, [('x' * 17, '', 0)])
    _raises(ValueError, GU, m.count_inversions, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_inversions, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_inversions((('a', 'b', 1),)) == m.count_inversions([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_inversions([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_inversions([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_inversions([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_inversions([('a', 'b', 9)])['pairs'] == 0
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_inversions([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_inversions([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_inversions([('a', 'b', 5),
                               ('x' * 16, 'y' * 16, 5)])['total'] == 2
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
        _raises(TypeError, P, m.count_inversions, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (hazard, guard, level) triple',
                m.count_inversions, [K(('a', 'b', 1))])
    _raises(ValueError, HA, m.count_inversions, [(S('a'), 'b', 1)])
    _raises(ValueError, GU, m.count_inversions, [('a', S('b'), 1)])
    _raises(ValueError, LE, m.count_inversions, [('a', 'b', I(1))])
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
    ('type(hazard) is not str', 'not isinstance(hazard, str)'),
    ('type(guard) is not str', 'not isinstance(guard, str)'),
    ('type(level) is not int', 'not isinstance(level, int)'),
    ('not 1 <= len(hazard) <= 16', 'not 1 <= len(hazard) <= 17'),
    ('not 1 <= len(guard) <= 16', 'not 1 <= len(guard) <= 17'),
    ('not 1 <= level <= 9', 'not 1 <= level <= 10'),
    ('if seq[i] > seq[j]:', 'if seq[i] >= seq[j]:'),
    ('if seq[i] > seq[j]:', 'if seq[i] < seq[j]:'),
    ('        if count:', '        if count > 1:'),
    ('for guard in order:', 'for guard in sorted(order):'),
    ("'inversions': inversions", "'inversions': {}"),
    ("'pairs': total", "'pairs': 0"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(seqs)"),
    ('        hazard, guard, level = row',
     '        guard, hazard, level = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True

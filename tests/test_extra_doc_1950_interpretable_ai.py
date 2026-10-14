import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import interpretable_ai as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
RU = 'row 1: rule must be a string of 1 to 16 characters'
MO = 'row 1: model must be a string of 1 to 16 characters'
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
    assert section == ('rule extraction, surrogate modeling, '
                       'distillation, glossary curation, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: slip counting over supplied gains'
    assert mod.NOT_CLAIMED == ('rule extraction', 'surrogate modeling',
                               'distillation', 'glossary curation',
                               'production readiness')


def _expected(rows):
    previous = {}
    slips = {}
    for rule, model, gain in rows:
        if rule in previous and gain < previous[rule]:
            slips[rule] = slips.get(rule, 0) + 1
        previous[rule] = gain
    leader = None
    if slips:
        top = max(slips.values())
        order = list(dict.fromkeys(rule for rule, _, _ in rows))
        leader = next(r for r in order if slips.get(r) == top)
    return {'total': len(rows), 'slips': slips,
            'count': sum(slips.values()), 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1950
    assert m.count_slips([('r', 'x', 5), ('r', 'x', 3), ('r', 'x', 3),
                          ('s', 'x', 9), ('r', 'x', 1)]) == {
        'total': 5, 'slips': {'r': 2}, 'count': 2, 'leader': 'r'}
    # one row accepted with full expected output
    assert m.count_slips([('r', 'm', 5)]) == {
        'total': 1, 'slips': {}, 'count': 0, 'leader': None}
    # an equal gain is not a slip
    assert m.count_slips([('r', 'm', 3), ('r', 'm', 3)]) == {
        'total': 2, 'slips': {}, 'count': 0, 'leader': None}
    # a rise is not a slip
    assert m.count_slips([('r', 'm', 3), ('r', 'm', 4)]) == {
        'total': 2, 'slips': {}, 'count': 0, 'leader': None}
    # slips are counted within each rule only
    assert m.count_slips([('r', 'x', 9), ('s', 'x', 1),
                          ('s', 'x', 2)]) == {
        'total': 3, 'slips': {}, 'count': 0, 'leader': None}
    # consecutive drops each count
    assert m.count_slips([('r', 'm', 9), ('r', 'm', 5),
                          ('r', 'm', 2)]) == {
        'total': 3, 'slips': {'r': 2}, 'count': 2, 'leader': 'r'}
    # a leader tie goes to the first supplied rule
    assert m.count_slips([('b', 'm', 2), ('a', 'm', 9),
                          ('b', 'm', 1), ('a', 'm', 1)]) == {
        'total': 4, 'slips': {'b': 1, 'a': 1}, 'count': 2, 'leader': 'b'}
    # non-ASCII rules follow the same rule
    assert m.count_slips([('Üser-9!', 'm', 2), ('Üser-9!', 'm', 1),
                          ('q?7', 'm', 5)]) == {
        'total': 3, 'slips': {'Üser-9!': 1}, 'count': 1,
        'leader': 'Üser-9!'}
    # the previous gain moves with every row
    assert m.count_slips([('r', 'm', 5), ('r', 'm', 4),
                          ('r', 'm', 4)]) == {
        'total': 3, 'slips': {'r': 1}, 'count': 1, 'leader': 'r'}
    # pre-seed pin: fresh accumulators only
    assert m.count_slips([('m', 'x', 3), ('n', 'x', 9),
                          ('m', 'x', 1), ('n', 'x', 2)]) == {
        'total': 4, 'slips': {'m': 1, 'n': 1}, 'count': 2, 'leader': 'm'}
    rng = random.Random(1950)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_slips(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_slips, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_slips, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_slips, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_slips, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (rule, model, gain) triple',
            m.count_slips, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_slips, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_slips, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, RU, m.count_slips, [(1, 'b', 1)])
    _raises(ValueError, RU, m.count_slips, [('', 'b', 1)])
    _raises(ValueError, RU, m.count_slips, [('x' * 17, 'b', 1)])
    _raises(ValueError, MO, m.count_slips, [('a', 1, 1)])
    _raises(ValueError, MO, m.count_slips, [('a', '', 1)])
    _raises(ValueError, MO, m.count_slips, [('a', 'x' * 17, 1)])
    _raises(ValueError, GA, m.count_slips, [('a', 'b', '1')])
    _raises(ValueError, GA, m.count_slips, [('a', 'b', 0)])
    _raises(ValueError, GA, m.count_slips, [('a', 'b', 10)])
    _raises(ValueError, GA, m.count_slips, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: rule must be a string of 1 to 16 characters',
            m.count_slips, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: gain must be a nonbool integer between 1 and 9',
            m.count_slips, [('a', 'b', 1), ('c', 'd', 0)])
    # rule is validated before model, model before gain
    _raises(ValueError, RU, m.count_slips, [('x' * 17, '', 0)])
    _raises(ValueError, MO, m.count_slips, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_slips, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_slips((('a', 'b', 1),)) == m.count_slips([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_slips([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_slips([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_slips([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_slips([('a', 'b', 9)])['slips'] == {}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_slips([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_slips([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_slips([('a', 'b', 5),
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
        _raises(TypeError, P, m.count_slips, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (rule, model, gain) triple',
                m.count_slips, [K(('a', 'b', 1))])
    _raises(ValueError, RU, m.count_slips, [(S('a'), 'b', 1)])
    _raises(ValueError, MO, m.count_slips, [('a', S('b'), 1)])
    _raises(ValueError, GA, m.count_slips, [('a', 'b', I(1))])
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
    ('type(rule) is not str', 'not isinstance(rule, str)'),
    ('type(model) is not str', 'not isinstance(model, str)'),
    ('type(gain) is not int', 'not isinstance(gain, int)'),
    ('not 1 <= len(rule) <= 16', 'not 1 <= len(rule) <= 17'),
    ('not 1 <= len(model) <= 16', 'not 1 <= len(model) <= 17'),
    ('not 1 <= gain <= 9', 'not 1 <= gain <= 10'),
    ('gain < previous[rule]', 'gain <= previous[rule]'),
    ('gain < previous[rule]', 'gain > previous[rule]'),
    ('        previous[rule] = gain', '        previous[rule] = 0'),
    ('slips[rule] += 1', 'slips[rule] += 2'),
    ('for rule in order:', 'for rule in sorted(order):'),
    ("'slips': slips", "'slips': {}"),
    ("'count': total", "'count': 0"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(slips)"),
    ('        rule, model, gain = row',
     '        model, rule, gain = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True

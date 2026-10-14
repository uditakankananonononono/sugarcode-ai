import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import explainable_ai as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
FE = 'row 1: feature must be a string of 1 to 16 characters'
MO = 'row 1: model must be a string of 1 to 16 characters'
WE = 'row 1: weight must be a nonbool integer between 1 and 9'


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
    assert section == ('feature extraction, saliency methods, '
                       'counterfactual generation, model debugging, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: top tracking over supplied weights'
    assert mod.NOT_CLAIMED == ('feature extraction', 'saliency methods',
                               'counterfactual generation', 'model debugging',
                               'production readiness')


def _expected(rows):
    sums = {}
    displacements = {}
    tops = {}
    for feature, model, weight in rows:
        inner = sums.setdefault(model, {})
        inner[feature] = inner.get(feature, 0) + weight
        high = max(inner.values())
        top = next(f for f in inner if inner[f] == high)
        if model in tops and tops[model] != top:
            displacements[model] = displacements.get(model, 0) + 1
        tops[model] = top
    leader = None
    if displacements:
        best = max(displacements.values())
        order = list(dict.fromkeys(model for _, model, _ in rows))
        leader = next(md for md in order if displacements.get(md) == best)
    return {'total': len(rows), 'displacements': displacements,
            'tops': tops, 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1949
    assert m.track_tops([('f1', 'm', 2), ('f2', 'm', 5),
                         ('f1', 'm', 9)]) == {
        'total': 3, 'displacements': {'m': 2}, 'tops': {'m': 'f1'},
        'leader': 'm'}
    # one row accepted with full expected output
    assert m.track_tops([('f', 'm', 5)]) == {
        'total': 1, 'displacements': {}, 'tops': {'m': 'f'}, 'leader': None}
    # an even split keeps the first supplied feature on top
    assert m.track_tops([('f1', 'm', 5), ('f2', 'm', 5)]) == {
        'total': 2, 'displacements': {}, 'tops': {'m': 'f1'}, 'leader': None}
    # the top can swing back and forth
    assert m.track_tops([('f2', 'm', 1), ('f1', 'm', 5),
                         ('f2', 'm', 5)]) == {
        'total': 3, 'displacements': {'m': 2}, 'tops': {'m': 'f2'},
        'leader': 'm'}
    # an even split on a later row still favors the earlier feature
    assert m.track_tops([('f2', 'm', 3), ('f1', 'm', 3)]) == {
        'total': 2, 'displacements': {}, 'tops': {'m': 'f2'}, 'leader': None}
    # displacements are counted within each model only
    assert m.track_tops([('f', 'a', 1), ('f', 'b', 9),
                         ('g', 'a', 2)]) == {
        'total': 3, 'displacements': {'a': 1},
        'tops': {'a': 'g', 'b': 'f'}, 'leader': 'a'}
    # a leader tie goes to the first supplied model
    assert m.track_tops([('f', 'b', 1), ('f', 'a', 1),
                         ('g', 'b', 9), ('g', 'a', 9)]) == {
        'total': 4, 'displacements': {'b': 1, 'a': 1},
        'tops': {'b': 'g', 'a': 'g'}, 'leader': 'b'}
    # non-ASCII models follow the same rule
    assert m.track_tops([('f', 'Üser-9!', 1), ('g', 'Üser-9!', 9),
                         ('f', 'q?7', 2)]) == {
        'total': 3, 'displacements': {'Üser-9!': 1},
        'tops': {'Üser-9!': 'g', 'q?7': 'f'}, 'leader': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.track_tops([('x', 'm', 1), ('y', 'n', 1),
                         ('y', 'm', 9), ('z', 'n', 2)]) == {
        'total': 4, 'displacements': {'m': 1, 'n': 1},
        'tops': {'m': 'y', 'n': 'z'}, 'leader': 'm'}
    rng = random.Random(1949)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.track_tops(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.track_tops, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.track_tops, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_tops, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_tops, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (feature, model, weight) triple',
            m.track_tops, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.track_tops, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.track_tops, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, FE, m.track_tops, [(1, 'b', 1)])
    _raises(ValueError, FE, m.track_tops, [('', 'b', 1)])
    _raises(ValueError, FE, m.track_tops, [('x' * 17, 'b', 1)])
    _raises(ValueError, MO, m.track_tops, [('a', 1, 1)])
    _raises(ValueError, MO, m.track_tops, [('a', '', 1)])
    _raises(ValueError, MO, m.track_tops, [('a', 'x' * 17, 1)])
    _raises(ValueError, WE, m.track_tops, [('a', 'b', '1')])
    _raises(ValueError, WE, m.track_tops, [('a', 'b', 0)])
    _raises(ValueError, WE, m.track_tops, [('a', 'b', 10)])
    _raises(ValueError, WE, m.track_tops, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: feature must be a string of 1 to 16 characters',
            m.track_tops, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: weight must be a nonbool integer between 1 and 9',
            m.track_tops, [('a', 'b', 1), ('c', 'd', 0)])
    # feature is validated before model, model before weight
    _raises(ValueError, FE, m.track_tops, [('x' * 17, '', 0)])
    _raises(ValueError, MO, m.track_tops, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.track_tops, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.track_tops((('a', 'b', 1),)) == m.track_tops([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.track_tops([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.track_tops([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.track_tops([('a', 'b', 1)] * 60)['total'] == 60
    assert m.track_tops([('a', 'b', 9)])['tops'] == {'b': 'a'}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.track_tops([('x' * 16, 'b', 5)])['total'] == 1
    assert m.track_tops([('a', 'y' * 16, 5)])['total'] == 1
    assert m.track_tops([('a', 'b', 5),
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
        _raises(TypeError, P, m.track_tops, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (feature, model, weight) triple',
                m.track_tops, [K(('a', 'b', 1))])
    _raises(ValueError, FE, m.track_tops, [(S('a'), 'b', 1)])
    _raises(ValueError, MO, m.track_tops, [('a', S('b'), 1)])
    _raises(ValueError, WE, m.track_tops, [('a', 'b', I(1))])
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
    ('type(feature) is not str', 'not isinstance(feature, str)'),
    ('type(model) is not str', 'not isinstance(model, str)'),
    ('type(weight) is not int', 'not isinstance(weight, int)'),
    ('not 1 <= len(feature) <= 16', 'not 1 <= len(feature) <= 17'),
    ('not 1 <= len(model) <= 16', 'not 1 <= len(model) <= 17'),
    ('not 1 <= weight <= 9', 'not 1 <= weight <= 10'),
    ('sums[model][name] > sums[model][top]',
     'sums[model][name] >= sums[model][top]'),
    ('if model in tops and tops[model] != top:',
     'if model in tops and tops[model] == top:'),
    ('sums[model][feature] += weight', 'sums[model][feature] = weight'),
    ('displacements[model] += 1', 'displacements[model] += 2'),
    ('for model in order:', 'for model in sorted(order):'),
    ("'tops': tops", "'tops': {}"),
    ("'displacements': displacements", "'displacements': {}"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(sums)"),
    ('        feature, model, weight = row',
     '        model, feature, weight = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True

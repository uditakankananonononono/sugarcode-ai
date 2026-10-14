import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import (
    reinforcement_learning_from_human_feedback as mod)

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PR = 'row 1: prompt must be a string of 1 to 16 characters'
LA = 'row 1: labeler must be a string of 1 to 16 characters'
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
    assert section == ('reward model training, policy optimization, '
                       'kl regularization, human rater screening, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: weighting over supplied scores'
    assert mod.NOT_CLAIMED == ('reward model training', 'policy optimization',
                               'kl regularization', 'human rater screening',
                               'production readiness')


def _expected(rows):
    counts = {}
    weighted = {}
    for prompt, labeler, score in rows:
        counts[labeler] = counts.get(labeler, 0) + 1
        weighted[labeler] = weighted.get(labeler, 0) + score * counts[labeler]
    order = list(dict.fromkeys(labeler for _, labeler, _ in rows))
    top = max(weighted.values())
    leader = next(l for l in order if weighted[l] == top)
    return {'total': len(rows), 'weighted': weighted,
            'weight': sum(weighted.values()), 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1944
    assert m.weight_feedback([('p', 'x', 2), ('p', 'y', 9),
                              ('p', 'x', 3)]) == {
        'total': 3, 'weighted': {'x': 8, 'y': 9}, 'weight': 17, 'leader': 'y'}
    # one row accepted with full expected output
    assert m.weight_feedback([('p', 'x', 5)]) == {
        'total': 1, 'weighted': {'x': 5}, 'weight': 5, 'leader': 'x'}
    # later rows of one labeler weigh more
    assert m.weight_feedback([('p', 'x', 1), ('p', 'x', 1),
                              ('p', 'x', 1)]) == {
        'total': 3, 'weighted': {'x': 6}, 'weight': 6, 'leader': 'x'}
    # a leader tie goes to the first supplied labeler
    assert m.weight_feedback([('p', 'b', 4), ('p', 'a', 4)]) == {
        'total': 2, 'weighted': {'b': 4, 'a': 4}, 'weight': 8, 'leader': 'b'}
    # position can outweigh the single highest score
    assert m.weight_feedback([('p', 'x', 9), ('p', 'y', 1),
                              ('p', 'y', 9)]) == {
        'total': 3, 'weighted': {'x': 9, 'y': 19}, 'weight': 28, 'leader': 'y'}
    # non-ASCII labelers follow the same rule
    assert m.weight_feedback([('p', 'Üser-9!', 3), ('p', 'q?7', 3)]) == {
        'total': 2, 'weighted': {'Üser-9!': 3, 'q?7': 3},
        'weight': 6, 'leader': 'Üser-9!'}
    # dicts keep first-touch order
    r = m.weight_feedback([('p', 'z', 1), ('p', 'a', 1)])
    assert r['weighted'] == {'z': 1, 'a': 1} and r['leader'] == 'z'
    # pre-seed pin: fresh accumulators only
    assert m.weight_feedback([('p', 'm', 2), ('p', 'n', 3),
                              ('p', 'm', 4)]) == {
        'total': 3, 'weighted': {'m': 10, 'n': 3}, 'weight': 13, 'leader': 'm'}
    rng = random.Random(1944)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.weight_feedback(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.weight_feedback, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.weight_feedback, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weight_feedback, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weight_feedback, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (prompt, labeler, score) triple',
            m.weight_feedback, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.weight_feedback, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.weight_feedback, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PR, m.weight_feedback, [(1, 'b', 1)])
    _raises(ValueError, PR, m.weight_feedback, [('', 'b', 1)])
    _raises(ValueError, PR, m.weight_feedback, [('x' * 17, 'b', 1)])
    _raises(ValueError, LA, m.weight_feedback, [('a', 1, 1)])
    _raises(ValueError, LA, m.weight_feedback, [('a', '', 1)])
    _raises(ValueError, LA, m.weight_feedback, [('a', 'x' * 17, 1)])
    _raises(ValueError, SC, m.weight_feedback, [('a', 'b', '1')])
    _raises(ValueError, SC, m.weight_feedback, [('a', 'b', 0)])
    _raises(ValueError, SC, m.weight_feedback, [('a', 'b', 10)])
    _raises(ValueError, SC, m.weight_feedback, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: prompt must be a string of 1 to 16 characters',
            m.weight_feedback, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.weight_feedback, [('a', 'b', 1), ('c', 'd', 0)])
    # prompt is validated before labeler, labeler before score
    _raises(ValueError, PR, m.weight_feedback, [('x' * 17, '', 0)])
    _raises(ValueError, LA, m.weight_feedback, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.weight_feedback, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.weight_feedback((('a', 'b', 1),)) == m.weight_feedback([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.weight_feedback([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.weight_feedback([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.weight_feedback([('a', 'b', 1)] * 60)['total'] == 60
    assert m.weight_feedback([('a', 'b', 9)])['weight'] == 9
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.weight_feedback([('x' * 16, 'b', 5)])['total'] == 1
    assert m.weight_feedback([('a', 'y' * 16, 5)])['total'] == 1
    assert m.weight_feedback([('a', 'b', 5),
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
        _raises(TypeError, P, m.weight_feedback, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (prompt, labeler, score) triple',
                m.weight_feedback, [K(('a', 'b', 1))])
    _raises(ValueError, PR, m.weight_feedback, [(S('a'), 'b', 1)])
    _raises(ValueError, LA, m.weight_feedback, [('a', S('b'), 1)])
    _raises(ValueError, SC, m.weight_feedback, [('a', 'b', I(1))])
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
    ('type(prompt) is not str', 'not isinstance(prompt, str)'),
    ('type(labeler) is not str', 'not isinstance(labeler, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(prompt) <= 16', 'not 1 <= len(prompt) <= 17'),
    ('not 1 <= len(labeler) <= 16', 'not 1 <= len(labeler) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('weighted[labeler] += score * seen[labeler]',
     'weighted[labeler] += score'),
    ('seen[labeler] += 1', 'seen[labeler] += 2'),
    ('for labeler in order:', 'for labeler in sorted(order):'),
    ('weighted[labeler] > weighted[leader]',
     'weighted[labeler] >= weighted[leader]'),
    ("'weighted': weighted", "'weighted': {}"),
    ("'weight': sum(weighted.values())", "'weight': 0"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(weighted)"),
    ('        prompt, labeler, score = row',
     '        labeler, prompt, score = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True

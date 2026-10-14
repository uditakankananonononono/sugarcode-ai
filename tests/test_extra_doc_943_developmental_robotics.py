"""Mutation and oracle tests for extra_doc.developmental_robotics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_943_developmental_robotics.py',
                        'src/sugarcode/extra_doc/developmental_robotics.py')

with open(SRC_PATH) as _f:
    SRC = _f.read()


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def _load_code(code):
    module = types.ModuleType('mutant')
    exec(compile(code, 'mutant', 'exec'), module.__dict__)
    return module


class LyingI:
    def __index__(self):
        return 1


class ListSub(list):
    pass


def _core(module):
    m = module
    # oracle seeded with row number 943
    assert m.develop([]) == {'total': 0, 'advanced': 0, 'review': 0,
                             'skipped': 0, 'stage': {}, 'graduated': []}
    r = m.develop([('a', 1), ('a', 1), ('a', 3), ('a', 2)])
    assert r == {'total': 4, 'advanced': 2, 'review': 1, 'skipped': 1,
                 'stage': {'a': 2}, 'graduated': []}
    # in-order advances graduate
    r = m.develop([('a', 1), ('a', 2), ('a', 3), ('a', 4)])
    assert r['stage'] == {'a': 4} and r['graduated'] == ['a']
    assert r['advanced'] == 4
    # skipping ahead changes nothing
    r = m.develop([('a', 1), ('a', 3)])
    assert r == {'total': 2, 'advanced': 1, 'review': 0, 'skipped': 1,
                 'stage': {'a': 1}, 'graduated': []}
    # a repeat at the current stage is review, not skipped
    r = m.develop([('a', 1), ('a', 1)])
    assert r['review'] == 1 and r['skipped'] == 0 and r['stage'] == {'a': 1}
    # stage 0 from the start is review; the learner is reported at stage 0
    r = m.develop([('a', 0)])
    assert r['review'] == 1 and r['stage'] == {'a': 0} and r['graduated'] == []
    # two learners: only the fully advanced one graduates
    rows = [('a', 1), ('b', 1), ('a', 2), ('b', 2), ('a', 3), ('a', 4)]
    r = m.develop(rows)
    assert r['stage'] == {'a': 4, 'b': 2}
    assert r['graduated'] == ['a']
    # dynamic equal-string witness: equal names fold into one entry
    dyn = ''.join(['l', '1'])
    r = m.develop([(dyn, 1), (''.join(['l', '1']), 2)])
    assert r['stage'] == {'l1': 2} and r['advanced'] == 2
    # wide many-name graduation sort pin (20 names x 4 stages = 80 rows)
    names = ['lrn%02d' % i for i in range(20)]
    rows = [(n, s) for s in (1, 2, 3, 4) for n in names]
    r = m.develop(rows)
    assert r['graduated'] == sorted(names)
    assert r['advanced'] == 80 and r['total'] == 80
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.develop('nope')
    with pytest.raises(TypeError):
        m.develop(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.develop([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.develop([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.develop([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.develop([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.develop([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.develop([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.develop([('a', '1')])
    with pytest.raises(TypeError):
        m.develop([('a', LyingI())])
    with pytest.raises(TypeError):
        m.develop([('a', True)])
    with pytest.raises(ValueError, match='0-4'):
        m.develop([('a', 5)])
    with pytest.raises(ValueError, match='0-4'):
        m.develop([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.develop([('ok', 1), ('ok', 2), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.develop([('ok', 1), ('ok', 9)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.develop({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.develop(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.develop([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.develop((('a', 1),)) == m.develop([('a', 1)])
    # boundary acceptance pins
    assert m.develop([('abcdefgh', 1)])['advanced'] == 1
    assert m.develop([('a', 1)] * 100)['total'] == 100
    assert m.develop([('a', 0)])['review'] == 1
    assert m.develop([('a', 1), ('a', 2), ('a', 3), ('a', 4)])['graduated'] == ['a']
    # default-start pin: unknown learner must start at stage 0
    r = m.develop([('zz', 1)])
    assert r['stage'] == {'zz': 1} and r['advanced'] == 1
    r = m.develop([('zz', 2)])
    assert r['skipped'] == 1 and r['stage'] == {'zz': 0}
    return True


def battery(module):
    _core(module)
    _late(module)
    return True


def _survives(old, new):
    assert SRC.count(old) >= 1, f'needle missing: {old!r}'
    mutant = SRC.replace(old, new, 1)
    try:
        compile(mutant, 'mutant', 'exec')
    except SyntaxError:
        return 'syntax'
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(5)
    try:
        module = _load_code(mutant)
        battery(module)
    except (Exception, pytest.fail.Exception):
        return 'dies'
    except BaseException:
        return 'dies'
    finally:
        signal.alarm(0)
    return 'survives'


MUTANTS = [
    ('if stage == current + 1:', 'if stage >= current + 1:'),
    ('if stage == current + 1:', 'if stage == current + 2:'),
    ('if stage == current + 1:', 'if stage == current:'),
    ('elif stage <= current:', 'elif stage < current:'),
    ('elif stage <= current:', 'elif stage >= current:'),
    ('advanced += 1', 'advanced += 2'),
    ('review += 1', 'review += 2'),
    ('skipped += 1', 'skipped += 2'),
    ('skipped += 1', 'skipped += 0'),
    ('stages[learner] = stage', 'stages[learner] = stage + 1'),
    ('stages[learner] = stage', 'stages[learner] = current'),
    ('stages.setdefault(learner, MIN_STAGE)', 'stages.setdefault(learner, 1)'),
    ('stages.setdefault(learner, MIN_STAGE)', 'stages.setdefault(learner, MAX_STAGE)'),
    ('MIN_STAGE = 0', 'MIN_STAGE = 1'),
    ('MAX_STAGE = 4', 'MAX_STAGE = 5'),
    ('MAX_STAGE = 4', 'MAX_STAGE = 3'),
    ('stage == MAX_STAGE', 'stage == MAX_STAGE - 1'),
    ("'total': len(rows)", "'total': len(stages)"),
    ('learner, stage = row', 'stage, learner = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(learner) <= MAX_NAME', 'not 1 <= len(learner) < MAX_NAME'),
    ('not MIN_STAGE <= stage <= MAX_STAGE', 'not MIN_STAGE < stage < MAX_STAGE'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('advanced = 0\n    review = 0', 'advanced = 1\n    review = 0'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 943, Developmental Robotics' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True

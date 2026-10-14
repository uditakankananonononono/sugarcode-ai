import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import trustworthy_ai as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SY = 'row 1: system must be a string of 1 to 16 characters'
TR = 'row 1: trial must be a string of 1 to 16 characters'
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
    assert section == ('trial design, score calibration, red-teaming, '
                       'certification, production readiness.')
    assert mod.SCOPE == 'PARTIAL: silver counting over supplied scores'
    assert mod.NOT_CLAIMED == ('trial design', 'score calibration',
                               'red-teaming', 'certification',
                               'production readiness')


def _expected(rows):
    per_trial = {}
    for system, trial, score in rows:
        holders = per_trial.setdefault(trial, {})
        holders[system] = max(score, holders.get(system, 0))
    silvers = {}
    outright = 0
    for trial, holders in per_trial.items():
        top = max(holders.values())
        if list(holders.values()).count(top) == 1:
            outright += 1
        below = {s: v for s, v in holders.items() if v < top}
        if below:
            mark = max(below.values())
            for s, v in below.items():
                if v == mark:
                    silvers[s] = silvers.get(s, 0) + 1
    leader = None
    if silvers:
        most = max(silvers.values())
        supply = list(dict.fromkeys(s for s, _t, _v in rows))
        leader = next(s for s in supply if silvers.get(s) == most)
    return {'total': len(rows), 'silvers': silvers,
            'count': sum(silvers.values()), 'outright': outright,
            'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1953
    assert m.count_silvers([('s1', 't1', 9), ('s2', 't1', 5),
                            ('s1', 't2', 5), ('s2', 't2', 9),
                            ('s3', 't2', 9)]) == {
        'total': 5, 'silvers': {'s2': 1, 's1': 1}, 'count': 2,
        'outright': 1, 'leader': 's1'}
    # one row accepted with full expected output
    assert m.count_silvers([('s', 't', 5)]) == {
        'total': 1, 'silvers': {}, 'count': 0, 'outright': 1,
        'leader': None}
    # a trial tied at the top has no silver and is not outright
    assert m.count_silvers([('a', 't', 7), ('b', 't', 7)]) == {
        'total': 2, 'silvers': {}, 'count': 0, 'outright': 0,
        'leader': None}
    # a re-scored system keeps its trial peak
    assert m.count_silvers([('s', 't', 3), ('s', 't', 9),
                            ('x', 't', 8)]) == {
        'total': 3, 'silvers': {'x': 1}, 'count': 1, 'outright': 1,
        'leader': 'x'}
    # the silver is the highest score below the top, no other
    assert m.count_silvers([('a', 't', 9), ('b', 't', 3),
                            ('c', 't', 5)]) == {
        'total': 3, 'silvers': {'c': 1}, 'count': 1, 'outright': 1,
        'leader': 'c'}
    # every system at the silver score is credited
    assert m.count_silvers([('a', 't', 9), ('b', 't', 5),
                            ('c', 't', 5)]) == {
        'total': 3, 'silvers': {'b': 1, 'c': 1}, 'count': 2,
        'outright': 1, 'leader': 'b'}
    # a tied top still leaves a silver below
    assert m.count_silvers([('a', 't', 9), ('b', 't', 9),
                            ('c', 't', 4)]) == {
        'total': 3, 'silvers': {'c': 1}, 'count': 1, 'outright': 0,
        'leader': 'c'}
    # non-ASCII systems follow the same rule
    assert m.count_silvers([('Üser-9!', 't', 4), ('q?7', 't', 8)]) == {
        'total': 2, 'silvers': {'Üser-9!': 1}, 'count': 1,
        'outright': 1, 'leader': 'Üser-9!'}
    # trials are independent, and a leader tie is first supplied
    assert m.count_silvers([('z', 't1', 9), ('a', 't1', 1),
                            ('z', 't2', 1), ('a', 't2', 9)]) == {
        'total': 4, 'silvers': {'a': 1, 'z': 1}, 'count': 2,
        'outright': 2, 'leader': 'z'}
    # pre-seed pin: fresh accumulators only
    assert m.count_silvers([('x', 't1', 9), ('y', 't1', 3),
                            ('y', 't2', 8), ('x', 't2', 4)]) == {
        'total': 4, 'silvers': {'y': 1, 'x': 1}, 'count': 2,
        'outright': 2, 'leader': 'x'}
    rng = random.Random(1953)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_silvers(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_silvers, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_silvers, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_silvers, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_silvers, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (system, trial, score) triple',
            m.count_silvers, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_silvers, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_silvers, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SY, m.count_silvers, [(1, 'b', 1)])
    _raises(ValueError, SY, m.count_silvers, [('', 'b', 1)])
    _raises(ValueError, SY, m.count_silvers, [('x' * 17, 'b', 1)])
    _raises(ValueError, TR, m.count_silvers, [('a', 1, 1)])
    _raises(ValueError, TR, m.count_silvers, [('a', '', 1)])
    _raises(ValueError, TR, m.count_silvers, [('a', 'x' * 17, 1)])
    _raises(ValueError, SC, m.count_silvers, [('a', 'b', '1')])
    _raises(ValueError, SC, m.count_silvers, [('a', 'b', 0)])
    _raises(ValueError, SC, m.count_silvers, [('a', 'b', 10)])
    _raises(ValueError, SC, m.count_silvers, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: system must be a string of 1 to 16 characters',
            m.count_silvers, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.count_silvers, [('a', 'b', 1), ('c', 'd', 0)])
    # system is validated before trial, trial before score
    _raises(ValueError, SY, m.count_silvers, [('x' * 17, '', 0)])
    _raises(ValueError, TR, m.count_silvers, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_silvers,
            {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_silvers((('a', 'b', 1),)) == m.count_silvers([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_silvers([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_silvers([['a', 'x', 2], ('b', 'y', 1),
                                     ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_silvers([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_silvers([('a', 'b', 9)])['silvers'] == {}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_silvers([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_silvers([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_silvers([('a', 'b', 5),
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
        _raises(TypeError, P, m.count_silvers, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (system, trial, score) triple',
                m.count_silvers, [K(('a', 'b', 1))])
    _raises(ValueError, SY, m.count_silvers, [(S('a'), 'b', 1)])
    _raises(ValueError, TR, m.count_silvers, [('a', S('b'), 1)])
    _raises(ValueError, SC, m.count_silvers, [('a', 'b', I(1))])
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
    ('type(system) is not str', 'not isinstance(system, str)'),
    ('type(trial) is not str', 'not isinstance(trial, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(system) <= 16', 'not 1 <= len(system) <= 17'),
    ('not 1 <= len(trial) <= 16', 'not 1 <= len(trial) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('score > per_trial[trial][system]', 'score < per_trial[trial][system]'),
    ('tops == 1', 'tops != 1'),
    ('silver = max(rest)', 'silver = min(rest)'),
    ('if holders[system] == silver:', 'if holders[system] != silver:'),
    ('if rest:', 'if not rest:'),
    ('silvers[system] += 1', 'silvers[system] += 2'),
    ('total += 1', 'total += 2'),
    ('outright += 1', 'outright += 2'),
    ('for system in order:', 'for system in sorted(order):'),
    ("'silvers': silvers", "'silvers': {}"),
    ("'count': total", "'count': 0"),
    ("'outright': outright", "'outright': 0"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(silvers)"),
    ('        system, trial, score = row',
     '        trial, system, score = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True

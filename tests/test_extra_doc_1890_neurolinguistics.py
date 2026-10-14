import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import neurolinguistics as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
RM = 'row 1: region must be a string of 1 to 16 characters'
TM = 'row 1: task must be a string of 1 to 16 characters'
SM = 'row 1: signal must be a nonbool integer between 1 and 9'


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
    assert section == ("brain imaging, Broca's area, lesion studies, "
                       "neural substrates, production readiness.")
    assert mod.SCOPE == 'PARTIAL: activation mapping over supplied signals'
    assert mod.NOT_CLAIMED == ('brain imaging', "Broca's area",
                               'lesion studies', 'neural substrates',
                               'production readiness')


def _expected(rows):
    activators = {}
    signal_sum = {}
    for region, task, signal in rows:
        if region not in activators:
            activators[region] = {}
            signal_sum[region] = 0
        if signal >= 5:
            activators[region][task] = True
        signal_sum[region] += signal
    engaged = {}
    for region in activators:
        engaged[region] = len(activators[region])
    hot = sorted(region for region in engaged if engaged[region] >= 3)
    cold = sorted(region for region in engaged if engaged[region] == 0)
    busiest = None
    for region in signal_sum:
        if busiest is None or signal_sum[region] > signal_sum[busiest]:
            busiest = region
    return {'total': len(rows), 'engaged': engaged, 'hot': hot,
            'cold': cold, 'signal': signal_sum, 'busiest': busiest}


def _core(m):
    # fixed pins, oracle seeded with row number 1890
    assert m.map_activation([('broca', 'naming', 7), ('broca', 'syntax', 2),
                             ('wernicke', 'syntax', 6),
                             ('broca', 'reading', 5)]) == {
        'total': 4, 'engaged': {'broca': 2, 'wernicke': 1}, 'hot': [],
        'cold': [], 'signal': {'broca': 14, 'wernicke': 6},
        'busiest': 'broca'}
    # one weak row: a cold region
    assert m.map_activation([('r', 't', 4)]) == {
        'total': 1, 'engaged': {'r': 0}, 'hot': [], 'cold': ['r'],
        'signal': {'r': 4}, 'busiest': 'r'}
    # a signal of exactly 5 activates, 4 never does
    r = m.map_activation([('r', 't', 5)])
    assert r['engaged'] == {'r': 1} and r['cold'] == []
    r = m.map_activation([('r', 't', 4), ('r', 't', 4), ('r', 't', 4)])
    assert r['engaged'] == {'r': 0} and r['cold'] == ['r']
    # one task cannot activate twice
    r = m.map_activation([('r', 't', 9), ('r', 't', 9)])
    assert r['engaged'] == {'r': 1}
    # three tasks is hot, two is not
    r = m.map_activation([('r', 'a', 9), ('r', 'b', 9), ('r', 'c', 9)])
    assert r['hot'] == ['r']
    r = m.map_activation([('r', 'a', 9), ('r', 'b', 9)])
    assert r['hot'] == []
    # the busiest tie goes to the first supplied
    r = m.map_activation([('a', 't', 5), ('b', 't', 5)])
    assert r['busiest'] == 'a'
    # signal piles up weak activations too
    r = m.map_activation([('r', 't1', 2), ('r', 't2', 2)])
    assert r['signal'] == {'r': 4} and r['engaged'] == {'r': 0}
    # dicts keep first-touch order
    r = m.map_activation([('z', 't', 1), ('a', 't', 2)])
    assert r['signal'] == {'z': 1, 'a': 2}
    # non-ASCII regions and tasks follow the same rule
    r = m.map_activation([('Üser-9!', 'Ω-1', 9), ('q?7', 'Ω-1', 1)])
    assert r == {'total': 2, 'engaged': {'Üser-9!': 1, 'q?7': 0},
                 'hot': [], 'cold': ['q?7'],
                 'signal': {'Üser-9!': 9, 'q?7': 1}, 'busiest': 'Üser-9!'}
    rng = random.Random(1890)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.map_activation(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.map_activation, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.map_activation, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.map_activation, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.map_activation, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (region, task, signal) triple',
            m.map_activation, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.map_activation, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.map_activation, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, RM, m.map_activation, [(1, 'b', 1)])
    _raises(ValueError, RM, m.map_activation, [('', 'b', 1)])
    _raises(ValueError, RM, m.map_activation, [('x' * 17, 'b', 1)])
    _raises(ValueError, TM, m.map_activation, [('a', 1, 1)])
    _raises(ValueError, TM, m.map_activation, [('a', '', 1)])
    _raises(ValueError, TM, m.map_activation, [('a', 'x' * 17, 1)])
    _raises(ValueError, SM, m.map_activation, [('a', 'b', '1')])
    _raises(ValueError, SM, m.map_activation, [('a', 'b', 0)])
    _raises(ValueError, SM, m.map_activation, [('a', 'b', 10)])
    _raises(ValueError, SM, m.map_activation, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: region must be a string of 1 to 16 characters',
            m.map_activation, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: signal must be a nonbool integer between 1 and 9',
            m.map_activation, [('a', 'b', 1), ('c', 'd', 0)])
    # region is validated before task, task before signal
    _raises(ValueError, RM, m.map_activation, [('x' * 17, '', 0)])
    _raises(ValueError, TM, m.map_activation, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.map_activation, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.map_activation((('a', 'b', 1),)) == m.map_activation([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.map_activation([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.map_activation([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.map_activation([('a', 'b', 1)] * 60)['total'] == 60
    assert m.map_activation([('a', 'b', 9)])['signal'] == {'a': 9}
    # pre-seed pin: fresh accumulators only
    assert m.map_activation([('p', 'a', 9), ('q', 'b', 1), ('p', 'b', 8)]) == {
        'total': 3, 'engaged': {'p': 2, 'q': 0}, 'hot': [], 'cold': ['q'],
        'signal': {'p': 17, 'q': 1}, 'busiest': 'p'}
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
        _raises(TypeError, P, m.map_activation, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (region, task, signal) triple',
                m.map_activation, [K(('a', 'b', 1))])
    _raises(ValueError, RM, m.map_activation, [(S('a'), 'b', 1)])
    _raises(ValueError, TM, m.map_activation, [('a', S('b'), 1)])
    _raises(ValueError, SM, m.map_activation, [('a', 'b', I(1))])
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
    ('type(region) is not str', 'not isinstance(region, str)'),
    ('type(task) is not str', 'not isinstance(task, str)'),
    ('type(signal) is not int', 'not isinstance(signal, int)'),
    ('not 1 <= len(region) <= 16', 'not 1 <= len(region) <= 17'),
    ('not 1 <= len(task) <= 16', 'not 1 <= len(task) <= 17'),
    ('not 1 <= signal <= 9', 'not 1 <= signal <= 10'),
    ('        if signal >= 5:', '        if signal >= 6:'),
    ('        signal_sum[region] += signal', '        signal_sum[region] += 1'),
    ('if engaged[region] >= 3', 'if engaged[region] >= 4'),
    ('if engaged[region] == 0', 'if engaged[region] == 1'),
    ('if busiest is None or signal_sum[region] > signal_sum[busiest]:',
     'if busiest is None or signal_sum[region] < signal_sum[busiest]:'),
    ("'hot': hot", "'hot': cold"),
    ("'engaged': engaged", "'engaged': signal_sum"),
    ("'signal': signal_sum", "'signal': engaged"),
    ("'total': len(rows)", "'total': len(signal_sum)"),
    ('        region, task, signal = row',
     '        task, region, signal = row'),
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
    assert mod.map_activation([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.map_activation([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.map_activation([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

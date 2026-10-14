import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import agent_coordination as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
AG = 'row 1: agent must be a string of 1 to 16 characters'
CH = 'row 1: channel must be a string of 1 to 16 characters'
LO = 'row 1: load must be a nonbool integer between 1 and 9'


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
    assert section == ('task scheduling, load balancing, fault '
                       'tolerance, network transport, production readiness.')
    assert mod.SCOPE == 'PARTIAL: span tracking over supplied loads'
    assert mod.NOT_CLAIMED == ('task scheduling', 'load balancing',
                               'fault tolerance', 'network transport',
                               'production readiness')


def _expected(rows):
    tightenings = 0
    previous = None
    for k in range(1, len(rows) + 1):
        totals = {}
        for agent, channel, load in rows[:k]:
            totals[agent] = totals.get(agent, 0) + load
        if len(totals) >= 2:
            span = max(totals.values()) - min(totals.values())
            if previous is not None and span < previous:
                tightenings += 1
            previous = span
    sums = {}
    for agent, channel, load in rows:
        sums[agent] = sums.get(agent, 0) + load
    return {'total': len(rows), 'sums': sums,
            'tightenings': tightenings,
            'span': previous if previous is not None else 0}


def _core(m):
    # fixed pins, oracle seeded with row number 1941
    assert m.tighten_spans([('a', 'c', 9), ('b', 'c', 1),
                            ('b', 'c', 2)]) == {
        'total': 3, 'sums': {'a': 9, 'b': 3}, 'tightenings': 1, 'span': 6}
    # one row accepted with full expected output
    assert m.tighten_spans([('s', 'c', 5)]) == {
        'total': 1, 'sums': {'s': 5}, 'tightenings': 0, 'span': 0}
    # the first span appears once two agents are seen
    assert m.tighten_spans([('a', 'c', 5), ('b', 'c', 2)]) == {
        'total': 2, 'sums': {'a': 5, 'b': 2}, 'tightenings': 0, 'span': 3}
    # a widening span is not a tightening
    assert m.tighten_spans([('a', 'c', 5), ('b', 'c', 5),
                            ('a', 'c', 9)]) == {
        'total': 3, 'sums': {'a': 14, 'b': 5}, 'tightenings': 0, 'span': 9}
    # an unchanged span is not a tightening
    assert m.tighten_spans([('a', 'c', 5), ('b', 'c', 1),
                            ('x', 'c', 3), ('x', 'c', 1)]) == {
        'total': 4, 'sums': {'a': 5, 'b': 1, 'x': 4},
        'tightenings': 0, 'span': 4}
    # every strict decrease counts
    assert m.tighten_spans([('a', 'c', 9), ('b', 'c', 1), ('b', 'c', 1),
                            ('b', 'c', 1)]) == {
        'total': 4, 'sums': {'a': 9, 'b': 3}, 'tightenings': 2, 'span': 6}
    # dicts keep first-touch order
    r = m.tighten_spans([('z', 'c', 1), ('a', 'c', 1)])
    assert r['sums'] == {'z': 1, 'a': 1} and r['span'] == 0
    # non-ASCII agents follow the same rule
    r = m.tighten_spans([('Üser-9!', 'c', 2), ('q?7', 'c', 1),
                         ('q?7', 'c', 3)])
    assert r == {'total': 3, 'sums': {'Üser-9!': 2, 'q?7': 4},
                 'tightenings': 0, 'span': 2}
    # pre-seed pin: fresh accumulators only
    assert m.tighten_spans([('m', 'c', 1), ('n', 'c', 9),
                            ('m', 'c', 1)]) == {
        'total': 3, 'sums': {'m': 2, 'n': 9}, 'tightenings': 1, 'span': 7}
    rng = random.Random(1941)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.tighten_spans(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.tighten_spans, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.tighten_spans, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.tighten_spans, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.tighten_spans, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected an (agent, channel, load) triple',
            m.tighten_spans, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.tighten_spans, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.tighten_spans, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, AG, m.tighten_spans, [(1, 'b', 1)])
    _raises(ValueError, AG, m.tighten_spans, [('', 'b', 1)])
    _raises(ValueError, AG, m.tighten_spans, [('x' * 17, 'b', 1)])
    _raises(ValueError, CH, m.tighten_spans, [('a', 1, 1)])
    _raises(ValueError, CH, m.tighten_spans, [('a', '', 1)])
    _raises(ValueError, CH, m.tighten_spans, [('a', 'x' * 17, 1)])
    _raises(ValueError, LO, m.tighten_spans, [('a', 'b', '1')])
    _raises(ValueError, LO, m.tighten_spans, [('a', 'b', 0)])
    _raises(ValueError, LO, m.tighten_spans, [('a', 'b', 10)])
    _raises(ValueError, LO, m.tighten_spans, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: agent must be a string of 1 to 16 characters',
            m.tighten_spans, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: load must be a nonbool integer between 1 and 9',
            m.tighten_spans, [('a', 'b', 1), ('c', 'd', 0)])
    # agent is validated before channel, channel before load
    _raises(ValueError, AG, m.tighten_spans, [('x' * 17, '', 0)])
    _raises(ValueError, CH, m.tighten_spans, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.tighten_spans, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.tighten_spans((('a', 'b', 1),)) == m.tighten_spans([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.tighten_spans([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.tighten_spans([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.tighten_spans([('a', 'b', 1)] * 60)['total'] == 60
    assert m.tighten_spans([('a', 'b', 9)])['sums'] == {'a': 9}
    assert m.tighten_spans([('a', 'b', 1)])['sums'] == {'a': 1}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.tighten_spans([('x' * 16, 'b', 5)])['total'] == 1
    assert m.tighten_spans([('a', 'y' * 16, 5)])['total'] == 1
    assert m.tighten_spans([('a', 'b', 5),
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
        _raises(TypeError, P, m.tighten_spans, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected an (agent, channel, load) triple',
                m.tighten_spans, [K(('a', 'b', 1))])
    _raises(ValueError, AG, m.tighten_spans, [(S('a'), 'b', 1)])
    _raises(ValueError, CH, m.tighten_spans, [('a', S('b'), 1)])
    _raises(ValueError, LO, m.tighten_spans, [('a', 'b', I(1))])
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
    ('type(agent) is not str', 'not isinstance(agent, str)'),
    ('type(channel) is not str', 'not isinstance(channel, str)'),
    ('type(load) is not int', 'not isinstance(load, int)'),
    ('not 1 <= len(agent) <= 16', 'not 1 <= len(agent) <= 17'),
    ('not 1 <= len(channel) <= 16', 'not 1 <= len(channel) <= 17'),
    ('not 1 <= load <= 9', 'not 1 <= load <= 10'),
    ('if len(sums) >= 2:', 'if len(sums) >= 3:'),
    ('if previous is not None and span < previous:',
     'if previous is not None and span <= previous:'),
    ('if previous is not None and span < previous:',
     'if previous is not None and span > previous:'),
    ('sums[agent] += load', 'sums[agent] += 1'),
    ('max(sums.values()) - min(sums.values())',
     'max(sums.values()) - max(sums.values())'),
    ('            previous = span', '            previous = 0'),
    ("'sums': sums", "'sums': {}"),
    ("'tightenings': tightenings", "'tightenings': 0"),
    ("'span': previous if previous is not None else 0", "'span': 0"),
    ("'total': len(rows)", "'total': len(sums)"),
    ('        agent, channel, load = row',
     '        channel, agent, load = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True

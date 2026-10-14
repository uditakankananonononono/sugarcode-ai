import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import anthropology_of_religion as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
TB = 'row 1: tribe must be a string of 1 to 16 characters'
RT = 'row 1: rite must be a string of 1 to 16 characters'
DR = 'row 1: duration must be a nonbool integer between 1 and 9'


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
    assert section == ('participant observation, cultural relativism, '
                       'kinship systems, fieldwork ethics, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: rite recording over supplied durations'
    assert mod.NOT_CLAIMED == ('participant observation',
                               'cultural relativism', 'kinship systems',
                               'fieldwork ethics', 'production readiness')


def _expected(rows):
    records = 0
    holders = []
    best = 0
    totals = {}
    for tribe, rite, duration in rows:
        if duration > best:
            records += 1
            holders.append(rite)
            best = duration
        if tribe not in totals:
            totals[tribe] = 0
        totals[tribe] += duration
    enduring = None
    for tribe in totals:
        if enduring is None or totals[tribe] > totals[enduring]:
            enduring = tribe
    return {'total': len(rows), 'records': records, 'holders': holders,
            'longest': holders[-1], 'totals': totals, 'enduring': enduring}


def _core(m):
    # fixed pins, oracle seeded with row number 1903
    assert m.record_rites([('t1', 'rain', 3), ('t2', 'dance', 1),
                           ('t1', 'feast', 5), ('t2', 'fast', 9),
                           ('t1', 'song', 4)]) == {
        'total': 5, 'records': 3, 'holders': ['rain', 'feast', 'fast'],
        'longest': 'fast', 'totals': {'t1': 12, 't2': 10}, 'enduring': 't1'}
    # one row is always the first record
    assert m.record_rites([('t', 'r', 5)]) == {
        'total': 1, 'records': 1, 'holders': ['r'], 'longest': 'r',
        'totals': {'t': 5}, 'enduring': 't'}
    # matching the best duration is not a record
    r = m.record_rites([('t', 'a', 9), ('t', 'b', 9)])
    assert r['records'] == 1 and r['holders'] == ['a']
    # the same rite can set more than one record
    r = m.record_rites([('t', 'a', 1), ('t', 'a', 5)])
    assert r['records'] == 2 and r['holders'] == ['a', 'a']
    # a descending start still records the first row only
    r = m.record_rites([('t', 'a', 9), ('t', 'b', 1), ('t', 'c', 5)])
    assert r['records'] == 1 and r['longest'] == 'a'
    # the enduring tie goes to the first supplied tribe
    r = m.record_rites([('x', 'r', 7), ('y', 's', 3)])
    assert r['totals'] == {'x': 7, 'y': 3} and r['enduring'] == 'x'
    r = m.record_rites([('p', 'a', 4), ('p', 'b', 6),
                        ('q', 'c', 9), ('q', 'd', 1)])
    assert r['totals'] == {'p': 10, 'q': 10} and r['enduring'] == 'p'
    # dicts keep first-touch order
    r = m.record_rites([('z', 'r', 1), ('a', 's', 2)])
    assert r['totals'] == {'z': 1, 'a': 2}
    # non-ASCII tribes and rites follow the same rule
    r = m.record_rites([('Üser-9!', 'Ω-1', 2), ('q?7', 'a', 8)])
    assert r == {'total': 2, 'records': 2, 'holders': ['Ω-1', 'a'],
                 'longest': 'a', 'totals': {'Üser-9!': 2, 'q?7': 8},
                 'enduring': 'q?7'}
    # pre-seed pin: fresh accumulators only
    assert m.record_rites([('p', 'a', 4), ('p', 'b', 6),
                           ('q', 'c', 9), ('q', 'd', 1)]) == {
        'total': 4, 'records': 3, 'holders': ['a', 'b', 'c'],
        'longest': 'c', 'totals': {'p': 10, 'q': 10}, 'enduring': 'p'}
    rng = random.Random(1903)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.record_rites(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.record_rites, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.record_rites, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.record_rites, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.record_rites, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (tribe, rite, duration) triple',
            m.record_rites, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.record_rites, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.record_rites, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, TB, m.record_rites, [(1, 'b', 1)])
    _raises(ValueError, TB, m.record_rites, [('', 'b', 1)])
    _raises(ValueError, TB, m.record_rites, [('x' * 17, 'b', 1)])
    _raises(ValueError, RT, m.record_rites, [('a', 1, 1)])
    _raises(ValueError, RT, m.record_rites, [('a', '', 1)])
    _raises(ValueError, RT, m.record_rites, [('a', 'x' * 17, 1)])
    _raises(ValueError, DR, m.record_rites, [('a', 'b', '1')])
    _raises(ValueError, DR, m.record_rites, [('a', 'b', 0)])
    _raises(ValueError, DR, m.record_rites, [('a', 'b', 10)])
    _raises(ValueError, DR, m.record_rites, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: tribe must be a string of 1 to 16 characters',
            m.record_rites, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: duration must be a nonbool integer between 1 and 9',
            m.record_rites, [('a', 'b', 1), ('c', 'd', 0)])
    # tribe is validated before rite, rite before duration
    _raises(ValueError, TB, m.record_rites, [('x' * 17, '', 0)])
    _raises(ValueError, RT, m.record_rites, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.record_rites, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.record_rites((('a', 'b', 1),)) == m.record_rites([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.record_rites([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.record_rites([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.record_rites([('a', 'b', 1)] * 60)['total'] == 60
    assert m.record_rites([('a', 'b', 9)])['records'] == 1
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
        _raises(TypeError, P, m.record_rites, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (tribe, rite, duration) triple',
                m.record_rites, [K(('a', 'b', 1))])
    _raises(ValueError, TB, m.record_rites, [(S('a'), 'b', 1)])
    _raises(ValueError, RT, m.record_rites, [('a', S('b'), 1)])
    _raises(ValueError, DR, m.record_rites, [('a', 'b', I(1))])
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
    ('type(tribe) is not str', 'not isinstance(tribe, str)'),
    ('type(rite) is not str', 'not isinstance(rite, str)'),
    ('type(duration) is not int', 'not isinstance(duration, int)'),
    ('not 1 <= len(tribe) <= 16', 'not 1 <= len(tribe) <= 17'),
    ('not 1 <= len(rite) <= 16', 'not 1 <= len(rite) <= 17'),
    ('not 1 <= duration <= 9', 'not 1 <= duration <= 10'),
    ('        if duration > best:', '        if duration >= best:'),
    ('            records += 1', '            records += 2'),
    ('    best = 0', '    best = 1'),
    ('        totals[tribe] += duration', '        totals[tribe] += 1'),
    ("'longest': holders[-1]", "'longest': holders[0]"),
    ("'holders': holders", "'holders': []"),
    ('if enduring is None or totals[tribe] > totals[enduring]:',
     'if enduring is None or totals[tribe] < totals[enduring]:'),
    ("'totals': totals", "'totals': {}"),
    ("'total': len(rows)", "'total': len(totals)"),
    ('        tribe, rite, duration = row',
     '        rite, tribe, duration = row'),
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
    assert mod.record_rites([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.record_rites([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.record_rites([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2

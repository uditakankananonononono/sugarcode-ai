import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import deliberation as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


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
    code = compile(mutated, 'mutant', 'exec')  # a syntax error is not a kill
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


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingI(int):
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: weight totaling over supplied rows, no real deliberation'
    assert len(mod.NOT_CLAIMED) >= 4 and 'truth' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_WEIGHT, mod.SIDES) == (100, 10, ('for', 'against'))


def _oracle(rows):
    """Independent: two running sums, leaning from their difference."""
    pro = 0
    con = 0
    for side, weight in rows:
        if side == 'for':
            pro += weight
        else:
            con += weight
    diff = pro - con
    if diff > 0:
        lean = 'for'
    elif diff < 0:
        lean = 'against'
    else:
        lean = 'even'
    return {'for': pro, 'against': con, 'balance': diff, 'leaning': lean, 'rows': len(rows)}


def _core(m):
    assert m.weigh([('for', 5), ('against', 3)]) == {
        'for': 5, 'against': 3, 'balance': 2, 'leaning': 'for', 'rows': 2}
    # a heavier against side leans against with a negative balance
    assert m.weigh([('for', 1), ('against', 4)]) == {
        'for': 1, 'against': 4, 'balance': -3, 'leaning': 'against', 'rows': 2}
    # matched totals are even, including the empty case
    assert m.weigh([('for', 2), ('against', 2)])['leaning'] == 'even'
    assert m.weigh([]) == {'for': 0, 'against': 0, 'balance': 0, 'leaning': 'even', 'rows': 0}
    # repeated rows on one side accumulate
    assert m.weigh([('for', 3), ('for', 3), ('against', 5)]) == {
        'for': 6, 'against': 5, 'balance': 1, 'leaning': 'for', 'rows': 3}
    # tuples accepted at every level
    assert m.weigh((('for', 1),))['rows'] == 1
    rng = random.Random(746)
    for _ in range(400):
        rows = [(rng.choice(['for', 'against']), rng.randint(1, 10))
                for _ in range(rng.randint(0, 12))]
        assert m.weigh(rows) == _oracle(rows)


def _late(m):
    PTS = 'points must be a list or tuple'
    CAP = 'points must contain at most 100 rows'
    ROW = 'each point must be a (side, weight) row'
    SID = 'side must be for or against'
    WGT = 'weight must be an integer from 1 to 10'
    good = [('for', 5)]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, PTS, m.weigh, bad)
    _raises(TypeError, PTS, m.weigh, L(good * 101))             # subclass refused before the cap
    _raises(ValueError, CAP, m.weigh, good * 101)
    assert m.weigh(good * 100)['rows'] == 100
    for bad in ('fw', 5, None, ('for',), ('for', 5, 'x'), ()):
        _raises(ValueError, ROW, m.weigh, [bad])
        _raises(ValueError, ROW, m.weigh, [('for', 5), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.weigh, [K(('for', 5))])
    for bad in ('', 'FOR', 'for ', 'yes', None, 5, S('for'), LyingS('for'), I(0)):
        _raises(ValueError, SID, m.weigh, [(bad, 5)])
        _raises(ValueError, SID, m.weigh, [('for', 5), (bad, 1)])
    for bad in (0, 11, -1, 100, '5', 5.0, None, True, False, I(5), LyingI(5)):
        _raises(ValueError, WGT, m.weigh, [('for', bad)])
        _raises(ValueError, WGT, m.weigh, [('against', 1), ('for', bad)])
    assert m.weigh([('for', 10), ('against', 1)])['balance'] == 9
    assert m.weigh([('for', 1)])['for'] == 1                     # the floor weight counts
    # order: container, cap, rows (shape, side, weight)
    _raises(TypeError, PTS, m.weigh, L(good))
    _raises(ValueError, CAP, m.weigh, [('maybe', 5)] * 101)
    _raises(ValueError, ROW, m.weigh, [('for', 5, 'x')])
    _raises(ValueError, SID, m.weigh, [(S('for'), 5)])
    _raises(ValueError, WGT, m.weigh, [('for', I(5))])
    # the first bad row reports first
    _raises(ValueError, SID, m.weigh, [('maybe', 99), ('for', 5, 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    points = [('for', 5), ('against', 3)]
    assert mod.weigh(points)['balance'] == 2
    assert points == [('for', 5), ('against', 3)]
    assert mod.weigh(points)['rows'] == 2


MUTANTS = [
    ("    if type(points) not in (list, tuple):", "    if not isinstance(points, (list, tuple)):"),
    ("    if len(points) > MAX_ROWS:", "    if len(points) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(side) is not str or side not in SIDES:",
     "        if not isinstance(side, str) or side not in SIDES:"),
    ("side not in SIDES", "side not in SIDES[:1]"),
    ("SIDES = ('for', 'against')", "SIDES = ('for',)"),
    ("        if type(weight) is not int or not 1 <= weight <= MAX_WEIGHT:",
     "        if type(weight) is not int or not 1 <= weight < MAX_WEIGHT:"),
    ("not 1 <= weight <= MAX_WEIGHT", "not 0 <= weight <= MAX_WEIGHT"),
    ("MAX_WEIGHT = 10", "MAX_WEIGHT = 11"),
    ("    totals = {'for': 0, 'against': 0}", "    totals = {'for': 1, 'against': 0}"),
    ("        totals[side] += weight", "        totals[side] += 1"),
    ("        totals[side] += weight", "        totals['for'] += weight"),
    ("    balance = totals['for'] - totals['against']", "    balance = totals['for'] + totals['against']"),
    ("    balance = totals['for'] - totals['against']", "    balance = totals['against'] - totals['for']"),
    ("    leaning = 'for' if balance > 0 else 'against' if balance < 0 else 'even'",
     "    leaning = 'for' if balance >= 0 else 'against' if balance < 0 else 'even'"),
    ("    leaning = 'for' if balance > 0 else 'against' if balance < 0 else 'even'",
     "    leaning = 'for' if balance > 0 else 'even'"),
    ("    for side, weight in rows:\n        totals[side] += weight",
     "    for side, weight in rows[1:]:\n        totals[side] += weight"),
    ("'points must be a list or tuple'", "'points must be a sequence'"),
    ("'points must contain at most 100 rows'", "'points must contain at most 99 rows'"),
    ("'each point must be a (side, weight) row'", "'each point must be a (side, weight) tuple'"),
    ("'side must be for or against'", "'side must be for'"),
    ("'weight must be an integer from 1 to 10'", "'weight must be an integer from 1 to 9'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

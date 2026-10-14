import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import cooperation as mod

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
    assert mod.SCOPE == 'PARTIAL: hour balancing over supplied rows, no real cooperation'
    assert len(mod.NOT_CLAIMED) >= 4 and 'payroll' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_WORKER, mod.MAX_HOURS) == (100, 8, 8)


def _oracle(rows):
    """Independent: totals in a dict, balance from a min/max walk."""
    totals = {}
    for worker, hours in rows:
        totals[worker] = totals.get(worker, 0) + hours
    ranked = sorted(totals.items(), key=lambda kv: (0 - kv[1], kv[0]))
    low = None
    high = None
    for value in totals.values():
        if low is None or value < low:
            low = value
        if high is None or value > high:
            high = value
    balanced = low is None or high - low <= 1
    return {'hours': ranked, 'total': sum(totals.values()), 'balanced': balanced}


def _core(m):
    assert m.share([('amy', 4), ('bo', 3), ('amy', 2)]) == {
        'hours': [('amy', 6), ('bo', 3)], 'total': 9, 'balanced': False}
    # a gap of one hour is still balanced
    assert m.share([('amy', 4), ('bo', 3)])['balanced'] is True
    # identical totals are balanced
    assert m.share([('amy', 4), ('bo', 4)])['balanced'] is True
    # nobody is balanced with zero hours
    assert m.share([]) == {'hours': [], 'total': 0, 'balanced': True}
    # one worker is always balanced
    assert m.share([('amy', 8)])['balanced'] is True
    # reversal cousins break on the real name
    assert m.share([('ab', 2), ('ba', 2)])['hours'] == [('ab', 2), ('ba', 2)]
    # ranking sorts by hours then name
    assert m.share([('zz', 2), ('aa', 2), ('mm', 5)])['hours'] == [('mm', 5), ('aa', 2), ('zz', 2)]
    # the balance follows the extremes, not the middle
    assert m.share([('a', 1), ('b', 2), ('c', 3)])['balanced'] is False
    # tuples accepted at every level
    assert m.share((('a', 1),))['total'] == 1
    rng = random.Random(768)
    for _ in range(400):
        rows = [(rng.choice(['a', 'b', 'cy']), rng.randint(1, 8))
                for _ in range(rng.randint(0, 10))]
        assert m.share(rows) == _oracle(rows)


def _late(m):
    SHF = 'shifts must be a list or tuple'
    CAP = 'shifts must contain at most 100 rows'
    ROW = 'each shift must be a (worker, hours) row'
    WRK = 'worker must be a string of 1 to 8 characters'
    HRS = 'hours must be an integer from 1 to 8'
    good = [('a', 3)]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, SHF, m.share, bad)
    _raises(TypeError, SHF, m.share, L(good * 101))             # subclass refused before the cap
    _raises(ValueError, CAP, m.share, good * 101)
    assert m.share(good * 100)['total'] == 300
    for bad in ('a3', 5, None, ('a',), ('a', 3, 'x'), ()):
        _raises(ValueError, ROW, m.share, [bad])
        _raises(ValueError, ROW, m.share, [('a', 3), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.share, [K(('a', 3))])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, WRK, m.share, [(bad, 3)])
        _raises(ValueError, WRK, m.share, [('a', 3), (bad, 1)])
    for bad in (0, 9, -1, 100, '3', 3.0, None, True, False, I(3), LyingI(3)):
        _raises(ValueError, HRS, m.share, [('a', bad)])
        _raises(ValueError, HRS, m.share, [('a', 1), ('b', bad)])
    assert m.share([('x' * 8, 8)])['total'] == 8
    assert m.share([('x', 1)])['total'] == 1                     # single-character worker accepted
    # order: container, cap, rows (shape, worker, hours)
    _raises(TypeError, SHF, m.share, L(good))
    _raises(ValueError, CAP, m.share, [('a', 99)] * 101)
    _raises(ValueError, ROW, m.share, [('a', 3, 'x')])
    _raises(ValueError, WRK, m.share, [(S('a'), 3)])
    _raises(ValueError, HRS, m.share, [('a', I(3))])
    # the first bad row reports first
    _raises(ValueError, WRK, m.share, [(5, 99), ('a', 3, 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    rows = [('a', 4), ('b', 3)]
    r = mod.share(rows)
    r['hours'].append(('bogus', 9))
    assert rows == [('a', 4), ('b', 3)]
    assert mod.share(rows)['hours'] == [('a', 4), ('b', 3)]


MUTANTS = [
    ("    if type(rows_in) not in (list, tuple):", "    if not isinstance(rows_in, (list, tuple)):"),
    ("    if len(rows_in) > MAX_ROWS:", "    if len(rows_in) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(worker) is not str or not 1 <= len(worker) <= MAX_WORKER:",
     "        if not isinstance(worker, str) or not 1 <= len(worker) <= MAX_WORKER:"),
    ("not 1 <= len(worker) <= MAX_WORKER", "not 1 <= len(worker) < MAX_WORKER"),
    ("MAX_WORKER = 8", "MAX_WORKER = 9"),
    ("        if type(hours) is not int or not 1 <= hours <= MAX_HOURS:",
     "        if type(hours) is not int or not 1 <= hours < MAX_HOURS:"),
    ("not 1 <= hours <= MAX_HOURS", "not 0 <= hours <= MAX_HOURS"),
    ("MAX_HOURS = 8", "MAX_HOURS = 9"),
    ("    totals = {}", "    totals = {'zz': 1}"),
    ("        totals[worker] = totals.get(worker, 0) + hours", "        totals[worker] = totals.get(worker, 0) + 1"),
    ("        totals[worker] = totals.get(worker, 0) + hours", "        totals[worker] = totals.get(worker, 0)"),
    ("    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))",
     "    ranked = sorted(totals.items(), key=lambda kv: (kv[1], kv[0]))"),
    ("    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))",
     "    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0][::-1]))"),
    ("    balanced = not values or max(values) - min(values) <= 1",
     "    balanced = not values or max(values) - min(values) <= 0"),
    ("    balanced = not values or max(values) - min(values) <= 1",
     "    balanced = not values or max(values) - min(values) < 1"),
    ("    balanced = not values or max(values) - min(values) <= 1",
     "    balanced = not values or max(values) - min(values) <= 2"),
    ("    balanced = not values or max(values) - min(values) <= 1",
     "    balanced = max(values) - min(values) <= 1"),
    ("    return {'hours': ranked, 'total': sum(values), 'balanced': balanced}",
     "    return {'hours': ranked, 'total': sum(values) + 1, 'balanced': balanced}"),
    ("    for worker, hours in rows:\n        totals[worker] = totals.get(worker, 0) + hours",
     "    for worker, hours in rows[1:]:\n        totals[worker] = totals.get(worker, 0) + hours"),
    ("'shifts must be a list or tuple'", "'shifts must be a sequence'"),
    ("'shifts must contain at most 100 rows'", "'shifts must contain at most 99 rows'"),
    ("'each shift must be a (worker, hours) row'", "'each shift must be a (worker, hours) tuple'"),
    ("'worker must be a string of 1 to 8 characters'", "'worker must be a string of 1 to 7 characters'"),
    ("'hours must be an integer from 1 to 8'", "'hours must be an integer from 1 to 7'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

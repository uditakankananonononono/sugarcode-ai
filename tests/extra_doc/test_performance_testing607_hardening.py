"""Row607 hardening: exact-type subclass pins, full-message pins, clock-spy
oracles (battery-safe manual patching), boundary accepts, mutation sweep.
Tests-only delta."""
import enum
import pathlib
import signal
import types

import pytest

from sugarcode.extra_doc import performance_testing607 as mod

SRC = pathlib.Path(mod.__file__).read_text()


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


class LyingGe(int):
    def __ge__(self, other):
        return True

    def __le__(self, other):
        return True


class WeirdNe(int):
    def __ne__(self, other):
        return False

    def __eq__(self, other):
        return False


class Color(enum.IntEnum):
    RED = 1


class L(list):
    pass


def _patched_clock(m, ticks):
    orig = m.time.perf_counter_ns
    it = iter(ticks)
    m.time.perf_counter_ns = lambda: next(it)
    return orig, it


def _core(m):
    run = m.measure_sort
    orig_clock = m.time.perf_counter_ns
    try:
        # clock spy: exact aggregation oracle
        orig, ticks = _patched_clock(m, [100, 107, 200, 202, 300, 311])
        values = [3, -1, 3, 0]
        assert run(values, 3) == {'sorted_values': [-1, 0, 3, 3], 'durations_ns': [7, 2, 11],
                                  'minimum_ns': 2, 'maximum_ns': 11, 'mean_ns_fraction': '20/3',
                                  'repetitions': 3}
        assert values == [3, -1, 3, 0]  # input not mutated
        with pytest.raises(StopIteration):
            next(ticks)  # exactly 2 clock reads per repetition
        # exact fraction reduction and integer mean
        _patched_clock(m, [0, 1, 0, 2])
        assert run([1], 2)['mean_ns_fraction'] == '3/2'
        _patched_clock(m, [0, 0, 0, 0])
        assert run([1], 2)['mean_ns_fraction'] == '0'
        # zero durations accepted; backward clock refused with exact message
        _patched_clock(m, [5, 5])
        assert run([1], 1)['durations_ns'] == [0]
        _patched_clock(m, [2, 1])
        _raises(RuntimeError, 'monotonic clock moved backward', run, [1], 1)
        # every repetition sorts inside the timed interval
        events = []
        m.time.perf_counter_ns = lambda: events.append('clock') or 0
        m.sorted = lambda v: events.append('sort') or sorted(v)
        try:
            assert run([3, 1, 2], 4)['sorted_values'] == [1, 2, 3]
            assert events == ['clock', 'sort', 'clock'] * 4
        finally:
            del m.sorted
        # validation completes before any clock read
        m.time.perf_counter_ns = lambda: pytest.fail('clock read before validation')
        _raises(TypeError, 'exact nonbool integer required', run, [None], 1)
        _raises(ValueError, 'repetition count must be 1..32', run, [1], 0)
    finally:
        m.time.perf_counter_ns = orig_clock
    # boundary accepts under the real clock
    assert len(run([-1000000, 1000000] * 128, 32)['durations_ns']) == 32
    assert run([1], 1)['repetitions'] == 1
    # full exact error messages and validation order
    for bad in (None, (), True, {}, 'x', 1, 1.0):
        _raises(TypeError, 'exact integer list required', run, bad, 1)
    _raises(ValueError, 'value count must be 1..256', run, [], 1)
    _raises(ValueError, 'value count must be 1..256', run, [None] * 257, 1)  # cap before scan
    for bad in (None, True, 1.0, '1', [], {}):
        _raises(TypeError, 'exact nonbool repetition integer required', run, [1], bad)
    _raises(ValueError, 'repetition count must be 1..32', run, [1], 0)
    _raises(ValueError, 'repetition count must be 1..32', run, [1], 33)
    for bad in (None, True, 1.0, '1', [], {}):
        _raises(TypeError, 'exact nonbool integer required', run, [[1, bad, 3]][0], 1)
    for bad in (-1000001, 1000001, 10 ** 1000):
        _raises(ValueError, 'integer outside declared range', run, [bad], 1)
    # order: outer list, value cap, repetitions, then element scan
    _raises(ValueError, 'value count must be 1..256', run, [None] * 257, 'x')
    _raises(TypeError, 'exact nonbool repetition integer required', run, [None], 'x')


def _late(m):
    run = m.measure_sort
    _raises(TypeError, 'exact integer list required', run, L([1]), 1)
    for bad in (I(1), LyingGe(1), WeirdNe(1), Color.RED):
        _raises(TypeError, 'exact nonbool repetition integer required', run, [1], bad)
        _raises(TypeError, 'exact nonbool integer required', run, [bad], 1)
    # subclass refused before any cap or range check
    _raises(TypeError, 'exact integer list required', run, L([0] * 257), 1)
    _raises(TypeError, 'exact nonbool repetition integer required', run, [1], I(33))
    _raises(TypeError, 'exact nonbool integer required', run, [LyingGe(10 ** 30)], 1)
    _raises(TypeError, 'exact nonbool integer required', run, [1, 2, WeirdNe(10 ** 30)], 1)
    # exact list-shaped / int acceptance counterparts
    assert run(list([int(2), int(1)]), int(1))['sorted_values'] == [1, 2]


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('type(values) is not list', 'not isinstance(values, list)'),
    ('type(repetitions) is not int', 'not isinstance(repetitions, int)'),
    ('type(value) is not int', 'not isinstance(value, int)'),
    ('if not 1<=len(values)<=256', 'if not 1<=len(values)<=257'),
    ('if not 1<=len(values)<=256', 'if not 0<=len(values)<=256'),
    ('if not 1<=repetitions<=32', 'if not 1<=repetitions<=33'),
    ('if not 1<=repetitions<=32', 'if not 0<=repetitions<=32'),
    ('not -1000000<=value<=1000000', 'not -1000001<=value<=1000000'),
    ('not -1000000<=value<=1000000', 'not -1000000<=value<=1000001'),
    ('duration<0', 'duration<=0'),
    ('if duration<0', 'if False'),
    ('result=sorted(values)', 'result=list(values)'),
    ('for _ in range(repetitions)', 'for _ in range(1)'),
    ('durations.append(duration)', 'durations.append(0)'),
    ('duration=finish-start', 'duration=finish-start+1'),
    ("'minimum_ns':min(durations)", "'minimum_ns':max(durations)"),
    ("'maximum_ns':max(durations)", "'maximum_ns':min(durations)"),
    ('Fraction(sum(durations),repetitions)', 'Fraction(sum(durations),repetitions+1)'),
    ('str(Fraction(sum(durations),repetitions))', 'str(sum(durations)//repetitions)'),
    ("'repetitions':repetitions", "'repetitions':repetitions+1"),
    ('exact integer list required', 'exact int list required'),
    ('value count must be 1..256', 'value count must be 1xx256'),
    ('repetition count must be 1..32', 'repetition count must be 1xx32'),
    ('monotonic clock moved backward', 'clock moved backward'),
    ('exact nonbool repetition integer required', 'exact nonbool repetition int required'),
    ("raise ValueError('integer outside declared range')", "raise ValueError('integer outside declared bounds')"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

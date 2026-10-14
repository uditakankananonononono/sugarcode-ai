import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import backoff_schedule as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


def _load(src):
    m = types.ModuleType('mutant')
    exec(compile(src, 'mutant', 'exec'), m.__dict__)
    return m


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
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __ne__(self, o): return False
    def __eq__(self, o): return True
    __hash__ = int.__hash__


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('web')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: backoff delay arithmetic for supplied counts, nothing waits'
    assert len(mod.NOT_CLAIMED) >= 4 and 'random jitter' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(n, base, kind, cap):
    """Independent: closed forms through lookup of per-kind lambdas, min() for the cap."""
    f = {'fixed': lambda i: base, 'linear': lambda i: base + i * base, 'exponential': lambda i: base << i}[kind]
    raw = [f(i) for i in range(n)]
    d = [min(x, cap) for x in raw]
    return {'delays': d, 'total': sum(d), 'capped': sum(1 for x in raw if x > cap)}


def _core(m):
    assert m.backoff_schedule(0) == {'delays': [], 'total': 0, 'capped': 0}
    assert m.backoff_schedule(1) == {'delays': [100], 'total': 100, 'capped': 0}
    # defaults: base 100, exponential, cap 5000 -> 100 200 400 800 1600 3200 5000 5000
    assert m.backoff_schedule(8) == {'delays': [100, 200, 400, 800, 1600, 3200, 5000, 5000], 'total': 16300, 'capped': 2}
    assert m.backoff_schedule(7)['capped'] == 1 and m.backoff_schedule(7)['delays'][-1] == 5000 and m.backoff_schedule(6)['delays'][-1] == 3200
    assert m.backoff_schedule(4, 100, 'exponential', 5000) == m.backoff_schedule(4)
    assert m.backoff_schedule(4, 10, 'fixed') == {'delays': [10, 10, 10, 10], 'total': 40, 'capped': 0}
    assert m.backoff_schedule(4, 10, 'linear') == {'delays': [10, 20, 30, 40], 'total': 100, 'capped': 0}
    assert m.backoff_schedule(4, 10, 'exponential') == {'delays': [10, 20, 40, 80], 'total': 150, 'capped': 0}
    assert m.backoff_schedule(4, 10, 'linear', 25) == {'delays': [10, 20, 25, 25], 'total': 80, 'capped': 2}
    assert m.backoff_schedule(3, 10, 'fixed', 5) == {'delays': [5, 5, 5], 'total': 15, 'capped': 3}
    assert m.backoff_schedule(3, 10, 'fixed', 10)['capped'] == 0            # equal to the cap is not capped
    assert m.backoff_schedule(3, 10, 'fixed', 9)['capped'] == 3
    assert m.backoff_schedule(12, 1000, 'exponential', 100000)['delays'][-1] == 100000
    assert m.backoff_schedule(12, 1000, 'exponential', 100000)['capped'] == 5
    assert m.backoff_schedule(12, 1, 'exponential', 100000)['delays'][-1] == 2048
    assert m.backoff_schedule(12, 1000, 'linear', 100000)['delays'][-1] == 12000
    assert m.backoff_schedule(12, 1, 'fixed', 1)['total'] == 12
    for n in range(0, 13):
        for base in (1, 7, 100, 1000):
            for kind in ('fixed', 'linear', 'exponential'):
                for cap in (1, 50, 5000, 100000):
                    assert m.backoff_schedule(n, base, kind, cap) == _oracle(n, base, kind, cap), (n, base, kind, cap)
        assert m.backoff_schedule(n) == _oracle(n, 100, 'exponential', 5000)


def _late(m):
    CN = 'count must be a nonbool integer between 0 and 12'
    BS = 'base must be a nonbool integer between 1 and 1000'
    KD = 'kind must be fixed, linear or exponential'
    CP = 'cap must be a nonbool integer between 1 and 100000'
    BADI = (True, False, 1.0, '1', None, I(3), LyingI(3), LyingI(10 ** 30), I(10 ** 30), [3], (3,))
    for bad in (-1, 13) + BADI:
        _raises(ValueError, CN, m.backoff_schedule, bad)
    for bad in (0, 1001, -1) + BADI:
        _raises(ValueError, BS, m.backoff_schedule, 3, bad)
    for bad in (0, 100001, -1) + BADI:
        _raises(ValueError, CP, m.backoff_schedule, 3, 100, 'fixed', bad)
    for bad in ('', 'Fixed', 'constant', None, 5, S('fixed'), LyingS('fixed'), b'fixed', ['fixed']):
        _raises(ValueError, KD, m.backoff_schedule, 3, 100, bad)
    assert m.backoff_schedule(0)['total'] == 0 and m.backoff_schedule(12)['delays'][0] == 100
    assert m.backoff_schedule(1, 1, 'fixed', 1)['delays'] == [1] and m.backoff_schedule(1, 1000, 'fixed', 100000)['delays'] == [1000]
    # order: count, base, kind, cap
    _raises(ValueError, CN, m.backoff_schedule, I(1), I(1), S('x'), I(1))
    _raises(ValueError, BS, m.backoff_schedule, 1, I(1), S('x'), I(1))
    _raises(ValueError, KD, m.backoff_schedule, 1, 1, S('fixed'), I(1))
    _raises(ValueError, CP, m.backoff_schedule, 1, 1, 'fixed', I(1))


class I(int):
    pass


class S(str):
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('fixed')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(count, 0, 12", "_int(count, 1, 12"),
    ("_int(count, 0, 12", "_int(count, 0, 13"),
    ("_int(count, 0, 12", "_int(count, 0, 11"),
    ("_int(base, 1, 1000", "_int(base, 0, 1000"),
    ("_int(base, 1, 1000", "_int(base, 1, 1001"),
    ("_int(cap, 1, 100000", "_int(cap, 0, 100000"),
    ("_int(cap, 1, 100000", "_int(cap, 1, 100001"),
    ("base=100", "base=101"),
    ("kind='exponential'", "kind='linear'"),
    ("cap=5000", "cap=5001"),
    ("cap=5000", "cap=4999"),
    ("type(kind) is not str or kind not in KINDS", "not isinstance(kind, str) or kind not in KINDS"),
    ("KINDS = ('fixed', 'linear', 'exponential')", "KINDS = ('fixed', 'exponential')"),
    ("if kind == 'fixed':", "if kind != 'fixed':"),
    ("elif kind == 'linear':", "elif kind != 'linear':"),
    ("d = base * (i + 1)", "d = base * i"),
    ("d = base * 2 ** i", "d = base * 2 ** (i + 1)"),
    ("d = base * 2 ** i", "d = base * 2 * i"),
    ("if d > cap:", "if d >= cap:"),
    ("d = cap\n", "d = cap - 1\n"),
    ("capped += 1", "capped += 2"),
    ("'total': sum(delays)", "'total': sum(delays[:-1])"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import retry_attempts as mod

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
    assert mod.SCOPE == 'PARTIAL: retry decisions over supplied attempt outcomes, no real calls'
    assert len(mod.NOT_CLAIMED) >= 4 and 'jitter' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(outs, mr):
    """Independent: first stopping index among terminal outcomes and the attempt budget."""
    budget = mr + 1
    stop = next((i for i, o in enumerate(outs) if o != 'transient'), None)
    if stop is not None and stop < budget:
        return {'status': 'success' if outs[stop] == 'ok' else 'fatal', 'attempts': stop + 1, 'retries': stop}
    if len(outs) >= budget:
        return {'status': 'exhausted', 'attempts': budget, 'retries': budget - 1}
    return {'status': 'pending', 'attempts': len(outs), 'retries': max(len(outs) - 1, 0)}


def _core(m):
    a, t, f = 'ok', 'transient', 'fatal'
    assert m.retry_attempts([]) == {'status': 'pending', 'attempts': 0, 'retries': 0}
    assert m.retry_attempts([a]) == {'status': 'success', 'attempts': 1, 'retries': 0}
    assert m.retry_attempts([t, a]) == {'status': 'success', 'attempts': 2, 'retries': 1}
    assert m.retry_attempts([f, a]) == {'status': 'fatal', 'attempts': 1, 'retries': 0}
    assert m.retry_attempts([t, t, f]) == {'status': 'fatal', 'attempts': 3, 'retries': 2}
    assert m.retry_attempts([t]) == {'status': 'pending', 'attempts': 1, 'retries': 0}
    assert m.retry_attempts([t, t]) == {'status': 'pending', 'attempts': 2, 'retries': 1}
    # default 3 retries: 4 attempts at most
    assert m.retry_attempts([t, t, t, a]) == {'status': 'success', 'attempts': 4, 'retries': 3}
    assert m.retry_attempts([t, t, t, t, a]) == {'status': 'exhausted', 'attempts': 4, 'retries': 3}
    assert m.retry_attempts([t, t, t, f, a])['status'] == 'fatal'
    assert m.retry_attempts([t, t, t]) == {'status': 'pending', 'attempts': 3, 'retries': 2}
    assert m.retry_attempts([t, t, t, t]) == {'status': 'exhausted', 'attempts': 4, 'retries': 3}
    assert m.retry_attempts([t, a], 0) == {'status': 'exhausted', 'attempts': 1, 'retries': 0}
    assert m.retry_attempts([a], 0)['status'] == 'success' and m.retry_attempts([f], 0)['status'] == 'fatal'
    assert m.retry_attempts([t, t, a], 1) == {'status': 'exhausted', 'attempts': 2, 'retries': 1}
    assert m.retry_attempts([t] * 11 + [a], 10) == {'status': 'exhausted', 'attempts': 11, 'retries': 10}
    assert m.retry_attempts((t,) * 10 + (a,), 10) == {'status': 'success', 'attempts': 11, 'retries': 10}
    assert m.retry_attempts([t] * 12)['attempts'] == 4
    for mr in range(0, 11):
        for n in range(0, 13):
            for pos in [None] + list(range(n)):
                for term in (a, f):
                    outs = [term if i == pos else t for i in range(n)]
                    assert m.retry_attempts(outs, mr) == _oracle(outs, mr), (outs, mr)
    rng = random.Random(656)
    for _ in range(300):
        outs = [rng.choice([a, t, t, f]) for _ in range(rng.randint(0, 12))]
        assert m.retry_attempts(outs) == _oracle(outs, 3)


def _late(m):
    OT = 'outcomes must be a list or tuple'
    SZ = 'outcomes must contain at most 12 entries'
    MR = 'max_retries must be a nonbool integer between 0 and 10'
    OC = 'outcome must be ok, transient or fatal'
    for bad in ('ab', None, 5, {}, L(['ok']), T(['ok']), L(), T()):
        _raises(TypeError, OT, m.retry_attempts, bad)
    _raises(TypeError, OT, m.retry_attempts, L(['ok'] * 13))
    _raises(ValueError, SZ, m.retry_attempts, ['ok'] * 13)
    assert m.retry_attempts(['transient'] * 12)['attempts'] == 4
    for bad in (-1, 11, True, False, 1.0, '1', None, I(3), LyingI(3), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MR, m.retry_attempts, ['ok'], bad)
    assert m.retry_attempts(['ok'], 0) and m.retry_attempts(['ok'], 10)
    for bad in ('', 'OK', 'retry', None, 5, True, S('ok'), LyingS('ok'), b'ok', ['ok']):
        _raises(ValueError, OC, m.retry_attempts, [bad])
        _raises(ValueError, OC, m.retry_attempts, ['ok', bad])                           # validated after the success
        _raises(ValueError, OC, m.retry_attempts, ['fatal', bad])
        _raises(ValueError, OC, m.retry_attempts, ['transient'] * 4 + [bad])             # and after exhaustion
    # order: type, size, max_retries, then outcomes
    _raises(TypeError, OT, m.retry_attempts, L([1]), I(1))
    _raises(ValueError, SZ, m.retry_attempts, [1] * 13, I(1))
    _raises(ValueError, MR, m.retry_attempts, [1], I(1))
    _raises(ValueError, OC, m.retry_attempts, [1], 3)


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('ok')


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
    ("type(outcomes) not in (list, tuple)", "not isinstance(outcomes, (list, tuple))"),
    ("len(outcomes) > MAX_OUTCOMES", "len(outcomes) >= MAX_OUTCOMES"),
    ("MAX_OUTCOMES = 12", "MAX_OUTCOMES = 13"),
    ("max_retries=3", "max_retries=2"),
    ("max_retries=3", "max_retries=4"),
    ("type(max_retries) is not int or not 0 <= max_retries <= 10", "not isinstance(max_retries, int) or not 0 <= max_retries <= 10"),
    ("type(max_retries) is not int or not 0 <= max_retries <= 10", "isinstance(max_retries, bool) or not isinstance(max_retries, int) or not 0 <= max_retries <= 10"),
    ("not 0 <= max_retries <= 10", "not 1 <= max_retries <= 10"),
    ("not 0 <= max_retries <= 10", "not 0 <= max_retries < 10"),
    ("not 0 <= max_retries <= 10", "not 0 <= max_retries <= 11"),
    ("type(o) is not str or o not in KINDS", "not isinstance(o, str) or o not in KINDS"),
    ("KINDS = ('ok', 'transient', 'fatal')", "KINDS = ('ok', 'transient')"),
    ("attempts += 1", "attempts += 2"),
    ("if o == 'ok':", "if o != 'ok':"),
    ("status = 'success'", "status = 'fatal'"),
    ("if o == 'fatal':", "if o == 'transient':"),
    ("status = 'fatal'\n            break", "status = 'success'\n            break"),
    ("if attempts == max_retries + 1:", "if attempts == max_retries:"),
    ("if attempts == max_retries + 1:", "if attempts == max_retries + 2:"),
    ("status = 'exhausted'", "status = 'pending'"),
    ("status = 'pending'\n    for", "status = 'exhausted'\n    for"),
    ("'retries': max(attempts - 1, 0)", "'retries': attempts"),
    ("'retries': max(attempts - 1, 0)", "'retries': attempts - 1"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

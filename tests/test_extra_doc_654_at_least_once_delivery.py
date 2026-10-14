import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import at_least_once_delivery as mod

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
    assert mod.SCOPE == 'PARTIAL: resend-until-acked simulation over supplied outcomes, no real network'
    assert len(mod.NOT_CLAIMED) >= 4 and 'timers' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(outs, mx):
    """Independent: index of first True and the attempt budget."""
    first = outs.index(True) if True in outs else None
    budget = min(mx, len(outs))
    if first is not None and first + 1 <= budget:
        n, st = first + 1, 'acked'
    elif len(outs) >= mx:
        n, st = mx, 'gave_up'
    else:
        n, st = len(outs), 'pending'
    return {'status': st, 'attempts': n, 'copies': n, 'duplicates': n - 1 if n else 0}


def _core(m):
    F, Tr = False, True
    assert m.at_least_once_delivery([]) == {'status': 'pending', 'attempts': 0, 'copies': 0, 'duplicates': 0}
    assert m.at_least_once_delivery([Tr]) == {'status': 'acked', 'attempts': 1, 'copies': 1, 'duplicates': 0}
    assert m.at_least_once_delivery([F, Tr]) == {'status': 'acked', 'attempts': 2, 'copies': 2, 'duplicates': 1}
    assert m.at_least_once_delivery([F, F, Tr]) == {'status': 'acked', 'attempts': 3, 'copies': 3, 'duplicates': 2}
    # default max 3: a fourth attempt is never made
    assert m.at_least_once_delivery([F, F, F, Tr]) == {'status': 'gave_up', 'attempts': 3, 'copies': 3, 'duplicates': 2}
    assert m.at_least_once_delivery([F, F, F, Tr], 4) == {'status': 'acked', 'attempts': 4, 'copies': 4, 'duplicates': 3}
    assert m.at_least_once_delivery([F, F, Tr], 2) == {'status': 'gave_up', 'attempts': 2, 'copies': 2, 'duplicates': 1}
    assert m.at_least_once_delivery([F]) == {'status': 'pending', 'attempts': 1, 'copies': 1, 'duplicates': 0}
    assert m.at_least_once_delivery([F, F]) == {'status': 'pending', 'attempts': 2, 'copies': 2, 'duplicates': 1}
    assert m.at_least_once_delivery([F], 1) == {'status': 'gave_up', 'attempts': 1, 'copies': 1, 'duplicates': 0}
    assert m.at_least_once_delivery([Tr, F, F], 1)['status'] == 'acked'
    assert m.at_least_once_delivery((F, F, F, F, F, F, F, F, F, Tr), 10) == {'status': 'acked', 'attempts': 10, 'copies': 10, 'duplicates': 9}
    assert m.at_least_once_delivery([F] * 10, 10)['status'] == 'gave_up'
    assert m.at_least_once_delivery([F] * 9, 10)['status'] == 'pending'
    assert m.at_least_once_delivery([F] * 10)['attempts'] == 3
    assert m.at_least_once_delivery([F, Tr, Tr, F])['attempts'] == 2
    for mx in range(1, 11):
        for n in range(0, 11):
            for pos in [None] + list(range(n)):
                outs = [i == pos for i in range(n)]
                assert m.at_least_once_delivery(outs, mx) == _oracle(outs, mx), (outs, mx)
    rng = random.Random(654)
    for _ in range(300):
        outs = [rng.random() < .3 for _ in range(rng.randint(0, 10))]
        assert m.at_least_once_delivery(outs) == _oracle(outs, 3)


def _late(m):
    AO = 'ack_outcomes must be a list or tuple'
    SZ = 'ack_outcomes must contain at most 10 entries'
    MA = 'max_attempts must be a nonbool integer between 1 and 10'
    OB = 'each outcome must be a bool'
    for bad in ('ab', None, 5, {}, L([True]), T([True]), L(), T()):
        _raises(TypeError, AO, m.at_least_once_delivery, bad)
    _raises(TypeError, AO, m.at_least_once_delivery, L([True] * 11))
    _raises(ValueError, SZ, m.at_least_once_delivery, [True] * 11)
    assert m.at_least_once_delivery([False] * 10)['attempts'] == 3
    for bad in (0, 11, -1, True, False, 1.0, '1', None, I(3), LyingI(3), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MA, m.at_least_once_delivery, [True], bad)
    assert m.at_least_once_delivery([False], 1)['status'] == 'gave_up' and m.at_least_once_delivery([False], 10)['status'] == 'pending'
    for bad in (1, 0, None, 'True', I(1), [True], 1.0, (True,)):
        _raises(ValueError, OB, m.at_least_once_delivery, [bad])
        _raises(ValueError, OB, m.at_least_once_delivery, [True, bad])             # validated even after the ack
        _raises(ValueError, OB, m.at_least_once_delivery, [False, False, False, bad])   # and after the give-up
    # order: type, size, max_attempts, then outcomes
    _raises(TypeError, AO, m.at_least_once_delivery, L([1]), I(1))
    _raises(ValueError, SZ, m.at_least_once_delivery, [1] * 11, I(1))
    _raises(ValueError, MA, m.at_least_once_delivery, [1], I(1))
    _raises(ValueError, OB, m.at_least_once_delivery, [1], 3)


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


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
    ("type(ack_outcomes) not in (list, tuple)", "not isinstance(ack_outcomes, (list, tuple))"),
    ("len(ack_outcomes) > MAX_OUTCOMES", "len(ack_outcomes) >= MAX_OUTCOMES"),
    ("MAX_OUTCOMES = 10", "MAX_OUTCOMES = 11"),
    ("max_attempts=3", "max_attempts=2"),
    ("max_attempts=3", "max_attempts=4"),
    ("type(max_attempts) is not int or not 1 <= max_attempts <= 10", "not isinstance(max_attempts, int) or not 1 <= max_attempts <= 10"),
    ("type(max_attempts) is not int or not 1 <= max_attempts <= 10", "isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 10"),
    ("not 1 <= max_attempts <= 10", "not 0 <= max_attempts <= 10"),
    ("not 1 <= max_attempts <= 10", "not 1 <= max_attempts < 10"),
    ("not 1 <= max_attempts <= 10", "not 1 <= max_attempts <= 11"),
    ("type(o) is not bool", "not isinstance(o, (bool, int))"),
    ("status = 'pending'\n    for", "status = 'gave_up'\n    for"),
    ("attempts += 1", "attempts += 2"),
    ("if o:", "if not o:"),
    ("status = 'acked'", "status = 'gave_up'"),
    ("if attempts == max_attempts:", "if attempts >= max_attempts + 1:"),
    ("if attempts == max_attempts:", "if attempts == max_attempts - 1:"),
    ("status = 'gave_up'\n            break", "status = 'pending'\n            break"),
    ("'copies': attempts", "'copies': attempts + 1"),
    ("max(attempts - 1, 0)", "attempts"),
    ("max(attempts - 1, 0)", "attempts - 1"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

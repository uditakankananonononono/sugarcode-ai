import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import exactly_once_apply as mod

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
    assert mod.SCOPE == 'PARTIAL: deduplicated application of supplied deliveries, no real broker'
    assert len(mod.NOT_CLAIMED) >= 4 and 'real brokers' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(ds, start):
    """Independent: index of first occurrence per delivery."""
    firsts = [i for i, (k, _) in enumerate(ds) if all(ds[j][0] != k for j in range(i))]
    return {'balance': start + sum(ds[i][1] for i in firsts), 'applied': [ds[i][0] for i in firsts],
            'duplicates': len(ds) - len(firsts), 'flags': [i in firsts for i in range(len(ds))]}


def _core(m):
    assert m.exactly_once_apply([]) == {'balance': 0, 'applied': [], 'duplicates': 0, 'flags': []}
    assert m.exactly_once_apply([], 7)['balance'] == 7
    r = m.exactly_once_apply([(1, 10), (2, -5), (1, 10), (3, 0), (2, -5), (1, 10)], 100)
    assert r == {'balance': 105, 'applied': [1, 2, 3], 'duplicates': 3, 'flags': [True, True, False, True, False, False]}
    assert m.exactly_once_apply([(5, 3), (4, 3)]) == {'balance': 6, 'applied': [5, 4], 'duplicates': 0, 'flags': [True, True]}
    assert m.exactly_once_apply([(5, 3), (5, 3)]) == {'balance': 3, 'applied': [5], 'duplicates': 1, 'flags': [True, False]}
    assert m.exactly_once_apply([[0, -100], (99, 100)], -1000)['balance'] == -1000
    assert m.exactly_once_apply([(0, -100)], -1000)['balance'] == -1100
    assert m.exactly_once_apply([(99, 100)], 1000)['balance'] == 1100
    assert m.exactly_once_apply([(1, 4), (2, 6)], 10)['balance'] == 20 and m.exactly_once_apply(((1, 4), (2, 6)))['balance'] == 10  # start default 0
    assert m.exactly_once_apply([(i, 1) for i in range(40)])['balance'] == 40
    assert m.exactly_once_apply([(1, 1)] * 40) == {'balance': 1, 'applied': [1], 'duplicates': 39, 'flags': [True] + [False] * 39}
    assert m.exactly_once_apply([(1, 0), (1, 0)])['flags'] == [True, False]
    rng = random.Random(653)
    for _ in range(600):
        ids = {}
        ds = []
        for _k in range(rng.randint(0, 40)):
            k = rng.randint(0, 9)
            ids.setdefault(k, rng.randint(-100, 100))
            ds.append((k, ids[k]))
        st = rng.randint(-1000, 1000)
        assert m.exactly_once_apply(ds, st) == _oracle(ds, st), (ds, st)
        assert m.exactly_once_apply(ds) == _oracle(ds, 0)


def _late(m):
    DL = 'deliveries must be a list or tuple'
    SZ = 'deliveries must contain at most 40 entries'
    ST = 'start must be a nonbool integer between -1000 and 1000'
    PR = 'each delivery must be a (msg_id, delta) pair'
    MI = 'msg_id must be a nonbool integer between 0 and 99'
    DT = 'delta must be a nonbool integer between -100 and 100'
    CH = 'a known msg_id came again with a different delta'
    ok = (1, 1)
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, DL, m.exactly_once_apply, bad)
    _raises(TypeError, DL, m.exactly_once_apply, L([ok] * 41))
    _raises(ValueError, SZ, m.exactly_once_apply, [ok] * 41)
    for bad in (-1001, 1001, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, ST, m.exactly_once_apply, [ok], bad)
    for K in (L, T):
        for bad in (K(ok), K((1,))):
            _raises(ValueError, PR, m.exactly_once_apply, [bad])
            _raises(ValueError, PR, m.exactly_once_apply, [ok, bad])
    for bad in ('ab', None, 5, (1,), (1, 1, 1), ()):
        _raises(ValueError, PR, m.exactly_once_apply, [bad])
        _raises(ValueError, PR, m.exactly_once_apply, [ok, bad])
    for bad in (-1, 100, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MI, m.exactly_once_apply, [(bad, 1)])
        _raises(ValueError, MI, m.exactly_once_apply, [ok, (bad, 1)])
    for bad in (-101, 101, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, DT, m.exactly_once_apply, [(2, bad)])
        _raises(ValueError, DT, m.exactly_once_apply, [ok, (2, bad)])
    _raises(ValueError, CH, m.exactly_once_apply, [(1, 1), (1, 2)])
    _raises(ValueError, CH, m.exactly_once_apply, [(1, 1), (2, 2), (1, 0)])
    # order: type, size, start, then per delivery: shape, id, delta, change
    _raises(TypeError, DL, m.exactly_once_apply, L([1]), I(1))
    _raises(ValueError, SZ, m.exactly_once_apply, [1] * 41, I(1))
    _raises(ValueError, ST, m.exactly_once_apply, [1], I(1))
    _raises(ValueError, PR, m.exactly_once_apply, [1], 5)
    _raises(ValueError, MI, m.exactly_once_apply, [(I(1), I(1))])
    _raises(ValueError, DT, m.exactly_once_apply, [(1, I(1))])
    _raises(ValueError, DT, m.exactly_once_apply, [ok, (1, 101)])            # range before the changed-delta check
    _raises(ValueError, CH, m.exactly_once_apply, [ok, (1, 2), (I(1), 1)])   # change error stops before the later bad row


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
    ("type(deliveries) not in (list, tuple)", "not isinstance(deliveries, (list, tuple))"),
    ("len(deliveries) > MAX_DELIVERIES", "len(deliveries) >= MAX_DELIVERIES"),
    ("MAX_DELIVERIES = 40", "MAX_DELIVERIES = 41"),
    ("start=0", "start=1"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(start, -1000, 1000", "_int(start, -999, 1000"),
    ("_int(start, -1000, 1000", "_int(start, -1000, 999"),
    ("_int(mid, 0, 99", "_int(mid, 1, 99"),
    ("_int(mid, 0, 99", "_int(mid, 0, 100"),
    ("_int(mid, 0, 99", "_int(mid, 0, 98"),
    ("_int(delta, -100, 100", "_int(delta, -99, 100"),
    ("_int(delta, -100, 100", "_int(delta, -100, 101"),
    ("type(d) not in (list, tuple) or len(d) != 2", "not isinstance(d, (list, tuple)) or len(d) != 2"),
    ("or len(d) != 2", "or len(d) > 2"),
    ("or len(d) != 2", "or len(d) < 2"),
    ("if seen[mid] != delta:", "if False:"),
    ("seen[mid] = delta\n            flags.append(True)", "seen[mid] = delta\n            flags.append(False)"),
    ("flags.append(False)\n        else:", "flags.append(True)\n        else:"),
    ("'balance': start + sum(seen.values())", "'balance': sum(seen.values())"),
    ("'balance': start + sum(seen.values())", "'balance': start + sum(d[1] for d in deliveries)"),
    ("'applied': list(seen)", "'applied': sorted(seen)"),
    ("flags.count(False)", "flags.count(True)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import sidecar_chain as mod

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
    assert mod.SCOPE == 'PARTIAL: ordered sidecar steps over one supplied value, no real proxy'
    assert len(mod.NOT_CLAIMED) >= 4 and 'service meshes' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(v, steps):
    """Independent: operator-table fold."""
    import operator
    ops = {'add': operator.add, 'scale': operator.mul, 'cap': lambda a, b: a if a < b else b, 'floor': lambda a, b: a if a > b else b}
    tr = []
    ch = 0
    for k, a in steps:
        nv = ops[k](v, a)
        ch += nv != v
        v = nv
        tr.append(v)
    return {'result': v, 'trace': tr, 'changed': ch}


def _core(m):
    assert m.sidecar_chain(5, []) == {'result': 5, 'trace': [], 'changed': 0}
    assert m.sidecar_chain(5, [('add', 3)]) == {'result': 8, 'trace': [8], 'changed': 1}
    assert m.sidecar_chain(5, [('scale', 3)]) == {'result': 15, 'trace': [15], 'changed': 1}
    assert m.sidecar_chain(5, [('cap', 3)]) == {'result': 3, 'trace': [3], 'changed': 1}
    assert m.sidecar_chain(5, [('cap', 9)]) == {'result': 5, 'trace': [5], 'changed': 0}
    assert m.sidecar_chain(5, [('floor', 9)]) == {'result': 9, 'trace': [9], 'changed': 1}
    assert m.sidecar_chain(5, [('floor', 3)]) == {'result': 5, 'trace': [5], 'changed': 0}
    assert m.sidecar_chain(5, [('cap', 5), ('floor', 5), ('add', 0), ('scale', 1)])['changed'] == 0
    assert m.sidecar_chain(-7, [('scale', -2), ('add', -4), ('cap', 5), ('floor', -100)]) == {'result': 5, 'trace': [14, 10, 5, 5], 'changed': 3}
    # order matters
    assert m.sidecar_chain(2, [('add', 3), ('scale', 4)])['result'] == 20
    assert m.sidecar_chain(2, [('scale', 4), ('add', 3)])['result'] == 11
    assert m.sidecar_chain(2, [['scale', 0], ('add', 0)]) == {'result': 0, 'trace': [0, 0], 'changed': 1}
    assert m.sidecar_chain(1000, [('scale', 100)] * 8)['result'] == 1000 * 100 ** 8
    assert m.sidecar_chain(-1000, [('add', -100)] * 8)['result'] == -1800
    assert m.sidecar_chain(0, (('add', 100), ('floor', -100)))['trace'] == [100, 100]
    rng = random.Random(659)
    for _ in range(600):
        v = rng.randint(-1000, 1000)
        st = [(rng.choice(['add', 'scale', 'cap', 'floor']), rng.randint(-100, 100)) for _ in range(rng.randint(0, 8))]
        assert m.sidecar_chain(v, st) == _oracle(v, st), (v, st)


def _late(m):
    VL = 'value must be a nonbool integer between -1000 and 1000'
    ST = 'steps must be a list or tuple'
    SZ = 'steps must contain at most 8 entries'
    PR = 'each step must be a (kind, arg) pair'
    KD = 'kind must be add, scale, cap or floor'
    AG = 'arg must be a nonbool integer between -100 and 100'
    ok = ('add', 1)
    for bad in (-1001, 1001, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, VL, m.sidecar_chain, bad, [])
    assert m.sidecar_chain(-1000, [])['result'] == -1000 and m.sidecar_chain(1000, [])['result'] == 1000
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, ST, m.sidecar_chain, 1, bad)
    _raises(TypeError, ST, m.sidecar_chain, 1, L([ok] * 9))
    _raises(ValueError, SZ, m.sidecar_chain, 1, [ok] * 9)
    assert m.sidecar_chain(1, [ok] * 8)['result'] == 9
    for K in (L, T):
        for bad in (K(ok), K(('add',))):
            _raises(ValueError, PR, m.sidecar_chain, 1, [bad])
            _raises(ValueError, PR, m.sidecar_chain, 1, [ok, bad])
    for bad in ('ab', None, 5, ('add',), ('add', 1, 1), ()):
        _raises(ValueError, PR, m.sidecar_chain, 1, [bad])
        _raises(ValueError, PR, m.sidecar_chain, 1, [ok, bad])
    for bad in ('', 'ADD', 'sub', None, 5, S('add'), LyingS('add'), b'add', ['add']):
        _raises(ValueError, KD, m.sidecar_chain, 1, [(bad, 1)])
        _raises(ValueError, KD, m.sidecar_chain, 1, [ok, (bad, 1)])
    for bad in (-101, 101, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, AG, m.sidecar_chain, 1, [('add', bad)])
        _raises(ValueError, AG, m.sidecar_chain, 1, [ok, ('add', bad)])
    assert m.sidecar_chain(0, [('add', -100), ('add', 100)])['result'] == 0
    # order: value, steps type, steps size, then each step: shape, kind, arg
    _raises(ValueError, VL, m.sidecar_chain, I(1), L([1]))
    _raises(TypeError, ST, m.sidecar_chain, 1, L([1]))
    _raises(ValueError, SZ, m.sidecar_chain, 1, [1] * 9)
    _raises(ValueError, PR, m.sidecar_chain, 1, [1])
    _raises(ValueError, KD, m.sidecar_chain, 1, [(S('add'), I(1))])
    _raises(ValueError, AG, m.sidecar_chain, 1, [('add', I(1)), (5, 5)])


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
    def __hash__(self): return hash('add')


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
    ("_int(value, -1000, 1000", "_int(value, -999, 1000"),
    ("_int(value, -1000, 1000", "_int(value, -1000, 999"),
    ("_int(arg, -100, 100", "_int(arg, -99, 100"),
    ("_int(arg, -100, 100", "_int(arg, -100, 99"),
    ("type(steps) not in (list, tuple)", "not isinstance(steps, (list, tuple))"),
    ("len(steps) > MAX_STEPS", "len(steps) >= MAX_STEPS"),
    ("MAX_STEPS = 8", "MAX_STEPS = 9"),
    ("type(s) not in (list, tuple) or len(s) != 2", "not isinstance(s, (list, tuple)) or len(s) != 2"),
    ("or len(s) != 2", "or len(s) > 2"),
    ("or len(s) != 2", "or len(s) < 2"),
    ("type(kind) is not str or kind not in KINDS", "not isinstance(kind, str) or kind not in KINDS"),
    ("KINDS = ('add', 'scale', 'cap', 'floor')", "KINDS = ('add', 'scale', 'cap')"),
    ("if kind == 'add':", "if kind != 'add':"),
    ("new = cur + arg", "new = cur - arg"),
    ("new = cur * arg", "new = cur + arg * 2"),
    ("new = min(cur, arg)", "new = max(cur, arg)"),
    ("new = max(cur, arg)", "new = min(cur, arg)"),
    ("elif kind == 'cap':", "elif kind == 'floor':"),
    ("if new != cur:", "if new > cur:"),
    ("if new != cur:", "if True:"),
    ("cur = new\n", "cur = cur\n"),
    ("trace.append(cur)", "trace.append(arg)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

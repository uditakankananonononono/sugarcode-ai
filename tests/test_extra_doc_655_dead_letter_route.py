import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import dead_letter_route as mod

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
    assert mod.SCOPE == 'PARTIAL: dead letter routing of supplied failure counts, no real queue'
    assert len(mod.NOT_CLAIMED) >= 4 and 'redrive' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(ms, mx, cap):
    """Independent: filter passes, then slice the dead list."""
    deliv = [i for i, f in ms if f == 0]
    retry = [i for i, f in ms if 0 < f < mx]
    dead = [i for i, f in ms if f >= mx]
    cut = max(len(dead) - cap, 0)
    return {'delivered': deliv, 'retry': retry, 'dlq': dead[cut:], 'dropped': dead[:cut]}


def _core(m):
    assert m.dead_letter_route([]) == {'delivered': [], 'retry': [], 'dlq': [], 'dropped': []}
    r = m.dead_letter_route([('a', 0), ('b', 1), ('c', 2), ('d', 3), ('e', 9)])
    assert r == {'delivered': ['a'], 'retry': ['b', 'c'], 'dlq': ['d', 'e'], 'dropped': []}
    assert m.dead_letter_route([('a', 2)], 2) == {'delivered': [], 'retry': [], 'dlq': ['a'], 'dropped': []}
    assert m.dead_letter_route([('a', 2)], 3)['retry'] == ['a']
    assert m.dead_letter_route([('a', 1)], 1)['dlq'] == ['a'] and m.dead_letter_route([('a', 0)], 1)['delivered'] == ['a']
    assert m.dead_letter_route([('a', 20)], 20)['dlq'] == ['a'] and m.dead_letter_route([('a', 19)], 20)['retry'] == ['a']
    # default capacity 5: the sixth dead message pushes out the first, the seventh the second
    six = [('d%d' % i, 5) for i in range(7)]
    assert m.dead_letter_route(six) == {'delivered': [], 'retry': [], 'dlq': ['d2', 'd3', 'd4', 'd5', 'd6'], 'dropped': ['d0', 'd1']}
    assert m.dead_letter_route(six[:5])['dropped'] == []
    assert m.dead_letter_route(six[:6])['dlq'] == ['d1', 'd2', 'd3', 'd4', 'd5']
    assert m.dead_letter_route(six, 3, 2) == {'delivered': [], 'retry': [], 'dlq': ['d5', 'd6'], 'dropped': ['d0', 'd1', 'd2', 'd3', 'd4']}
    assert m.dead_letter_route(six, 3, 10)['dlq'] == ['d%d' % i for i in range(7)]
    # default max_failures 3: failures 2 retry, 3 dead
    assert m.dead_letter_route([('x', 2), ('y', 3)]) == {'delivered': [], 'retry': ['x'], 'dlq': ['y'], 'dropped': []}
    assert m.dead_letter_route([['x', 2], ('y', 3)], 4)['retry'] == ['x', 'y']
    big = [('m%d' % i, i) for i in range(20)]
    assert m.dead_letter_route(tuple(big), 10, 10)['dlq'] == ['m%d' % i for i in range(10, 20)]
    assert m.dead_letter_route([('n' * 12, 0)])['delivered'] == ['n' * 12]
    rng = random.Random(655)
    for _ in range(600):
        ms = [('i%d' % k, rng.choice([0, 1, 2, 3, 4, 20, rng.randint(0, 20)])) for k in range(rng.randint(0, 20))]
        mx, cap = rng.randint(1, 20), rng.randint(1, 10)
        assert m.dead_letter_route(ms, mx, cap) == _oracle(ms, mx, cap), (ms, mx, cap)
        assert m.dead_letter_route(ms) == _oracle(ms, 3, 5)


def _late(m):
    MS = 'messages must be a list or tuple'
    SZ = 'messages must contain at most 20 entries'
    MF = 'max_failures must be a nonbool integer between 1 and 20'
    DC = 'dlq_capacity must be a nonbool integer between 1 and 10'
    PR = 'each message must be a (msg_id, failures) pair'
    ID = 'msg_id must be a string of 1 to 12 characters'
    DU = 'duplicate msg_id'
    FL = 'failures must be a nonbool integer between 0 and 20'
    ok = ('a', 1)
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, MS, m.dead_letter_route, bad)
    _raises(TypeError, MS, m.dead_letter_route, L([ok] * 21))
    _raises(ValueError, SZ, m.dead_letter_route, [ok] * 21)
    assert m.dead_letter_route([('p%d' % i, 0) for i in range(20)])['delivered'][-1] == 'p19'
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(3), LyingI(3), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MF, m.dead_letter_route, [ok], bad)
    for bad in (0, 11, -1, True, False, 1.0, '1', None, I(3), LyingI(3), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, DC, m.dead_letter_route, [ok], 3, bad)
    assert m.dead_letter_route([ok], 1, 1) and m.dead_letter_route([ok], 20, 10)
    for K in (L, T):
        for bad in (K(ok), K(('a',))):
            _raises(ValueError, PR, m.dead_letter_route, [bad])
            _raises(ValueError, PR, m.dead_letter_route, [ok, bad])
    for bad in ('ab', None, 5, ('a',), ('a', 1, 1), ()):
        _raises(ValueError, PR, m.dead_letter_route, [bad])
        _raises(ValueError, PR, m.dead_letter_route, [ok, bad])
    for bad in ('', 'x' * 13, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, ID, m.dead_letter_route, [(bad, 1)])
        _raises(ValueError, ID, m.dead_letter_route, [ok, (bad, 1)])
    _raises(ValueError, DU, m.dead_letter_route, [ok, ('a', 2)])
    _raises(ValueError, DU, m.dead_letter_route, [ok, ('b', 1), ('a', 1)])
    for bad in (-1, 21, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, FL, m.dead_letter_route, [('b', bad)])
        _raises(ValueError, FL, m.dead_letter_route, [ok, ('b', bad)])
    # order: type, size, max_failures, dlq_capacity, then per message: shape, id, duplicate, failures
    _raises(TypeError, MS, m.dead_letter_route, L([1]), I(1), I(1))
    _raises(ValueError, SZ, m.dead_letter_route, [1] * 21, I(1), I(1))
    _raises(ValueError, MF, m.dead_letter_route, [1], I(1), I(1))
    _raises(ValueError, DC, m.dead_letter_route, [1], 3, I(1))
    _raises(ValueError, PR, m.dead_letter_route, [1], 3, 5)
    _raises(ValueError, ID, m.dead_letter_route, [(5, I(1))])
    _raises(ValueError, DU, m.dead_letter_route, [ok, ('a', I(1))])
    _raises(ValueError, FL, m.dead_letter_route, [('b', I(1)), (5, 1)])


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
    def __hash__(self): return hash('b')


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
    ("type(messages) not in (list, tuple)", "not isinstance(messages, (list, tuple))"),
    ("len(messages) > MAX_MESSAGES", "len(messages) >= MAX_MESSAGES"),
    ("MAX_MESSAGES = 20", "MAX_MESSAGES = 21"),
    ("max_failures=3", "max_failures=2"),
    ("max_failures=3", "max_failures=4"),
    ("dlq_capacity=5", "dlq_capacity=4"),
    ("dlq_capacity=5", "dlq_capacity=6"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(max_failures, 1, 20", "_int(max_failures, 0, 20"),
    ("_int(max_failures, 1, 20", "_int(max_failures, 1, 21"),
    ("_int(dlq_capacity, 1, 10", "_int(dlq_capacity, 0, 10"),
    ("_int(dlq_capacity, 1, 10", "_int(dlq_capacity, 1, 11"),
    ("_int(failures, 0, 20", "_int(failures, 1, 20"),
    ("_int(failures, 0, 20", "_int(failures, 0, 21"),
    ("type(m) not in (list, tuple) or len(m) != 2", "not isinstance(m, (list, tuple)) or len(m) != 2"),
    ("or len(m) != 2", "or len(m) > 2"),
    ("or len(m) != 2", "or len(m) < 2"),
    ("type(mid) is not str or not 1 <= len(mid) <= 12", "not isinstance(mid, str) or not 1 <= len(mid) <= 12"),
    ("not 1 <= len(mid) <= 12", "not 0 <= len(mid) <= 12"),
    ("not 1 <= len(mid) <= 12", "not 1 <= len(mid) < 12"),
    ("not 1 <= len(mid) <= 12", "not 1 <= len(mid) <= 13"),
    ("if mid in seen:", "if False:"),
    ("if failures == 0:", "if failures <= 1:"),
    ("elif failures < max_failures:", "elif failures <= max_failures:"),
    ("if len(dlq) > dlq_capacity:", "if len(dlq) >= dlq_capacity:"),
    ("dropped.append(dlq.pop(0))", "dropped.append(dlq.pop())"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

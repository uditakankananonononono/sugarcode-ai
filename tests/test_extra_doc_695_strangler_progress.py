import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import strangler_progress as mod

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
    assert mod.SCOPE == 'PARTIAL: count-based cutover summary of supplied routes, no traffic is routed'
    assert len(mod.NOT_CLAIMED) == 5 and 'legacy shutdown' in mod.NOT_CLAIMED and 'rollback safety' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(rs):
    ts = [t for _, t in rs]
    n = len(rs)
    new = ts.count('new')
    first = None
    for p, t in rs:
        if t == 'legacy':
            first = p
            break
    return {'new': new, 'legacy': ts.count('legacy'), 'percent': __import__('math').floor(__import__('fractions').Fraction(new * 100, n)),
            'phase': 'not_started' if new == 0 else ('complete' if new == n else 'strangling'), 'next_route': first}


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
    def __hash__(self): return hash('a')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def _core(m):
    f = m.strangler_progress
    assert f([('a', 'legacy')]) == {'new': 0, 'legacy': 1, 'percent': 0, 'phase': 'not_started', 'next_route': 'a'}
    assert f([('a', 'new')]) == {'new': 1, 'legacy': 0, 'percent': 100, 'phase': 'complete', 'next_route': None}
    assert f([('a', 'new'), ('b', 'legacy')]) == {'new': 1, 'legacy': 1, 'percent': 50, 'phase': 'strangling', 'next_route': 'b'}
    assert f([('a', 'new'), ('b', 'new'), ('c', 'legacy')])['percent'] == 66
    assert f([('a', 'new'), ('b', 'legacy'), ('c', 'legacy')])['percent'] == 33
    assert f([('a', 'legacy'), ('b', 'new'), ('c', 'legacy')])['next_route'] == 'a'
    assert f([('a', 'new'), ('b', 'new'), ('c', 'legacy'), ('d', 'legacy')])['next_route'] == 'c'
    assert f((['x', 'new'], ('y', 'legacy')))['legacy'] == 1
    assert f([('a', 'new')] * 1)['phase'] == 'complete'
    assert f([('a', 'legacy'), ('b', 'legacy')])['phase'] == 'not_started'
    assert f([('x' * 16, 'legacy')])['next_route'] == 'x' * 16
    # default max_routes is 8
    r8 = [(chr(97 + i), 'new') for i in range(8)]
    f(r8)
    _raises(ValueError, 'routes must contain 1 to max_routes entries', f, r8 + [('i', 'new')])
    assert f(r8 + [('i', 'new')], 9)['new'] == 9
    assert f([(chr(97 + i), 'legacy') for i in range(20)], 20)['legacy'] == 20
    _raises(ValueError, 'routes must contain 1 to max_routes entries', f, r8[:3], 2)
    f(r8[:2], 2)
    assert f([(chr(97 + i), 'new' if i < 7 else 'legacy') for i in range(7 + 1)])['percent'] == 87
    assert f([(chr(97 + i), 'new' if i < 1 else 'legacy') for i in range(6)], 6)['percent'] == 16
    import itertools
    for n in range(1, 7):
        for combo in itertools.product(('legacy', 'new'), repeat=n):
            rs = [(chr(97 + i), t) for i, t in enumerate(combo)]
            assert f(rs) == _oracle(rs), rs


def _late(m):
    f = m.strangler_progress
    MR = 'max_routes must be a nonbool integer between 1 and 20'
    RT = 'routes must be a list or tuple'
    RS = 'routes must contain 1 to max_routes entries'
    RP = 'each route must be a (path, target) pair'
    PA = 'each path must be a string of 1 to 16 characters'
    TG = 'target must be legacy or new'
    PD = 'paths must be distinct'
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MR, f, [('a', 'new')], bad)
    f([('a', 'new')], 1)
    f([('a', 'new')], 20)
    for bad in ('ab', None, 5, {}, L([('a', 'new')]), T([('a', 'new')]), L(), T()):
        _raises(TypeError, RT, f, bad)
    _raises(ValueError, RS, f, [])
    for bad in ('ab', None, 5, ('a',), ('a', 'new', 1), (), {'a': 'new'}, L(['a', 'new']), T(('a', 'new'))):
        _raises(ValueError, RP, f, [bad])
        _raises(ValueError, RP, f, [('b', 'new'), bad])
    for bad in ('', 'x' * 17, None, 5, True, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, PA, f, [(bad, 'new')])
        _raises(ValueError, PA, f, [('b', 'new'), (bad, 'new')])
    for bad in ('', 'NEW', 'old', None, 5, True, S('new'), LyingS('new'), b'new', ['new']):
        _raises(ValueError, TG, f, [('a', bad)])
        _raises(ValueError, TG, f, [('b', 'new'), ('a', bad)])
    _raises(ValueError, PD, f, [('a', 'new'), ('a', 'legacy')])
    _raises(ValueError, PD, f, [('a', 'new'), ('b', 'new'), ('a', 'new')])
    # validation order
    _raises(ValueError, MR, f, None, I(1))
    _raises(TypeError, RT, f, None)
    _raises(ValueError, RS, f, [1] * 9)
    _raises(ValueError, RP, f, [1])
    _raises(ValueError, PA, f, [(1, 1)])
    _raises(ValueError, TG, f, [('a', 1), ('a', 1)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_routes=8", "max_routes=9"),
    ("max_routes=8", "max_routes=7"),
    ("type(max_routes) is not int or not 1 <= max_routes <= 20", "not isinstance(max_routes, int) or not 1 <= max_routes <= 20"),
    ("type(max_routes) is not int or not 1 <= max_routes <= 20", "isinstance(max_routes, bool) or not isinstance(max_routes, int) or not 1 <= max_routes <= 20"),
    ("not 1 <= max_routes <= 20", "not 0 <= max_routes <= 20"),
    ("not 1 <= max_routes <= 20", "not 1 <= max_routes < 20"),
    ("not 1 <= max_routes <= 20", "not 1 <= max_routes <= 21"),
    ("type(routes) not in (list, tuple)", "not isinstance(routes, (list, tuple))"),
    ("not 1 <= len(routes) <= max_routes", "not 0 <= len(routes) <= max_routes"),
    ("not 1 <= len(routes) <= max_routes", "not 1 <= len(routes) < max_routes"),
    ("type(r) not in (list, tuple) or len(r) != 2", "not isinstance(r, (list, tuple)) or len(r) != 2"),
    ("type(r) not in (list, tuple) or len(r) != 2", "type(r) not in (list, tuple) or len(r) > 2"),
    ("type(r) not in (list, tuple) or len(r) != 2", "type(r) not in (list, tuple) or len(r) < 2"),
    ("type(path) is not str or not 1 <= len(path) <= 16", "not isinstance(path, str) or not 1 <= len(path) <= 16"),
    ("type(path) is not str or not 1 <= len(path) <= 16", "type(path) is not str or not 0 <= len(path) <= 16"),
    ("type(path) is not str or not 1 <= len(path) <= 16", "type(path) is not str or not 1 <= len(path) < 16"),
    ("type(path) is not str or not 1 <= len(path) <= 16", "type(path) is not str or not 1 <= len(path) <= 17"),
    ("type(target) is not str or target not in ('legacy', 'new')", "not isinstance(target, str) or target not in ('legacy', 'new')"),
    ("type(target) is not str or target not in ('legacy', 'new')", "type(target) is not str or target not in ('legacy', 'new', 'old')"),
    ("len({p for p, _ in rows}) != len(rows)", "False"),
    ("new = sum(1 for _, t in rows if t == 'new')", "new = sum(1 for _, t in rows if t != 'legacy') - 1"),
    ("legacy = len(rows) - new", "legacy = len(rows)"),
    ("if new == 0:", "if new == 1:"),
    ("elif legacy == 0:", "elif legacy <= 1:"),
    ("phase = 'strangling'", "phase = 'complete'"),
    ("if t == 'legacy'), None)", "if t == 'new'), None)"),
    ("new * 100 // len(rows)", "(new * 100 + len(rows) // 2) // len(rows)"),
    ("new * 100 // len(rows)", "new * 100 // (len(rows) + 1)"),
    ("new * 100 // len(rows)", "new * 10 // len(rows) * 10"),
    ("new * 100 // len(rows)", "round(new * 100 / len(rows))"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

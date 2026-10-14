import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import feature_flag_rules as mod

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
    assert mod.SCOPE == 'PARTIAL: allow and deny list lookup over supplied flag rows, no rollouts or remote config'
    assert len(mod.NOT_CLAIMED) >= 4 and 'percentage rollouts' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(flags, flag, user):
    """Independent: truth table over (in deny, in allow, default)."""
    row = [r for r in flags if r[0] == flag][0]
    table = {(True, True): (False, 'denied'), (True, False): (False, 'denied'),
             (False, True): (True, 'allowed')}
    key = (user in row[2], user in row[1])
    if key in table:
        e, why = table[key]
        return {'enabled': e, 'reason': why}
    return {'enabled': row[3], 'reason': 'default'}


def _core(m):
    flags = [('beta', ['ann', 'bo'], ['bo', 'cy'], False), ('dark', [], [], True), ('off', ('x',), (), False)]
    assert m.flag_enabled(flags, 'beta', 'ann') == {'enabled': True, 'reason': 'allowed'}
    assert m.flag_enabled(flags, 'beta', 'bo') == {'enabled': False, 'reason': 'denied'}      # deny wins over allow
    assert m.flag_enabled(flags, 'beta', 'cy') == {'enabled': False, 'reason': 'denied'}
    assert m.flag_enabled(flags, 'beta', 'dee') == {'enabled': False, 'reason': 'default'}
    assert m.flag_enabled(flags, 'dark', 'ann') == {'enabled': True, 'reason': 'default'}
    assert m.flag_enabled(tuple(flags), 'off', 'x') == {'enabled': True, 'reason': 'allowed'}
    assert m.flag_enabled(flags, 'off', 'y') == {'enabled': False, 'reason': 'default'}
    d = [['d', [], ['u'], True], ['e', ['u'], [], False]]
    assert m.flag_enabled(d, 'd', 'u') == {'enabled': False, 'reason': 'denied'}              # deny beats a True default
    assert m.flag_enabled(d, 'e', 'u') == {'enabled': True, 'reason': 'allowed'}              # allow beats a False default
    assert m.flag_enabled(d, 'e', 'v') == {'enabled': False, 'reason': 'default'}
    assert m.flag_enabled([('f', ['u'], ['u'], True)], 'f', 'u')['reason'] == 'denied'
    assert m.flag_enabled([('f' * 16, ['u' * 16], [], False)], 'f' * 16, 'u' * 16)['enabled'] is True
    names = ['u%d' % i for i in range(10)]
    assert m.flag_enabled([('f', names, names[:0], False)], 'f', 'u9')['enabled'] is True
    assert m.flag_enabled([('f', names, names[:0], False)], 'f', 'u10')['enabled'] is False
    many = [('f%d' % i, [], [], i % 2 == 0) for i in range(30)]
    assert m.flag_enabled(many, 'f28', 'a')['enabled'] is True and m.flag_enabled(many, 'f29', 'a')['enabled'] is False
    assert m.flag_enabled(many, 'f0', 'a')['enabled'] is True and m.flag_enabled(many, 'f1', 'a')['enabled'] is False
    assert type(m.flag_enabled(flags, 'dark', 'a')['enabled']) is bool
    rng = random.Random(625)
    for _ in range(500):
        flags = []
        for i in range(rng.randint(1, 5)):
            users = ['a', 'b', 'c', 'd']
            flags.append(('f%d' % i, rng.sample(users, rng.randint(0, 3)), rng.sample(users, rng.randint(0, 3)), rng.random() < 0.5))
        f = rng.choice(flags)[0]
        u = rng.choice('abcde')
        assert m.flag_enabled(flags, f, u) == _oracle(flags, f, u), (flags, f, u)


def _late(m):
    FL = 'flags must be a list or tuple'
    SZ = 'flags must contain between 1 and 30 entries'
    FN = 'flag must be a string of 1 to 16 characters'
    UN = 'user must be a string of 1 to 16 characters'
    RW = 'each flag must be a (name, allow, deny, default) quadruple'
    NM = 'flag names must be strings of 1 to 16 characters'
    LT = 'allow and deny must be lists or tuples'
    HD = 'allow and deny must hold at most 10 unique names of 1 to 16 characters'
    DF = 'default must be a bool'
    good = ('f', ['a'], [], True)
    for bad in ('ab', None, 5, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, FL, m.flag_enabled, bad, 'f', 'a')
    _raises(TypeError, FL, m.flag_enabled, L([good] * 31), 'f', 'a')
    _raises(ValueError, SZ, m.flag_enabled, [], 'f', 'a')
    _raises(ValueError, SZ, m.flag_enabled, [('f%d' % i, [], [], True) for i in range(31)], 'f0', 'a')
    for bad in ('', 'x' * 17, None, 5, S('f'), LyingS('f')):
        _raises(ValueError, FN, m.flag_enabled, [good], bad, 'a')
        _raises(ValueError, UN, m.flag_enabled, [good], 'f', bad)
    for K in (L, T):
        for bad in (K(good), K(('f', [], []))):
            _raises(ValueError, RW, m.flag_enabled, [bad], 'f', 'a')
            _raises(ValueError, RW, m.flag_enabled, [good, bad], 'f', 'a')
    for bad in ('abcd', None, 5, ('f', [], []), ('f', [], [], True, 1), ()):
        _raises(ValueError, RW, m.flag_enabled, [bad], 'f', 'a')
        _raises(ValueError, RW, m.flag_enabled, [good, bad], 'f', 'a')
    for bad in ('', 'x' * 17, None, 5, S('g'), LyingS('g'), ['g']):
        _raises(ValueError, NM, m.flag_enabled, [(bad, [], [], True)], 'f', 'a')
        _raises(ValueError, NM, m.flag_enabled, [good, (bad, [], [], True)], 'f', 'a')
    for bad in ('abc', None, 5, {'a': 1}, L(['a']), T(['a']), L(), T(), {'a'}):
        _raises(ValueError, LT, m.flag_enabled, [('g', bad, [], True)], 'g', 'a')
        _raises(ValueError, LT, m.flag_enabled, [good, ('g', [], bad, True)], 'g', 'a')
    for bad in (['a', 'a'], [''], ['x' * 17], [None], [5], [S('a')], [LyingS('a')], ['u%d' % i for i in range(11)], ['a', S('a')]):
        _raises(ValueError, HD, m.flag_enabled, [('g', bad, [], True)], 'g', 'a')
        _raises(ValueError, HD, m.flag_enabled, [good, ('g', [], bad, True)], 'g', 'a')
        _raises(ValueError, HD, m.flag_enabled, [('g', bad, [], True)], 'g', 'a')
    for bad in (1, 0, None, 'x', 1.0, I(1), LyingI(1), [True]):
        _raises(ValueError, DF, m.flag_enabled, [('g', [], [], bad)], 'g', 'a')
        _raises(ValueError, DF, m.flag_enabled, [good, ('g', [], [], bad)], 'g', 'a')
    _raises(ValueError, 'duplicate flag name', m.flag_enabled, [good, good], 'f', 'a')
    _raises(ValueError, 'duplicate flag name', m.flag_enabled, [good, ('g', [], [], True), good], 'f', 'a')
    _raises(ValueError, 'unknown flag', m.flag_enabled, [good], 'g', 'a')
    _raises(ValueError, 'unknown flag', m.flag_enabled, [good], 'F', 'a')
    # order: flags, size, flag, user, rows (shape, name, allow, deny, default, duplicate), then unknown flag
    _raises(TypeError, FL, m.flag_enabled, L([1]), S('f'), S('a'))
    _raises(ValueError, SZ, m.flag_enabled, [], S('f'), S('a'))
    _raises(ValueError, FN, m.flag_enabled, [1], S('f'), S('a'))
    _raises(ValueError, UN, m.flag_enabled, [1], 'f', S('a'))
    _raises(ValueError, RW, m.flag_enabled, [1], 'f', 'a')
    _raises(ValueError, NM, m.flag_enabled, [(S('f'), L(), 1, 1)], 'f', 'a')
    _raises(ValueError, LT, m.flag_enabled, [('f', L(), 1, 1)], 'f', 'a')
    _raises(ValueError, LT, m.flag_enabled, [('f', [], L(), 1)], 'f', 'a')
    _raises(ValueError, DF, m.flag_enabled, [('f', [], [], 1), ('f', [], [], True)], 'f', 'a')
    _raises(ValueError, 'duplicate flag name', m.flag_enabled, [good, good], 'zz', 'a')
    _raises(ValueError, DF, m.flag_enabled, [good, ('zz', [], [], 1)], 'q', 'a')


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
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_flags_unchanged():
    flags = [('f', ['a'], [], False)]
    r = mod.flag_enabled(flags, 'f', 'a')
    r['reason'] = 'x'
    assert flags == [('f', ['a'], [], False)]
    assert mod.flag_enabled(flags, 'f', 'a') == {'enabled': True, 'reason': 'allowed'}


MUTANTS = [
    ("type(flags) not in (list, tuple)", "not isinstance(flags, (list, tuple))"),
    ("not 1 <= len(flags) <= MAX_FLAGS", "not 0 <= len(flags) <= MAX_FLAGS"),
    ("not 1 <= len(flags) <= MAX_FLAGS", "not 1 <= len(flags) < MAX_FLAGS"),
    ("MAX_FLAGS = 30", "MAX_FLAGS = 31"),
    ("MAX_USERS = 10", "MAX_USERS = 11"),
    ("MAX_USERS = 10", "MAX_USERS = 9"),
    ("type(v) is not str or not 1 <= len(v) <= 16", "not isinstance(v, str) or not 1 <= len(v) <= 16"),
    ("not 1 <= len(v) <= 16", "not 0 <= len(v) <= 16"),
    ("not 1 <= len(v) <= 16", "not 1 <= len(v) <= 17"),
    ("not 1 <= len(v) <= 16", "not 1 <= len(v) < 16"),
    ("if type(v) not in (list, tuple):", "if not isinstance(v, (list, tuple)):"),
    ("len(v) > MAX_USERS or", "len(v) >= MAX_USERS or"),
    ("type(u) is not str", "not isinstance(u, str)"),
    ("not 1 <= len(u) <= 16", "not 0 <= len(u) <= 16"),
    ("not 1 <= len(u) <= 16", "not 1 <= len(u) <= 17"),
    ("len(set(v)) != len(v)", "False"),
    ("type(r) not in (list, tuple) or len(r) != 4", "not isinstance(r, (list, tuple)) or len(r) != 4"),
    ("or len(r) != 4", "or len(r) > 4"),
    ("or len(r) != 4", "or len(r) < 4"),
    ("type(default) is not bool", "not isinstance(default, int)"),
    ("type(default) is not bool", "False"),
    ("if name in rows:", "if False:"),
    ("if flag not in rows:", "if False:"),
    ("if user in deny:", "if user in deny and user not in allow:"),
    ("if user in deny:", "if False:"),
    ("if user in allow:", "if False:"),
    ("return {'enabled': False, 'reason': 'denied'}", "return {'enabled': False, 'reason': 'default'}"),
    ("return {'enabled': True, 'reason': 'allowed'}", "return {'enabled': True, 'reason': 'default'}"),
    ("return {'enabled': default, 'reason': 'default'}", "return {'enabled': True, 'reason': 'default'}"),
    ("return {'enabled': default, 'reason': 'default'}", "return {'enabled': not default, 'reason': 'default'}"),
    ("rows[name] = (allow, deny, default)", "rows[name] = (deny, allow, default)"),
    ("allow, deny, default = rows[flag]", "allow, deny, default = rows[flags[0][0]]"),
    ("_name(user, 'user must", "_name(flag, 'user must"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

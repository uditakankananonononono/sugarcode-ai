import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import service_registry_lookup as mod

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
    assert mod.SCOPE == 'PARTIAL: heartbeat-age lookup in a supplied in-memory registry, no network or health probes'
    assert len(mod.NOT_CLAIMED) >= 4 and 'network lookup' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(registry, service, now, ttl):
    """Independent: scan the registry once per instance, compare beat + ttl with now."""
    live, stale, ages = [], [], {}
    for s, i, beat in registry:
        if s != service:
            continue
        ages[i] = now - beat
        (live if beat + ttl >= now else stale).append(i)
    return {'live': sorted(live), 'stale': sorted(stale), 'ages': ages, 'found': len(live) > 0}


def _core(m):
    reg = [('web', 'a', 90), ('web', 'b', 50), ('db', 'x', 99), ('web', 'c', 70)]
    assert m.discover(reg, 'web', 100) == {'live': ['a', 'c'], 'stale': ['b'], 'ages': {'a': 10, 'b': 50, 'c': 30}, 'found': True}
    assert m.discover(reg, 'web', 100, 29)['live'] == ['a']          # c is exactly 30 old: stale at ttl 29, live at 30
    assert m.discover(reg, 'web', 100, 30)['live'] == ['a', 'c']
    assert m.discover(reg, 'web', 100, 10)['live'] == ['a']
    assert m.discover(reg, 'web', 100, 9) == {'live': [], 'stale': ['a', 'b', 'c'], 'ages': {'a': 10, 'b': 50, 'c': 30}, 'found': False}
    assert m.discover(tuple(reg), 'db', 100) == {'live': ['x'], 'stale': [], 'ages': {'x': 1}, 'found': True}
    assert m.discover(reg, 'nope', 100) == {'live': [], 'stale': [], 'ages': {}, 'found': False}
    assert m.discover([], 'web', 0) == {'live': [], 'stale': [], 'ages': {}, 'found': False}
    assert m.discover([['web', 'z', 5], ('web', 'y', 5)], 'web', 5) == {'live': ['y', 'z'], 'stale': [], 'ages': {'z': 0, 'y': 0}, 'found': True}
    assert m.discover([('s', 'i', 0)], 's', 1000000, 1000000) == {'live': ['i'], 'stale': [], 'ages': {'i': 1000000}, 'found': True}
    assert m.discover([('s', 'i', 0)], 's', 1000000, 999999)['stale'] == ['i']
    # default ttl is 30, checked with several instances on both sides
    many = [('s', 'i%d' % k, 100 - k) for k in (0, 10, 29, 30, 31, 60)]
    assert m.discover(many, 's', 100)['live'] == ['i0', 'i10', 'i29', 'i30']
    assert m.discover(many, 's', 100)['stale'] == ['i31', 'i60']
    # the same instance name under two services is two entries
    assert m.discover([('a', 'i', 1), ('b', 'i', 2)], 'b', 3)['ages'] == {'i': 1}
    rng = random.Random(617)
    for _ in range(400):
        now = rng.randint(0, 200)
        ttl = rng.randint(1, 120)
        reg, used = [], set()
        for _ in range(rng.randint(0, 12)):
            s, i = rng.choice('abc'), 'i%d' % rng.randint(0, 5)
            if (s, i) not in used:
                used.add((s, i))
                reg.append((s, i, rng.randint(0, now)))
        for svc in 'abcd':
            assert m.discover(reg, svc, now, ttl) == _oracle(reg, svc, now, ttl)


def _late(m):
    REG = 'registry must be a list or tuple'
    SVC = 'service must be a string of 1 to 16 characters'
    NOW = 'now must be a nonbool integer between 0 and 1000000'
    TTL = 'ttl must be a nonbool integer between 1 and 1000000'
    ENT = 'each entry must be a (service, instance, heartbeat) triple'
    SN = 'service names must be strings of 1 to 16 characters'
    IN = 'instance names must be strings of 1 to 16 characters'
    HB = 'heartbeat must be a nonbool integer between 0 and 1000000'
    good = ('s', 'i', 1)
    for bad in ('ab', None, 5, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, REG, m.discover, bad, 's', 1)
    _raises(TypeError, REG, m.discover, L([good] * 51), 's', 1)
    _raises(ValueError, 'registry must contain at most 50 entries', m.discover, [('s', 'i%d' % k, 1) for k in range(51)], 's', 1)
    assert m.discover([('s', 'i%d' % k, 1) for k in range(50)], 's', 1)['found'] is True
    for bad in ('', 'x' * 17, None, 5, b's', S('s'), LyingS('s')):
        _raises(ValueError, SVC, m.discover, [good], bad, 1)
    assert m.discover([('x' * 16, 'i', 1)], 'x' * 16, 1)['found'] is True
    assert m.discover([('x', 'i', 1)], 'x', 1)['found'] is True
    for bad in (-1, 1000001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, NOW, m.discover, [good], 's', bad)
    for bad in (0, 1000001, True, False, 1.0, '1', None, I(30), LyingI(30), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TTL, m.discover, [good], 's', 1, bad)
    for K in (L, T):
        for bad in (K(good), K(('s', 'i'))):
            _raises(ValueError, ENT, m.discover, [bad], 's', 1)
            _raises(ValueError, ENT, m.discover, [good, bad], 's', 1)
    for bad in ('abc', None, 5, ('s', 'i'), ('s', 'i', 1, 2), ()):
        _raises(ValueError, ENT, m.discover, [bad], 's', 1)
        _raises(ValueError, ENT, m.discover, [good, bad], 's', 1)
    for bad in ('', 'x' * 17, None, 5, S('s'), LyingS('s')):
        _raises(ValueError, SN, m.discover, [(bad, 'i', 1)], 's', 1)
        _raises(ValueError, SN, m.discover, [good, (bad, 'j', 1)], 's', 1)
        _raises(ValueError, IN, m.discover, [('s', bad, 1)], 's', 1)
        _raises(ValueError, IN, m.discover, [good, ('s', bad, 1)], 's', 1)
    for bad in (-1, 1000001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, HB, m.discover, [('s', 'i', bad)], 's', 1000000)
        _raises(ValueError, HB, m.discover, [good, ('s', 'j', bad)], 's', 1000000)
    _raises(ValueError, 'duplicate instance for a service', m.discover, [('s', 'i', 1), ('s', 'i', 2)], 's', 5)
    _raises(ValueError, 'duplicate instance for a service', m.discover, [('s', 'i', 1), ('t', 'i', 1), ('s', 'i', 1)], 's', 5)
    _raises(ValueError, 'heartbeat is after now', m.discover, [('s', 'i', 6)], 's', 5)
    _raises(ValueError, 'heartbeat is after now', m.discover, [('s', 'i', 1), ('t', 'j', 6)], 's', 5)   # any service, not only the asked one
    assert m.discover([('s', 'i', 5)], 's', 5)['ages'] == {'i': 0}
    # order: container, size, service, now, ttl, then entries
    _raises(TypeError, REG, m.discover, L([1]), S('s'), I(1), I(1))
    _raises(ValueError, SVC, m.discover, [1], S('s'), I(1), I(1))
    _raises(ValueError, NOW, m.discover, [1], 's', I(1), I(1))
    _raises(ValueError, TTL, m.discover, [1], 's', 1, I(1))
    _raises(ValueError, ENT, m.discover, [1], 's', 1)
    _raises(ValueError, SN, m.discover, [(S('s'), 'i', I(1))], 's', 1)
    _raises(ValueError, HB, m.discover, [('s', 'i', I(1)), ('s', 'i', 1)], 's', 1)      # before the duplicate check


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_registry_unchanged():
    reg = [('s', 'a', 1), ('s', 'b', 2)]
    r = mod.discover(reg, 's', 3)
    r['live'].append('zzz')
    r['ages']['zzz'] = 0
    assert reg == [('s', 'a', 1), ('s', 'b', 2)]
    assert mod.discover(reg, 's', 3) == {'live': ['a', 'b'], 'stale': [], 'ages': {'a': 2, 'b': 1}, 'found': True}


MUTANTS = [
    ("type(registry) not in (list, tuple)", "not isinstance(registry, (list, tuple))"),
    ("len(registry) > MAX_ENTRIES", "len(registry) >= MAX_ENTRIES"),
    ("MAX_ENTRIES = 50", "MAX_ENTRIES = 51"),
    ("type(e) not in (list, tuple) or len(e) != 3", "not isinstance(e, (list, tuple)) or len(e) != 3"),
    ("or len(e) != 3", "or len(e) > 3"),
    ("or len(e) != 3", "or len(e) < 3"),
    ("type(v) is not str or not 1 <= len(v) <= 16", "not isinstance(v, str) or not 1 <= len(v) <= 16"),
    ("not 1 <= len(v) <= 16", "not 1 <= len(v) <= 17"),
    ("not 1 <= len(v) <= 16", "not 0 <= len(v) <= 16"),
    ("not 1 <= len(v) <= 16", "not 1 <= len(v) < 16"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("MAX_TIME = 1000000", "MAX_TIME = 1000001"),
    ("_int(now, 0, MAX_TIME", "_int(now, 1, MAX_TIME"),
    ("_int(ttl, 1, MAX_TIME", "_int(ttl, 0, MAX_TIME"),
    ("_int(beat, 0, MAX_TIME", "_int(beat, 1, MAX_TIME"),
    ("ttl=30", "ttl=31"),
    ("ttl=30", "ttl=29"),
    ("(s, i) in seen", "i in seen"),
    ("(s, i) in seen", "s in seen"),
    ("seen.add((s, i))", "pass"),
    ("if beat > now:", "if beat >= now:"),
    ("if beat > now:", "if beat > now + 1:"),
    ("now - beat for s, i, beat in registry if s == service", "now - beat for s, i, beat in registry"),
    ("now - beat for s, i, beat in registry if s == service", "beat - now for s, i, beat in registry if s == service"),
    ("if a <= ttl)", "if a < ttl)"),
    ("if a > ttl)", "if a >= ttl)"),
    ("live = sorted(", "live = list("),
    ("stale = sorted(", "stale = list("),
    ("'found': bool(live)", "'found': bool(ages)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

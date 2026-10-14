import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import signal_coverage as mod

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
    assert mod.SCOPE == 'PARTIAL: pillar coverage count over supplied service signal pairs, no real telemetry'
    assert len(mod.NOT_CLAIMED) >= 4 and 'signal quality' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(signals, k):
    """Independent: build a service by pillar matrix and read it row by row."""
    services = sorted({s for s, _ in signals})
    pillars = ['logs', 'metrics', 'traces']
    grid = {s: {p: ((s, p) in set(map(tuple, signals))) for p in pillars} for s in services}
    return {'coverage': {s: [p for p in pillars if grid[s][p]] for s in services},
            'missing': {s: [p for p in pillars if not grid[s][p]] for s in services},
            'observed': [s for s in services if sum(grid[s].values()) >= k],
            'blind': [s for s in services if sum(grid[s].values()) < k]}


def _core(m):
    sig = [('web', 'metrics'), ('web', 'logs'), ('web', 'traces'), ('db', 'metrics'), ('db', 'logs'), ('job', 'traces')]
    r = m.coverage_report(sig)
    assert r == {'coverage': {'web': ['logs', 'metrics', 'traces'], 'db': ['logs', 'metrics'], 'job': ['traces']},
                 'missing': {'web': [], 'db': ['traces'], 'job': ['logs', 'metrics']},
                 'observed': ['db', 'web'], 'blind': ['job']}
    assert m.coverage_report(sig, 2) == r and m.coverage_report(tuple(sig)) == r
    assert m.coverage_report(sig, 1)['observed'] == ['db', 'job', 'web'] and m.coverage_report(sig, 1)['blind'] == []
    assert m.coverage_report(sig, 3)['observed'] == ['web'] and m.coverage_report(sig, 3)['blind'] == ['db', 'job']
    assert m.coverage_report([]) == {'coverage': {}, 'missing': {}, 'observed': [], 'blind': []}
    assert m.coverage_report([['a', 'traces'], ('a', 'logs')])['coverage'] == {'a': ['logs', 'traces']}
    assert m.coverage_report([('z', 'metrics'), ('a', 'metrics')])['observed'] == [] and m.coverage_report([('z', 'metrics'), ('a', 'metrics')], 1)['observed'] == ['a', 'z']
    assert m.coverage_report([('x' * 16, 'logs')], 1)['observed'] == ['x' * 16]
    # the default min_pillars is 2: services with 1, 2 and 3 pillars
    assert m.coverage_report([('one', 'logs'), ('two', 'logs'), ('two', 'traces'), ('tri', 'logs'), ('tri', 'traces'), ('tri', 'metrics')]) \
        == m.coverage_report([('one', 'logs'), ('two', 'logs'), ('two', 'traces'), ('tri', 'logs'), ('tri', 'traces'), ('tri', 'metrics')], 2)
    assert m.coverage_report([('one', 'logs'), ('two', 'logs'), ('two', 'traces')])['blind'] == ['one']
    full = [('s%02d' % i, p) for i in range(20) for p in ('metrics', 'logs', 'traces')]
    assert len(full) == 60 and len(m.coverage_report(full)['observed']) == 20
    rng = random.Random(629)
    for _ in range(500):
        pairs = sorted({(rng.choice('abcd'), rng.choice(('metrics', 'logs', 'traces'))) for _ in range(rng.randint(0, 14))})
        rng.shuffle(pairs)
        k = rng.randint(1, 3)
        assert m.coverage_report(pairs, k) == _oracle(pairs, k), (pairs, k)


def _late(m):
    SG = 'signals must be a list or tuple'
    MP = 'min_pillars must be a nonbool integer between 1 and 3'
    EP = 'each signal must be a (service, pillar) pair'
    SN = 'service names must be strings of 1 to 16 characters'
    PL = 'pillar must be one of metrics, logs, traces'
    good = ('a', 'logs')
    for bad in ('ab', None, 5, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, SG, m.coverage_report, bad)
    _raises(TypeError, SG, m.coverage_report, L([good] * 61))
    _raises(ValueError, 'signals must contain at most 60 entries', m.coverage_report, [('s%d' % i, 'logs') for i in range(61)])
    for bad in (0, 4, True, False, 1.0, '1', None, I(2), LyingI(2), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MP, m.coverage_report, [good], bad)
    for K in (L, T):
        for bad in (K(good), K(('a',))):
            _raises(ValueError, EP, m.coverage_report, [bad])
            _raises(ValueError, EP, m.coverage_report, [good, bad])
    for bad in ('ab', None, 5, ('a',), ('a', 'logs', 1), ()):
        _raises(ValueError, EP, m.coverage_report, [bad])
        _raises(ValueError, EP, m.coverage_report, [good, bad])
    for bad in ('', 'x' * 17, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, SN, m.coverage_report, [(bad, 'logs')])
        _raises(ValueError, SN, m.coverage_report, [good, (bad, 'logs')])
    for bad in ('Logs', 'metric', '', None, 5, S('logs'), LyingS('logs'), LyingS('zzz'), ['logs'], b'logs'):
        _raises(ValueError, PL, m.coverage_report, [('b', bad)])
        _raises(ValueError, PL, m.coverage_report, [good, ('b', bad)])
    _raises(ValueError, 'duplicate signal', m.coverage_report, [good, good])
    _raises(ValueError, 'duplicate signal', m.coverage_report, [good, ('b', 'logs'), good])
    assert m.coverage_report([('a', 'logs'), ('b', 'logs'), ('a', 'traces')])['coverage'] == {'a': ['logs', 'traces'], 'b': ['logs']}   # same pillar on two services is fine
    # order: signals, size, min_pillars, then per signal: shape, service, pillar, duplicate
    _raises(TypeError, SG, m.coverage_report, L([1]), I(1))
    _raises(ValueError, MP, m.coverage_report, [1], I(1))
    _raises(ValueError, EP, m.coverage_report, [1], 2)
    _raises(ValueError, SN, m.coverage_report, [(S('a'), S('logs'))])
    _raises(ValueError, PL, m.coverage_report, [('a', S('logs')), ('a', 'logs')])      # pillar before the duplicate check


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
    def __hash__(self): return hash('logs')


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


def test_result_is_fresh_and_signals_unchanged():
    sig = [('a', 'traces'), ('a', 'logs')]
    r = mod.coverage_report(sig)
    r['coverage']['a'].append('zzz')
    r['observed'].append('zzz')
    assert sig == [('a', 'traces'), ('a', 'logs')]
    assert mod.coverage_report(sig)['coverage'] == {'a': ['logs', 'traces']}


MUTANTS = [
    ("type(signals) not in (list, tuple)", "not isinstance(signals, (list, tuple))"),
    ("len(signals) > MAX_SIGNALS", "len(signals) >= MAX_SIGNALS"),
    ("MAX_SIGNALS = 60", "MAX_SIGNALS = 61"),
    ("PILLARS = ('metrics', 'logs', 'traces')", "PILLARS = ('metrics', 'logs')"),
    ("PILLARS = ('metrics', 'logs', 'traces')", "PILLARS = ('metrics', 'logs', 'traces', 'events')"),
    ("type(min_pillars) is not int or not 1 <= min_pillars <= 3", "isinstance(min_pillars, bool) or not isinstance(min_pillars, int) or not 1 <= min_pillars <= 3"),
    ("type(min_pillars) is not int or not 1 <= min_pillars <= 3", "not isinstance(min_pillars, int) or not 1 <= min_pillars <= 3"),
    ("not 1 <= min_pillars <= 3", "not 0 <= min_pillars <= 3"),
    ("not 1 <= min_pillars <= 3", "not 1 <= min_pillars <= 4"),
    ("not 1 <= min_pillars <= 3", "not 1 <= min_pillars < 3"),
    ("min_pillars=2", "min_pillars=1"),
    ("min_pillars=2", "min_pillars=3"),
    ("type(s) not in (list, tuple) or len(s) != 2", "not isinstance(s, (list, tuple)) or len(s) != 2"),
    ("or len(s) != 2", "or len(s) > 2"),
    ("or len(s) != 2", "or len(s) < 2"),
    ("type(service) is not str", "not isinstance(service, str)"),
    ("not 1 <= len(service) <= 16", "not 0 <= len(service) <= 16"),
    ("not 1 <= len(service) <= 16", "not 1 <= len(service) <= 17"),
    ("not 1 <= len(service) <= 16", "not 1 <= len(service) < 16"),
    ("type(pillar) is not str or pillar not in PILLARS", "pillar not in PILLARS"),
    ("type(pillar) is not str or pillar not in PILLARS", "not isinstance(pillar, str) or pillar not in PILLARS"),
    ("(service, pillar) in seen", "service in seen"),
    ("(service, pillar) in seen", "pillar in seen"),
    ("seen.add((service, pillar))", "pass"),
    ("coverage = {s: sorted(p) for s, p in coverage.items()}", "coverage = {s: p for s, p in coverage.items()}"),
    ("set(PILLARS) - set(p)", "set(PILLARS) & set(p)"),
    ("len(p) >= min_pillars)", "len(p) > min_pillars)"),
    ("len(p) < min_pillars)", "len(p) <= min_pillars)"),
    ("'observed': sorted(", "'observed': list("),
    ("'blind': sorted(", "'blind': list("),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

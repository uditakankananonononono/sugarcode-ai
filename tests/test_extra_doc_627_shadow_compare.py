import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import shadow_compare as mod

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
    assert mod.SCOPE == 'PARTIAL: status and latency comparison of supplied primary and shadow results, nothing replayed'
    assert len(mod.NOT_CLAIMED) >= 4 and 'replaying real requests' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(pairs, pct):
    """Independent: exact rational comparison with Fraction instead of the integer cross-multiplication."""
    from fractions import Fraction
    out = {'mismatched': [], 'slow': [], 'clean': [], 'total': len(pairs)}
    for rid, ps, ss, pm, sm in sorted(pairs):
        bad = ps != ss
        slow = Fraction(sm, pm) > 1 + Fraction(pct, 100)
        if bad:
            out['mismatched'].append(rid)
        if slow:
            out['slow'].append(rid)
        if not bad and not slow:
            out['clean'].append(rid)
    return out


def _core(m):
    pairs = [('a', 200, 200, 100, 100), ('b', 200, 500, 100, 100), ('c', 200, 200, 100, 121), ('d', 404, 200, 100, 300), ('e', 200, 200, 100, 120)]
    assert m.compare_shadow(pairs) == {'mismatched': ['b', 'd'], 'slow': ['c', 'd'], 'clean': ['a', 'e'], 'total': 5}
    assert m.compare_shadow(tuple(pairs), 20) == m.compare_shadow(pairs)
    assert m.compare_shadow([['z', 200, 200, 10, 12]]) == {'mismatched': [], 'slow': [], 'clean': ['z'], 'total': 1}   # 20 percent exactly is not slow
    assert m.compare_shadow([('z', 200, 200, 10, 13)])['slow'] == ['z']
    assert m.compare_shadow([('z', 200, 200, 10, 12)], 19)['slow'] == ['z']
    assert m.compare_shadow([('z', 200, 200, 10, 12)], 20)['slow'] == []
    assert m.compare_shadow([('z', 200, 200, 10, 10)], 0)['slow'] == []
    assert m.compare_shadow([('z', 200, 200, 10, 11)], 0)['slow'] == ['z']
    assert m.compare_shadow([('z', 200, 200, 1, 11)], 1000)['slow'] == []
    assert m.compare_shadow([('z', 200, 200, 1, 12)], 1000)['slow'] == ['z']
    assert m.compare_shadow([('z', 200, 200, 100000, 1)], 0)['clean'] == ['z']                  # faster shadow is fine
    assert m.compare_shadow([('z', 100, 599, 100000, 100000)]) == {'mismatched': ['z'], 'slow': [], 'clean': [], 'total': 1}
    assert m.compare_shadow([('y', 599, 599, 1, 1), ('x', 100, 100, 1, 1)])['clean'] == ['x', 'y']
    assert m.compare_shadow([('z', 200, 200, 1, 2)], 99)['slow'] == ['z']        # 2 > 1.99, an off-by-one in the cross product would miss it
    assert m.compare_shadow([('z', 200, 200, 1, 2)], 100)['slow'] == []
    # ids come back sorted whatever the input order
    shuf = [('q', 200, 500, 1, 9), ('b', 200, 500, 1, 9), ('m', 200, 500, 1, 9), ('a', 200, 500, 1, 9)]
    assert m.compare_shadow(shuf) == {'mismatched': ['a', 'b', 'm', 'q'], 'slow': ['a', 'b', 'm', 'q'], 'clean': [], 'total': 4}
    shuf = [('q', 200, 200, 1, 1), ('b', 200, 200, 1, 1), ('a', 200, 200, 1, 1)]
    assert m.compare_shadow(shuf)['clean'] == ['a', 'b', 'q']
    assert m.compare_shadow([]) == {'mismatched': [], 'slow': [], 'clean': [], 'total': 0}
    ids = ['r%02d' % i for i in range(50)]
    assert m.compare_shadow([(i, 200, 200, 5, 5) for i in ids])['total'] == 50
    # the default slow_percent is 20: several pairs on each side of the edge
    edge = [('p%d' % k, 200, 200, 100, 100 + k) for k in (0, 10, 19, 20, 21, 40)]
    assert m.compare_shadow(edge)['slow'] == ['p21', 'p40'] and m.compare_shadow(edge, 20) == m.compare_shadow(edge)
    rng = random.Random(627)
    for _ in range(500):
        pairs = [('i%d' % k, rng.choice((200, 200, 500)), rng.choice((200, 500)), rng.randint(1, 50), rng.randint(1, 80)) for k in range(rng.randint(0, 10))]
        pct = rng.choice((0, 1, 20, 50, 99, 100, 250, 1000, rng.randint(0, 1000)))
        assert m.compare_shadow(pairs, pct) == _oracle(pairs, pct), (pairs, pct)


def _late(m):
    PR = 'pairs must be a list or tuple'
    SP = 'slow_percent must be a nonbool integer between 0 and 1000'
    EP = 'each pair must be a (request_id, primary_status, shadow_status, primary_ms, shadow_ms) tuple'
    RI = 'request ids must be strings of 1 to 16 characters'
    ST = 'status must be a nonbool integer between 100 and 599'
    MS = 'milliseconds must be nonbool integers between 1 and 100000'
    good = ('a', 200, 200, 1, 1)
    for bad in ('ab', None, 5, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, PR, m.compare_shadow, bad)
    _raises(TypeError, PR, m.compare_shadow, L([good] * 51))
    _raises(ValueError, 'pairs must contain at most 50 entries', m.compare_shadow, [('i%d' % k, 200, 200, 1, 1) for k in range(51)])
    for bad in (-1, 1001, True, False, 1.0, '1', None, I(20), LyingI(20), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, SP, m.compare_shadow, [good], bad)
    for K in (L, T):
        for bad in (K(good), K(('a', 200, 200, 1))):
            _raises(ValueError, EP, m.compare_shadow, [bad])
            _raises(ValueError, EP, m.compare_shadow, [good, bad])
    for bad in ('abcde', None, 5, ('a', 200, 200, 1), ('a', 200, 200, 1, 1, 1), ()):
        _raises(ValueError, EP, m.compare_shadow, [bad])
        _raises(ValueError, EP, m.compare_shadow, [good, bad])
    for bad in ('', 'x' * 17, None, 5, S('a'), LyingS('a'), b'a'):
        _raises(ValueError, RI, m.compare_shadow, [(bad, 200, 200, 1, 1)])
        _raises(ValueError, RI, m.compare_shadow, [good, (bad, 200, 200, 1, 1)])
    assert m.compare_shadow([('x' * 16, 200, 200, 1, 1)])['clean'] == ['x' * 16]
    for bad in (99, 600, True, False, 200.0, '200', None, I(200), LyingI(200), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, ST, m.compare_shadow, [('b', bad, 200, 1, 1)])
        _raises(ValueError, ST, m.compare_shadow, [('b', 200, bad, 1, 1)])
        _raises(ValueError, ST, m.compare_shadow, [good, ('b', bad, 200, 1, 1)])
        _raises(ValueError, ST, m.compare_shadow, [good, ('b', 200, bad, 1, 1)])
    for bad in (0, 100001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MS, m.compare_shadow, [('b', 200, 200, bad, 1)])
        _raises(ValueError, MS, m.compare_shadow, [('b', 200, 200, 1, bad)])
        _raises(ValueError, MS, m.compare_shadow, [good, ('b', 200, 200, bad, 1)])
        _raises(ValueError, MS, m.compare_shadow, [good, ('b', 200, 200, 1, bad)])
    _raises(ValueError, 'duplicate request id', m.compare_shadow, [good, good])
    _raises(ValueError, 'duplicate request id', m.compare_shadow, [good, ('b', 200, 200, 1, 1), good])
    # order: pairs, size, slow_percent, then per pair: shape, id, statuses, times, duplicate
    _raises(TypeError, PR, m.compare_shadow, L([1]), I(1))
    _raises(ValueError, SP, m.compare_shadow, [1], I(1))
    _raises(ValueError, EP, m.compare_shadow, [1], 5)
    _raises(ValueError, RI, m.compare_shadow, [(S('a'), I(1), I(1), I(1), I(1))])
    _raises(ValueError, ST, m.compare_shadow, [('a', I(200), I(1), I(1), I(1))])
    _raises(ValueError, ST, m.compare_shadow, [('a', 200, I(200), I(1), I(1))])
    _raises(ValueError, MS, m.compare_shadow, [('a', 200, 200, I(1), I(1))])
    _raises(ValueError, MS, m.compare_shadow, [('a', 200, 200, 1, I(1)), ('a', 200, 200, 1, 1)])      # before the duplicate check


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


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_pairs_unchanged():
    pairs = [('a', 200, 500, 1, 1)]
    r = mod.compare_shadow(pairs)
    r['mismatched'].append('zzz')
    assert pairs == [('a', 200, 500, 1, 1)]
    assert mod.compare_shadow(pairs)['mismatched'] == ['a']


MUTANTS = [
    ("type(pairs) not in (list, tuple)", "not isinstance(pairs, (list, tuple))"),
    ("len(pairs) > MAX_PAIRS", "len(pairs) >= MAX_PAIRS"),
    ("MAX_PAIRS = 50", "MAX_PAIRS = 51"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(slow_percent, 0, 1000", "_int(slow_percent, 1, 1000"),
    ("_int(slow_percent, 0, 1000", "_int(slow_percent, 0, 1001"),
    ("slow_percent=20", "slow_percent=21"),
    ("slow_percent=20", "slow_percent=19"),
    ("type(p) not in (list, tuple) or len(p) != 5", "not isinstance(p, (list, tuple)) or len(p) != 5"),
    ("or len(p) != 5", "or len(p) > 5"),
    ("or len(p) != 5", "or len(p) < 5"),
    ("type(rid) is not str", "not isinstance(rid, str)"),
    ("not 1 <= len(rid) <= 16", "not 0 <= len(rid) <= 16"),
    ("not 1 <= len(rid) <= 16", "not 1 <= len(rid) <= 17"),
    ("not 1 <= len(rid) <= 16", "not 1 <= len(rid) < 16"),
    ("_int(ps, 100, 599", "_int(ps, 101, 599"),
    ("_int(ps, 100, 599", "_int(ps, 100, 600"),
    ("_int(ss, 100, 599", "_int(ss, 99, 599"),
    ("_int(ss, 100, 599", "_int(ss, 100, 598"),
    ("_int(pm, 1, 100000", "_int(pm, 0, 100000"),
    ("_int(pm, 1, 100000", "_int(pm, 1, 100001"),
    ("_int(sm, 1, 100000", "_int(sm, 0, 100000"),
    ("_int(sm, 1, 100000", "_int(sm, 1, 99999"),
    ("if rid in seen:", "if False:"),
    ("if p[1] != p[2])", "if p[1] < p[2])"),
    ("p[4] * 100 > p[3] * (100 + slow_percent))\n    clean", "p[4] * 100 >= p[3] * (100 + slow_percent))\n    clean"),
    ("p[4] * 100 > p[3] * (100 + slow_percent))\n    clean", "p[4] * 100 > p[3] * (100 + slow_percent) + 1)\n    clean"),
    ("p[4] * 100 > p[3] * (100 + slow_percent))\n    clean", "p[4] * 100 > p[3] * slow_percent)\n    clean"),
    ("p[4] * 100 > p[3] * (100 + slow_percent))\n    clean", "p[3] * 100 > p[4] * (100 + slow_percent))\n    clean"),
    ("p[1] == p[2] and p[4]", "p[4]"),
    ("p[4] * 100 <= p[3] * (100 + slow_percent))", "p[4] * 100 < p[3] * (100 + slow_percent))"),
    ("'total': len(pairs)", "'total': len(pairs) - 1"),
    ("mismatched = sorted(", "mismatched = list("),
    ("slow = sorted(", "slow = list("),
    ("clean = sorted(", "clean = list("),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

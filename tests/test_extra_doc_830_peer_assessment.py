import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import peer_assessment as mod

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
    assert mod.SCOPE == 'PARTIAL: per-person tally of supplied peer rating triples, no person is evaluated'
    assert len(mod.NOT_CLAIMED) == 5 and 'rater honesty' in mod.NOT_CLAIMED and 'bias correction' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Peer Assessment - Evaluates others' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(rs):
    from fractions import Fraction
    import math
    names = sorted({b for _, b, _ in rs})
    out = []
    for n in names:
        sc = [s for _, b, s in rs if b == n]
        out.append((n, len(sc), sum(sc), math.floor(Fraction(sum(sc) * 10, len(sc)))))
    return {'ratees': out, 'raters': len({a for a, _, _ in rs})}


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
    f = m.peer_assessment
    assert f([]) == {'ratees': [], 'raters': 0}
    assert f([('a', 'b', 4)]) == {'ratees': [('b', 1, 4, 40)], 'raters': 1}
    r = f([('a', 'c', 5), ('b', 'c', 4), ('a', 'b', 1)])
    assert r == {'ratees': [('b', 1, 1, 10), ('c', 2, 9, 45)], 'raters': 2}
    assert f([('a', 'c', 5), ('b', 'c', 4), ('d', 'c', 4)])['ratees'] == [('c', 3, 13, 43)]
    assert f([('a', 'c', 1), ('b', 'c', 1), ('d', 'c', 2)])['ratees'] == [('c', 3, 4, 13)]
    assert f([('x', 'z', 3), ('x', 'y', 2)])['ratees'] == [('y', 1, 2, 20), ('z', 1, 3, 30)]
    assert f([('x', 'y', 2), ('x', 'z', 3)])['ratees'][0][0] == 'y'
    assert f((['a', 'b', 5], ('b', 'a', 5)))['raters'] == 2
    assert f([('x' * 12, 'y' * 12, 5)])['ratees'] == [('y' * 12, 1, 5, 50)]
    # a and b rate each other: both are raters and ratees
    assert f([('a', 'b', 2), ('b', 'a', 3)]) == {'ratees': [('a', 1, 3, 30), ('b', 1, 2, 20)], 'raters': 2}
    # default max_ratings 8
    rs8 = [('r%d' % i, 'z', 1) for i in range(8)]
    f(rs8)
    _raises(ValueError, 'ratings must contain at most max_ratings entries', f, rs8 + [('r8', 'z', 1)])
    assert f(rs8 + [('r8', 'z', 1)], 9)['ratees'] == [('z', 9, 9, 10)]
    assert f([('r%d' % i, 'z', 1) for i in range(20)], 20)['raters'] == 20
    _raises(ValueError, 'ratings must contain at most max_ratings entries', f, rs8[:3], 2)
    f(rs8[:2], 2)
    rng = random.Random(830)
    names = ['a', 'b', 'c', 'd', 'e']
    for _ in range(600):
        pairs = [(x, y) for x in names for y in names if x != y]
        rng.shuffle(pairs)
        rs = [(x, y, rng.randint(1, 5)) for x, y in pairs[:rng.randint(0, 8)]]
        assert f(rs) == _oracle(rs), rs


def _late(m):
    f = m.peer_assessment
    MR = 'max_ratings must be a nonbool integer between 1 and 20'
    RT = 'ratings must be a list or tuple'
    RS = 'ratings must contain at most max_ratings entries'
    RP = 'each rating must be a (rater, ratee, score) triple'
    RA = 'each rater must be an ASCII string of 1 to 12 characters'
    RE = 'each ratee must be an ASCII string of 1 to 12 characters'
    SC = 'score must be a nonbool integer between 1 and 5'
    SF = 'a person may not rate themself'
    DP = 'each rater may rate a person once'
    ok = [('a', 'b', 1)]
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MR, f, [], bad)
    f([], 1)
    f([], 20)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, RT, f, bad)
    for bad in ('ab', None, 5, ('a', 'b'), ('a', 'b', 1, 1), (), {'a': 1}, L(['a', 'b', 1]), T(('a', 'b', 1))):
        _raises(ValueError, RP, f, [bad])
        _raises(ValueError, RP, f, [('a', 'b', 1), bad])
    for bad in ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661'):
        _raises(ValueError, RA, f, [(bad, 'b', 1)])
        _raises(ValueError, RA, f, [('a', 'b', 1), (bad, 'b', 1)])
        _raises(ValueError, RE, f, [('a', bad, 1)])
        _raises(ValueError, RE, f, [('a', 'b', 1), ('c', bad, 1)])
    for bad in (0, 6, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, SC, f, [('a', 'b', bad)])
        _raises(ValueError, SC, f, [('a', 'b', 1), ('c', 'b', bad)])
    f([('a', 'b', 5)])
    f([('A~ z', 'b 9', 5)])
    _raises(ValueError, SF, f, [('a', 'a', 1)])
    _raises(ValueError, SF, f, [('a', 'b', 1), ('c', 'c', 1)])
    _raises(ValueError, DP, f, [('a', 'b', 1), ('a', 'b', 2)])
    _raises(ValueError, DP, f, [('a', 'b', 1), ('c', 'b', 1), ('a', 'b', 1)])
    f([('a', 'b', 1), ('a', 'c', 1), ('b', 'a', 1)])
    # validation order
    _raises(ValueError, MR, f, None, I(1))
    _raises(TypeError, RT, f, None)
    _raises(ValueError, RS, f, [1] * 9)
    _raises(ValueError, RP, f, [1])
    _raises(ValueError, RA, f, [(1, 1, 1)])
    _raises(ValueError, RE, f, [('a', 1, 1)])
    _raises(ValueError, SC, f, [('a', 'a', 0)])
    _raises(ValueError, SF, f, [('a', 'a', 1), ('a', 'a', 1)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_ratings=8", "max_ratings=9"),
    ("max_ratings=8", "max_ratings=7"),
    ("type(max_ratings) is not int or not 1 <= max_ratings <= 20", "not isinstance(max_ratings, int) or not 1 <= max_ratings <= 20"),
    ("type(max_ratings) is not int or not 1 <= max_ratings <= 20", "isinstance(max_ratings, bool) or not isinstance(max_ratings, int) or not 1 <= max_ratings <= 20"),
    ("not 1 <= max_ratings <= 20", "not 0 <= max_ratings <= 20"),
    ("not 1 <= max_ratings <= 20", "not 1 <= max_ratings < 20"),
    ("not 1 <= max_ratings <= 20", "not 1 <= max_ratings <= 21"),
    ("type(ratings) not in (list, tuple)", "not isinstance(ratings, (list, tuple))"),
    ("len(ratings) > max_ratings", "len(ratings) >= max_ratings"),
    ("type(r) not in (list, tuple) or len(r) != 3", "not isinstance(r, (list, tuple)) or len(r) != 3"),
    ("type(r) not in (list, tuple) or len(r) != 3", "type(r) not in (list, tuple) or len(r) > 3"),
    ("type(r) not in (list, tuple) or len(r) != 3", "type(r) not in (list, tuple) or len(r) < 3"),
    ("type(rater) is not str or not rater.isascii() or not 1 <= len(rater) <= 12", "not isinstance(rater, str) or not rater.isascii() or not 1 <= len(rater) <= 12"),
    ("type(rater) is not str or not rater.isascii() or not 1 <= len(rater) <= 12", "type(rater) is not str or not rater.isascii() or not 0 <= len(rater) <= 12"),
    ("type(rater) is not str or not rater.isascii() or not 1 <= len(rater) <= 12", "type(rater) is not str or not rater.isascii() or not 1 <= len(rater) < 12"),
    ("type(rater) is not str or not rater.isascii() or not 1 <= len(rater) <= 12", "type(rater) is not str or not rater.isascii() or not 1 <= len(rater) <= 13"),
    ("type(ratee) is not str or not ratee.isascii() or not 1 <= len(ratee) <= 12", "not isinstance(ratee, str) or not ratee.isascii() or not 1 <= len(ratee) <= 12"),
    ("type(ratee) is not str or not ratee.isascii() or not 1 <= len(ratee) <= 12", "type(ratee) is not str or not ratee.isascii() or not 0 <= len(ratee) <= 12"),
    ("type(ratee) is not str or not ratee.isascii() or not 1 <= len(ratee) <= 12", "type(ratee) is not str or not ratee.isascii() or not 1 <= len(ratee) < 12"),
    ("type(ratee) is not str or not ratee.isascii() or not 1 <= len(ratee) <= 12", "type(ratee) is not str or not ratee.isascii() or not 1 <= len(ratee) <= 13"),
    ("type(score) is not int or not 1 <= score <= 5", "not isinstance(score, int) or not 1 <= score <= 5"),
    ("type(score) is not int or not 1 <= score <= 5", "isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5"),
    ("not 1 <= score <= 5", "not 0 <= score <= 5"),
    ("not 1 <= score <= 5", "not 1 <= score < 5"),
    ("not 1 <= score <= 5", "not 1 <= score <= 6"),
    ("type(rater) is not str or not rater.isascii() or not 1 <= len(rater) <= 12", "type(rater) is not str or not 1 <= len(rater) <= 12"),
    ("type(ratee) is not str or not ratee.isascii() or not 1 <= len(ratee) <= 12", "type(ratee) is not str or not 1 <= len(ratee) <= 12"),
    ("if rater == ratee:", "if False:"),
    ("if (rater, ratee) in seen:", "if False:"),
    ("if (rater, ratee) in seen:", "if rater in raters:"),
    ("raters.add(rater)", "raters.add(ratee)"),
    ("tally[ratee] = (c + 1, t + score)", "tally[ratee] = (c + 1, t + 1)"),
    ("tally[ratee] = (c + 1, t + score)", "tally[ratee] = (1, t + score)"),
    ("t * 10 // c", "t * 10 // (c + 1)"),
    ("t * 10 // c", "(t * 10 + c // 2) // c"),
    ("t * 10 // c", "round(t * 10 / c)"),
    ("t * 10 // c", "t // c * 10"),
    ("sorted(tally.items())", "sorted(tally.items(), reverse=True)"),
    ("sorted(tally.items())", "tally.items()"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

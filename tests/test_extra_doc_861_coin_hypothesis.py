import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import coin_hypothesis as mod

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
    assert mod.SCOPE == 'PARTIAL: exact two-sided fair-coin tail count for supplied flips, no science is done'
    assert len(mod.NOT_CLAIMED) == 5 and 'effect size' in mod.NOT_CLAIMED and 'multiple testing' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Scientific Thinking - Tests hypotheses' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(nm, n, h, al):
    """Independent: build Pascal's triangle row by row instead of using a binomial function."""
    row = [1]
    for _ in range(n):
        row = [1] + [row[i] + row[i + 1] for i in range(len(row) - 1)] + [1]
    tail = 0
    for c in row:
        if c <= row[h]:
            tail += c
    tot = sum(row)
    pm = 0
    while (pm + 1) * tot <= tail * 1000:
        pm += 1
    return {'name': nm, 'tail_count': tail, 'total': tot, 'p_permille': pm, 'reject': tail * 100 < al * tot}


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
    f = m.coin_hypothesis
    assert f('h', 1, 0) == {'name': 'h', 'tail_count': 2, 'total': 2, 'p_permille': 1000, 'reject': False}
    assert f('h', 4, 2) == {'name': 'h', 'tail_count': 16, 'total': 16, 'p_permille': 1000, 'reject': False}
    assert f('h', 4, 0) == {'name': 'h', 'tail_count': 2, 'total': 16, 'p_permille': 125, 'reject': False}
    assert f('h', 4, 1) == {'name': 'h', 'tail_count': 10, 'total': 16, 'p_permille': 625, 'reject': False}
    # symmetric tails: 3 of 4 matches 1 of 4
    assert f('h', 4, 3) == f('h', 4, 1)
    # 10 flips: 0 heads has p = 2/1024; 1 head has 22/1024; 2 heads has 112/1024
    r = f('h', 10, 0)
    assert r['tail_count'] == 2 and r['total'] == 1024 and r['p_permille'] == 1 and r['reject'] is True
    r = f('h', 10, 1)
    assert r['tail_count'] == 22 and r['p_permille'] == 21 and r['reject'] is True
    r = f('h', 10, 2)
    assert r['tail_count'] == 112 and r['p_permille'] == 109 and r['reject'] is False
    # the default alpha 5 edge: 22/1024 is 2.1 percent, 112/1024 is 10.9 percent
    assert f('h', 10, 1, 2)['reject'] is False and f('h', 10, 1, 3)['reject'] is True
    assert f('h', 10, 1) == f('h', 10, 1, 5)
    assert f('h', 10, 2, 10)['reject'] is False and f('h', 10, 2, 11)['reject'] is True
    assert f('h', 10, 2) == f('h', 10, 2, 5) and f('h', 10, 2, 50)['reject'] is True
    # exactly at alpha: 2 of 16 total is 12.5 percent, so alpha 12 keeps and 13 rejects
    assert f('h', 4, 0, 12)['reject'] is False and f('h', 4, 0, 13)['reject'] is True
    # exactly at alpha with equality: tail 1 of 2 total at alpha 50 is not rejected (100 < 100 false)
    assert f('h', 1, 0, 50)['reject'] is False
    assert f('h', 2, 0, 50)['reject'] is False and f('h', 3, 0, 50)['reject'] is True
    assert f('h', 3, 0, 25)['reject'] is False and f('h', 3, 0, 26)['reject'] is True
    r = f('h', 30, 0)
    assert r['tail_count'] == 2 and r['total'] == 2 ** 30 and r['p_permille'] == 0 and r['reject'] is True
    assert f('h', 30, 15)['tail_count'] == 2 ** 30
    assert f('A~ z 9', 3, 1)['name'] == 'A~ z 9' and f('x' * 12, 3, 1)['name'] == 'x' * 12
    rng = random.Random(861)
    for _ in range(600):
        n = rng.randint(1, 30)
        h = rng.randint(0, n)
        al = rng.randint(1, 50)
        assert f('q', n, h, al) == _oracle('q', n, h, al), (n, h, al)
        assert f('q', n, h) == _oracle('q', n, h, 5)


def _late(m):
    f = m.coin_hypothesis
    NM = 'name must be a printable ASCII string of 1 to 12 characters'
    TR = 'trials must be a nonbool integer between 1 and 30'
    HE = 'heads must be a nonbool integer between 0 and trials'
    AL = 'alpha must be a nonbool integer between 1 and 50'
    for bad in ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661',
                '\n', 'a\n', '\ta', 'a\x00', '\x7f', 'a\r', '\x1b[0m', 'a\x0b'):
        _raises(ValueError, NM, f, bad, 3, 1)
    f('A~ z', 3, 1)
    f(' ', 3, 1)
    for bad in (0, 31, -1, True, False, 1.0, '1', None, I(3), LyingI(3), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TR, f, 'a', bad, 0)
    f('a', 1, 0)
    f('a', 30, 0)
    for bad in (-1, 4, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, HE, f, 'a', 3, bad)
    f('a', 3, 0)
    f('a', 3, 3)
    for bad in (0, 51, -1, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, AL, f, 'a', 3, 1, bad)
    f('a', 3, 1, 1)
    f('a', 3, 1, 50)
    _raises(ValueError, NM, f, None, None, None, None)
    _raises(ValueError, TR, f, 'a', None, None, None)
    _raises(ValueError, HE, f, 'a', 3, None, None)
    _raises(ValueError, HE, f, 'a', 3, 9, 99)
    _raises(ValueError, AL, f, 'a', 3, 1, None)


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


NC = "type(name) is not str or not name.isascii() or not name.isprintable() or not 1 <= len(name) <= 12"
MUTANTS = [
    ("alpha=5", "alpha=4"),
    ("alpha=5", "alpha=6"),
    (NC, "not isinstance(name, str) or not name.isascii() or not name.isprintable() or not 1 <= len(name) <= 12"),
    (NC, "type(name) is not str or not name.isprintable() or not 1 <= len(name) <= 12"),
    (NC, "type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12"),
    (NC, "type(name) is not str or not name.isascii() or not name.isalnum() or not 1 <= len(name) <= 12"),
    (NC, "type(name) is not str or not name.isascii() or not name.isprintable() or not 0 <= len(name) <= 12"),
    (NC, "type(name) is not str or not name.isascii() or not name.isprintable() or not 1 <= len(name) < 12"),
    (NC, "type(name) is not str or not name.isascii() or not name.isprintable() or not 1 <= len(name) <= 13"),
    ("type(trials) is not int or not 1 <= trials <= 30", "not isinstance(trials, int) or not 1 <= trials <= 30"),
    ("type(trials) is not int or not 1 <= trials <= 30", "isinstance(trials, bool) or not isinstance(trials, int) or not 1 <= trials <= 30"),
    ("not 1 <= trials <= 30", "not 0 <= trials <= 30"),
    ("not 1 <= trials <= 30", "not 1 <= trials < 30"),
    ("not 1 <= trials <= 30", "not 1 <= trials <= 31"),
    ("type(heads) is not int or not 0 <= heads <= trials", "not isinstance(heads, int) or not 0 <= heads <= trials"),
    ("type(heads) is not int or not 0 <= heads <= trials", "isinstance(heads, bool) or not isinstance(heads, int) or not 0 <= heads <= trials"),
    ("not 0 <= heads <= trials", "not 1 <= heads <= trials"),
    ("not 0 <= heads <= trials", "not -1 <= heads <= trials"),
    ("not 0 <= heads <= trials", "not 0 <= heads < trials"),
    ("not 0 <= heads <= trials", "not 0 <= heads <= trials + 1"),
    ("type(alpha) is not int or not 1 <= alpha <= 50", "not isinstance(alpha, int) or not 1 <= alpha <= 50"),
    ("type(alpha) is not int or not 1 <= alpha <= 50", "isinstance(alpha, bool) or not isinstance(alpha, int) or not 1 <= alpha <= 50"),
    ("not 1 <= alpha <= 50", "not 0 <= alpha <= 50"),
    ("not 1 <= alpha <= 50", "not 1 <= alpha < 50"),
    ("not 1 <= alpha <= 50", "not 1 <= alpha <= 51"),
    ("seen = comb(trials, heads)", "seen = comb(trials, trials - heads) + 1"),
    ("seen = comb(trials, heads)", "seen = comb(trials, 0)"),
    ("if c <= seen)", "if c < seen)"),
    ("if c <= seen)", "if c >= seen)"),
    ("for i in range(trials + 1))", "for i in range(trials))"),
    ("for i in range(trials + 1))", "for i in range(1, trials + 1))"),
    ("total = 2 ** trials", "total = 2 ** trials - 1"),
    ("total = 2 ** trials", "total = 2 * trials"),
    ("tail * 1000 // total", "(tail * 1000 + total - 1) // total"),
    ("tail * 1000 // total", "round(tail * 1000 / total)"),
    ("tail * 1000 // total", "tail * 100 // total"),
    ("'reject': tail * 100 < alpha * total", "'reject': tail * 100 <= alpha * total"),
    ("'reject': tail * 100 < alpha * total", "'reject': tail * 100 > alpha * total"),
    ("'reject': tail * 100 < alpha * total", "'reject': tail * 1000 < alpha * total"),
    ("'tail_count': tail", "'tail_count': seen"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

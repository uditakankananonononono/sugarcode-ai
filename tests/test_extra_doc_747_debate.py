import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import debate as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


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
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: round scoring over supplied rows, no real debate'
    assert len(mod.NOT_CLAIMED) >= 4 and 'rebuttals' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROUNDS, mod.MAX_SCORE, mod.SIDES) == (50, 5, ('pro', 'con'))


def _oracle(rows):
    """Independent: two running sums, winner from a three-way compare."""
    pro = 0
    con = 0
    for side, points in rows:
        if side == 'pro':
            pro = pro + points
        else:
            con = con + points
    if pro > con:
        win = 'pro'
    elif con > pro:
        win = 'con'
    else:
        win = 'draw'
    return {'pro': pro, 'con': con, 'winner': win, 'rounds': len(rows)}


def _core(m):
    assert m.score([('pro', 3), ('con', 2), ('pro', 4)]) == {
        'pro': 7, 'con': 2, 'winner': 'pro', 'rounds': 3}
    # con can take the match
    assert m.score([('pro', 1), ('con', 5)])['winner'] == 'con'
    # matched totals are a draw, including the empty match
    assert m.score([('pro', 2), ('con', 2)])['winner'] == 'draw'
    assert m.score([]) == {'pro': 0, 'con': 0, 'winner': 'draw', 'rounds': 0}
    # zero-score rounds still count as rounds
    assert m.score([('pro', 0), ('con', 0), ('pro', 0)])['rounds'] == 3
    # a lone pro round is a legal match
    assert m.score([('pro', 5)]) == {'pro': 5, 'con': 0, 'winner': 'pro', 'rounds': 1}
    # tuples accepted at every level
    assert m.score((('pro', 1), ('con', 1)))['rounds'] == 2
    rng = random.Random(747)
    for _ in range(400):
        rows = [(('pro' if n % 2 == 0 else 'con'), rng.randint(0, 5))
                for n in range(rng.randint(0, 10))]
        assert m.score(rows) == _oracle(rows)


def _late(m):
    RDS = 'rounds must be a list or tuple'
    CAP = 'rounds must contain at most 50 rows'
    ROW = 'each round must be a (side, points) row'
    SID = 'side must be pro or con'
    PTS = 'points must be an integer from 0 to 5'
    ALT = 'sides must alternate starting with pro'
    good = [('pro', 3)]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, RDS, m.score, bad)
    _raises(TypeError, RDS, m.score, L(good * 51))              # subclass refused before the cap
    _raises(ValueError, CAP, m.score, [('pro' if n % 2 == 0 else 'con', 0) for n in range(51)])
    assert m.score([('pro' if n % 2 == 0 else 'con', 0) for n in range(50)])['rounds'] == 50
    for bad in ('pc', 5, None, ('pro',), ('pro', 3, 'x'), ()):
        _raises(ValueError, ROW, m.score, [bad])
        _raises(ValueError, ROW, m.score, [('pro', 3), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.score, [K(('pro', 3))])
    for bad in ('', 'PRO', 'pro ', 'yes', None, 5, S('pro'), LyingS('pro'), I(0)):
        _raises(ValueError, SID, m.score, [(bad, 3)])
        _raises(ValueError, SID, m.score, [('pro', 3), (bad, 1)])
    for bad in (-1, 6, 100, '3', 3.0, None, True, False, I(3), LyingI(3)):
        _raises(ValueError, PTS, m.score, [('pro', bad)])
        _raises(ValueError, PTS, m.score, [('pro', 1), ('con', bad)])
    assert m.score([('pro', 0)])['pro'] == 0                     # the floor score is legal
    assert m.score([('pro', 5)])['pro'] == 5                     # the cap score is legal
    # alternation: must start with pro, then alternate
    _raises(ValueError, ALT, m.score, [('con', 1)])
    _raises(ValueError, ALT, m.score, [('pro', 1), ('pro', 1)])
    _raises(ValueError, ALT, m.score, [('pro', 1), ('con', 1), ('con', 1)])
    _raises(ValueError, ALT, m.score, [('con', 2), ('con', 2)])
    # order: container, cap, rows (shape, side, points), then alternation
    _raises(TypeError, RDS, m.score, L(good))
    _raises(ValueError, CAP, m.score, [('con', 1)] * 51)
    _raises(ValueError, ROW, m.score, [('pro', 3, 'x')])
    _raises(ValueError, SID, m.score, [(S('pro'), 3)])
    _raises(ValueError, PTS, m.score, [('pro', I(3))])
    _raises(ValueError, PTS, m.score, [('con', 9)])              # rows before alternation
    _raises(ValueError, ALT, m.score, [('con', 1), ('con', 1)])
    # the first bad row reports first
    _raises(ValueError, SID, m.score, [('maybe', 99), ('pro', 3, 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    rounds = [('pro', 3), ('con', 2)]
    assert mod.score(rounds)['winner'] == 'pro'
    assert rounds == [('pro', 3), ('con', 2)]
    assert mod.score(rounds)['rounds'] == 2


MUTANTS = [
    ("    if type(rounds) not in (list, tuple):", "    if not isinstance(rounds, (list, tuple)):"),
    ("    if len(rounds) > MAX_ROUNDS:", "    if len(rounds) >= MAX_ROUNDS:"),
    ("MAX_ROUNDS = 50", "MAX_ROUNDS = 51"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(side) is not str or side not in SIDES:",
     "        if not isinstance(side, str) or side not in SIDES:"),
    ("side not in SIDES", "side not in SIDES[:1]"),
    ("SIDES = ('pro', 'con')", "SIDES = ('pro',)"),
    ("        if type(points) is not int or not 0 <= points <= MAX_SCORE:",
     "        if type(points) is not int or not 0 <= points < MAX_SCORE:"),
    ("not 0 <= points <= MAX_SCORE", "not 1 <= points <= MAX_SCORE"),
    ("MAX_SCORE = 5", "MAX_SCORE = 6"),
    ("    totals = {'pro': 0, 'con': 0}", "    totals = {'pro': 1, 'con': 0}"),
    ("        totals[side] += points", "        totals[side] += 1"),
    ("        totals[side] += points", "        totals['pro'] += points"),
    ("        if side != ('pro' if index % 2 == 0 else 'con'):",
     "        if side != ('pro' if index % 2 == 1 else 'con'):"),
    ("        if side != ('pro' if index % 2 == 0 else 'con'):",
     "        if side != ('con' if index % 2 == 0 else 'pro'):"),
    ("    if totals['pro'] > totals['con']:", "    if totals['pro'] >= totals['con']:"),
    ("    elif totals['pro'] < totals['con']:", "    elif totals['pro'] <= totals['con']:"),
    ("    for index, (side, points) in enumerate(rows):",
     "    for index, (side, points) in enumerate(reversed(rows)):"),
    ("    for side, points in rows:\n        totals[side] += points",
     "    for side, points in rows[1:]:\n        totals[side] += points"),
    ("            'winner': winner, 'rounds': len(rows)}",
     "            'winner': winner, 'rounds': len(rows) + 1}"),
    ("'rounds must be a list or tuple'", "'rounds must be a sequence'"),
    ("'rounds must contain at most 50 rows'", "'rounds must contain at most 49 rows'"),
    ("'each round must be a (side, points) row'", "'each round must be a (side, points) tuple'"),
    ("'side must be pro or con'", "'side must be pro'"),
    ("'points must be an integer from 0 to 5'", "'points must be an integer from 0 to 4'"),
    ("'sides must alternate starting with pro'", "'sides must alternate starting with con'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import voting_design as mod

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
        signal.signal(SIGALRM if False else signal.SIGALRM, previous)
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
    assert mod.SCOPE == 'PARTIAL: Borda tally over supplied ballots, no real election'
    assert len(mod.NOT_CLAIMED) >= 4 and 'strategy' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_BALLOTS, mod.MAX_CANDIDATES, mod.MAX_NAME) == (50, 6, 8)


def _oracle(rows):
    """Independent: award points by slicing the tail, rank with a key."""
    points = {}
    for ballot in rows:
        for position in range(len(ballot)):
            candidate = ballot[position]
            points[candidate] = points.get(candidate, 0) + len(ballot[position + 1:])
    ranked = sorted(points.items(), key=lambda kv: (0 - kv[1], kv[0]))
    return {'points': ranked, 'winner': ranked[0][0] if ranked else None,
            'ballots': len(rows)}


def _core(m):
    # tied mirror ballots fall to the earlier name
    assert m.tally([['x', 'y'], ['y', 'x']]) == {
        'points': [('x', 1), ('y', 1)], 'winner': 'x', 'ballots': 2}
    # a short ballot scores fewer points per position
    assert m.tally([['x', 'y', 'z'], ['x', 'z']]) == {
        'points': [('x', 3), ('y', 1), ('z', 0)], 'winner': 'x', 'ballots': 2}
    assert m.tally([]) == {'points': [], 'winner': None, 'ballots': 0}
    # a single-candidate ballot is a valid shutout
    assert m.tally([['q']]) == {'points': [('q', 0)], 'winner': 'q', 'ballots': 1}
    # a candidate absent from a ballot earns nothing from it
    assert m.tally([['a', 'b'], ['a', 'c']]) == {
        'points': [('a', 2), ('b', 0), ('c', 0)], 'winner': 'a', 'ballots': 2}
    # second places can outscore a first place
    assert m.tally([['a', 'b'], ['b', 'a'], ['b', 'a']]) == {
        'points': [('b', 2), ('a', 1)], 'winner': 'b', 'ballots': 3}
    # tuples accepted at every level
    assert m.tally((('x', 'y'),))['winner'] == 'x'
    rng = random.Random(745)
    for _ in range(400):
        pool = ['a', 'b', 'c', 'dd']
        ballots = [rng.sample(pool, rng.randint(1, len(pool))) for _ in range(rng.randint(0, 8))]
        assert m.tally(ballots) == _oracle(ballots)


def _late(m):
    BAL = 'ballots must be a list or tuple'
    CAP = 'ballots must contain at most 50 rows'
    SHP = 'each ballot must list 1 to 6 candidates'
    NAM = 'candidates must be names of 1 to 8 characters'
    REP = 'a ballot may not repeat a candidate'
    good = [['x']]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, BAL, m.tally, bad)
    _raises(TypeError, BAL, m.tally, L(good * 51))              # subclass refused before the cap
    _raises(ValueError, CAP, m.tally, good * 51)
    assert m.tally(good * 50)['ballots'] == 50
    for bad in ('xy', 5, None, [], ('x',) * 7, L(['x']), T(['x'])):
        _raises(ValueError, SHP, m.tally, [bad])
        _raises(ValueError, SHP, m.tally, [['x'], bad])
    assert m.tally([['c%d' % n for n in range(6)]])['ballots'] == 1
    assert m.tally([['x' * 8, 'y']])['winner'] == 'x' * 8  # a max-length name is fine
    for bad in ('', 'x' * 9, None, 5, b'x', S('x'), LyingS('x'), I(1)):
        _raises(ValueError, NAM, m.tally, [[bad]])
        _raises(ValueError, NAM, m.tally, [['x', bad]])
        _raises(ValueError, NAM, m.tally, [['x'], [bad]])
    _raises(ValueError, REP, m.tally, [['x', 'x']])
    # the first bad ballot reports first
    _raises(ValueError, NAM, m.tally, [[5], ['x', 'x', 'x', 'x', 'x', 'x', 'x']])
    _raises(ValueError, REP, m.tally, [['x', 'y', 'x']])
    _raises(ValueError, REP, m.tally, [['x'], ['a', 'a']])
    # repeats across ballots are fine
    assert m.tally([['x'], ['x']])['ballots'] == 2
    # order: container, cap, shape, names, repeats
    _raises(TypeError, BAL, m.tally, L(good))
    _raises(ValueError, CAP, m.tally, [['x', 'x']] * 51)
    _raises(ValueError, SHP, m.tally, [['x', 'x', 'x', 'x', 'x', 'x', 'x']])
    _raises(ValueError, NAM, m.tally, [[S('x')]])
    _raises(ValueError, NAM, m.tally, [[5, 5]])
    _raises(ValueError, REP, m.tally, [['x', 'x']])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    ballots = [['x', 'y'], ['y', 'x']]
    r = mod.tally(ballots)
    r['points'].append(('bogus', 9))
    assert ballots == [['x', 'y'], ['y', 'x']]
    assert mod.tally(ballots)['points'] == [('x', 1), ('y', 1)]


MUTANTS = [
    ("    if type(ballots) not in (list, tuple):", "    if not isinstance(ballots, (list, tuple)):"),
    ("    if len(ballots) > MAX_BALLOTS:", "    if len(ballots) >= MAX_BALLOTS:"),
    ("MAX_BALLOTS = 50", "MAX_BALLOTS = 51"),
    ("        if type(ballot) not in (list, tuple) or not 1 <= len(ballot) <= MAX_CANDIDATES:",
     "        if not isinstance(ballot, (list, tuple)) or not 1 <= len(ballot) <= MAX_CANDIDATES:"),
    ("not 1 <= len(ballot) <= MAX_CANDIDATES", "not 1 <= len(ballot) < MAX_CANDIDATES"),
    ("not 1 <= len(ballot) <= MAX_CANDIDATES", "not 0 <= len(ballot) <= MAX_CANDIDATES"),
    ("MAX_CANDIDATES = 6", "MAX_CANDIDATES = 7"),
    ("            if type(candidate) is not str or not 1 <= len(candidate) <= MAX_NAME:",
     "            if not isinstance(candidate, str) or not 1 <= len(candidate) <= MAX_NAME:"),
    ("not 1 <= len(candidate) <= MAX_NAME", "not 1 <= len(candidate) < MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("        if len(set(ballot)) != len(ballot):", "        if len(set(ballot)) > len(ballot):"),
    ("            points[candidate] = points.get(candidate, 0) + len(ballot) - 1 - position",
     "            points[candidate] = points.get(candidate, 0) + len(ballot) - position"),
    ("            points[candidate] = points.get(candidate, 0) + len(ballot) - 1 - position",
     "            points[candidate] = points.get(candidate, 0) + position"),
    ("            points[candidate] = points.get(candidate, 0) + len(ballot) - 1 - position",
     "            points[candidate] = points.get(candidate, 1) + len(ballot) - 1 - position"),
    ("    ranked = sorted(points.items(), key=lambda kv: (-kv[1], kv[0]))",
     "    ranked = sorted(points.items(), key=lambda kv: (-kv[1], -len(kv[0])))"),
    ("    ranked = sorted(points.items(), key=lambda kv: (-kv[1], kv[0]))",
     "    ranked = sorted(points.items(), key=lambda kv: kv[1])"),
    ("    return {'points': ranked, 'winner': ranked[0][0] if ranked else None,",
     "    return {'points': ranked, 'winner': ranked[-1][0] if ranked else None,"),
    ("    return {'points': ranked, 'winner': ranked[0][0] if ranked else None,",
     "    return {'points': ranked, 'winner': None,"),
    ("            'ballots': len(rows)}", "            'ballots': len(rows) + 1}"),
    ("    for ballot in rows:\n        for position, candidate in enumerate(ballot):",
     "    for ballot in rows[1:]:\n        for position, candidate in enumerate(ballot):"),
    ("    for ballot in rows:\n        for position, candidate in enumerate(ballot):",
     "    for ballot in rows:\n        for position, candidate in enumerate(reversed(ballot)):"),
    ("        rows.append(list(ballot))", "        rows.append(list(reversed(ballot)))"),
    ("'ballots must be a list or tuple'", "'ballots must be a sequence'"),
    ("'ballots must contain at most 50 rows'", "'ballots must contain at most 49 rows'"),
    ("'each ballot must list 1 to 6 candidates'", "'each ballot must list 1 to 5 candidates'"),
    ("'candidates must be names of 1 to 8 characters'", "'candidates must be names of 1 to 7 characters'"),
    ("'a ballot may not repeat a candidate'", "'a ballot may not repeat a name'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

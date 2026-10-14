import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import two_phase_commit as mod

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
    assert mod.SCOPE == 'PARTIAL: two-phase commit decision over supplied votes, no network or recovery'
    assert len(mod.NOT_CLAIMED) >= 4 and 'crash recovery' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(votes, sc):
    """Independent: index scan with first-bad-index arithmetic."""
    bad = [i for i, (_, v) in enumerate(votes) if v != 'yes']
    names = [n for n, _ in votes]
    last = (bad[0] if (bad and sc) else len(votes) - 1)
    asked = names[:last + 1]
    if not bad:
        return {'decision': 'commit', 'asked': names, 'committed': names, 'aborted': [], 'blocker': None}
    return {'decision': 'abort', 'asked': asked, 'committed': [],
            'aborted': [n for n, v in votes[:last + 1] if v == 'yes'], 'blocker': names[bad[0]]}


def _core(m):
    Y = [('a', 'yes'), ('b', 'yes'), ('c', 'yes')]
    assert m.two_phase_commit(Y) == {'decision': 'commit', 'asked': ['a', 'b', 'c'], 'committed': ['a', 'b', 'c'], 'aborted': [], 'blocker': None}
    assert m.two_phase_commit(Y, False) == m.two_phase_commit(Y, True) == m.two_phase_commit(Y)
    V = [('a', 'yes'), ('b', 'no'), ('c', 'yes'), ('d', 'timeout')]
    assert m.two_phase_commit(V) == {'decision': 'abort', 'asked': ['a', 'b'], 'committed': [], 'aborted': ['a'], 'blocker': 'b'}
    assert m.two_phase_commit(V, True) == m.two_phase_commit(V)
    assert m.two_phase_commit(V, False) == {'decision': 'abort', 'asked': ['a', 'b', 'c', 'd'], 'committed': [], 'aborted': ['a', 'c'], 'blocker': 'b'}
    assert m.two_phase_commit([('a', 'timeout'), ('b', 'yes')]) == {'decision': 'abort', 'asked': ['a'], 'committed': [], 'aborted': [], 'blocker': 'a'}
    assert m.two_phase_commit([('a', 'timeout'), ('b', 'yes')], False) == {'decision': 'abort', 'asked': ['a', 'b'], 'committed': [], 'aborted': ['b'], 'blocker': 'a'}
    assert m.two_phase_commit([('a', 'yes'), ('b', 'yes'), ('c', 'no')]) == {'decision': 'abort', 'asked': ['a', 'b', 'c'], 'committed': [], 'aborted': ['a', 'b'], 'blocker': 'c'}
    assert m.two_phase_commit([('a', 'no')]) == {'decision': 'abort', 'asked': ['a'], 'committed': [], 'aborted': [], 'blocker': 'a'}
    assert m.two_phase_commit([['a', 'yes']])['decision'] == 'commit' and m.two_phase_commit((('a', 'yes'),))['asked'] == ['a']
    assert m.two_phase_commit([('a', 'timeout'), ('b', 'no')], False)['blocker'] == 'a'     # first bad vote, not the last
    assert m.two_phase_commit([('p%d' % i, 'yes') for i in range(8)])['committed'] == ['p%d' % i for i in range(8)]
    assert m.two_phase_commit([('n' * 16, 'yes')])['asked'] == ['n' * 16]
    rng = random.Random(651)
    for _ in range(600):
        n = rng.randint(1, 8)
        vs = [('q%d' % i, rng.choice(['yes', 'yes', 'yes', 'no', 'timeout'])) for i in range(n)]
        sc = rng.random() < .5
        assert m.two_phase_commit(vs, sc) == _oracle(vs, sc), (vs, sc)


def _late(m):
    VT = 'votes must be a list or tuple'
    SZ = 'votes must contain 1 to 8 entries'
    SC = 'short_circuit must be a bool'
    PR = 'each vote must be a (participant, vote) pair'
    NM = 'participants must be strings of 1 to 16 characters'
    DP = 'duplicate participant'
    VV = 'vote must be yes, no or timeout'
    ok = ('a', 'yes')
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, VT, m.two_phase_commit, bad)
    _raises(TypeError, VT, m.two_phase_commit, L([ok] * 9))
    _raises(ValueError, SZ, m.two_phase_commit, [])
    _raises(ValueError, SZ, m.two_phase_commit, [ok] * 9)
    for bad in (1, 0, None, 'True', I(1), [True], 1.0):
        _raises(ValueError, SC, m.two_phase_commit, [ok], bad)
    for K in (L, T):
        for bad in (K(ok), K(('a',))):
            _raises(ValueError, PR, m.two_phase_commit, [bad])
            _raises(ValueError, PR, m.two_phase_commit, [ok, bad])
    for bad in ('ab', None, 5, ('a',), ('a', 'yes', 1), ()):
        _raises(ValueError, PR, m.two_phase_commit, [bad])
        _raises(ValueError, PR, m.two_phase_commit, [ok, bad])
    for bad in ('', 'x' * 17, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, NM, m.two_phase_commit, [(bad, 'yes')])
        _raises(ValueError, NM, m.two_phase_commit, [ok, (bad, 'yes')])
    _raises(ValueError, DP, m.two_phase_commit, [ok, ('a', 'no')])
    _raises(ValueError, DP, m.two_phase_commit, [ok, ('b', 'yes'), ('a', 'yes')])
    for bad in ('', 'YES', 'maybe', None, 5, S('yes'), LyingS('yes'), b'yes', ['yes']):
        _raises(ValueError, VV, m.two_phase_commit, [('b', bad)])
        _raises(ValueError, VV, m.two_phase_commit, [ok, ('b', bad)])
        _raises(ValueError, VV, m.two_phase_commit, [('x', 'no'), ('b', bad)])     # validated even after a no
    # order: type, size, flag, then per vote: shape, participant, duplicate, vote value
    _raises(TypeError, VT, m.two_phase_commit, L([1]), I(1))
    _raises(ValueError, SZ, m.two_phase_commit, [], I(1))
    _raises(ValueError, SC, m.two_phase_commit, [1], 1)
    _raises(ValueError, PR, m.two_phase_commit, [1], True)
    _raises(ValueError, NM, m.two_phase_commit, [(5, 5)])
    _raises(ValueError, DP, m.two_phase_commit, [ok, ('a', 5)])
    _raises(ValueError, VV, m.two_phase_commit, [('b', 5), (5, 'yes')])


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
    def __hash__(self): return hash('yes')


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(votes) not in (list, tuple)", "not isinstance(votes, (list, tuple))"),
    ("not 1 <= len(votes) <= MAX_VOTES", "not 0 <= len(votes) <= MAX_VOTES"),
    ("not 1 <= len(votes) <= MAX_VOTES", "not 1 <= len(votes) < MAX_VOTES"),
    ("MAX_VOTES = 8", "MAX_VOTES = 9"),
    ("short_circuit=True", "short_circuit=False"),
    ("type(short_circuit) is not bool", "not isinstance(short_circuit, (bool, int))"),
    ("type(v) not in (list, tuple) or len(v) != 2", "not isinstance(v, (list, tuple)) or len(v) != 2"),
    ("or len(v) != 2", "or len(v) > 2"),
    ("or len(v) != 2", "or len(v) < 2"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "not isinstance(name, str) or not 1 <= len(name) <= 16"),
    ("not 1 <= len(name) <= 16", "not 0 <= len(name) <= 16"),
    ("not 1 <= len(name) <= 16", "not 1 <= len(name) < 16"),
    ("not 1 <= len(name) <= 16", "not 1 <= len(name) <= 17"),
    ("if name in seen:", "if False:"),
    ("type(vote) is not str or vote not in VOTES", "not isinstance(vote, str) or vote not in VOTES"),
    ("VOTES = ('yes', 'no', 'timeout')", "VOTES = ('yes', 'no')"),
    ("if vote != 'yes' and blocker is None:", "if vote != 'yes':"),
    ("if vote != 'yes' and blocker is None:", "if vote == 'no' and blocker is None:"),
    ("if short_circuit:", "if not short_circuit:"),
    ("if short_circuit:", "if True:"),
    ("asked.append((name, vote))", "pass"),
    ("'committed': names, 'aborted': [], 'blocker': None}", "'committed': [], 'aborted': [], 'blocker': None}"),
    ("if blocker is None:", "if blocker is not None:"),
    ("'aborted': [a[0] for a in asked if a[1] == 'yes']", "'aborted': [a[0] for a in asked]"),
    ("'aborted': [a[0] for a in asked if a[1] == 'yes']", "'aborted': [a[0] for a in asked if a[1] != 'no']"),
    ("'blocker': blocker}", "'blocker': names[-1]}"),
    ("'decision': 'commit'", "'decision': 'abort'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

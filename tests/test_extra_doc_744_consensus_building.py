import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import consensus_building as mod

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
    assert mod.SCOPE == 'PARTIAL: position counting over supplied rows, no real consensus process'
    assert len(mod.NOT_CLAIMED) >= 4 and 'voting' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_MEMBER, mod.POSITIONS) == (100, 8, ('support', 'accept', 'block'))


def _oracle(rows):
    """Independent: one dict per position, consensus restated."""
    counts = {'support': 0, 'accept': 0, 'block': 0}
    for member, position in rows:
        counts[position] = counts[position] + 1
    agreed = counts['block'] == 0 and counts['support'] > 0
    return {'support': counts['support'], 'accept': counts['accept'],
            'block': counts['block'], 'consensus': agreed, 'total': len(rows)}


def _core(m):
    assert m.assess([('a', 'support'), ('b', 'accept')]) == {
        'support': 1, 'accept': 1, 'block': 0, 'consensus': True, 'total': 2}
    # one block defeats consensus even with support
    assert m.assess([('a', 'support'), ('b', 'block')])['consensus'] is False
    # accepts alone never reach consensus
    assert m.assess([('a', 'accept'), ('b', 'accept')])['consensus'] is False
    # a member named zz is not pre-seen
    assert m.assess([('zz', 'support')])['consensus'] is True
    # an empty ballot is no consensus
    assert m.assess([]) == {'support': 0, 'accept': 0, 'block': 0,
                            'consensus': False, 'total': 0}
    # support with zero accepts still reaches consensus
    assert m.assess([('a', 'support')])['consensus'] is True
    # tuples accepted at every level
    assert m.assess((('a', 'support'),))['total'] == 1
    rng = random.Random(744)
    for _ in range(400):
        members = rng.sample(['a', 'b', 'c', 'dd', 'ee'], rng.randint(0, 5))
        rows = [(member, rng.choice(['support', 'accept', 'block'])) for member in members]
        assert m.assess(rows) == _oracle(rows)


def _late(m):
    VTS = 'votes must be a list or tuple'
    CAP = 'votes must contain at most 100 rows'
    ROW = 'each vote must be a (member, position) row'
    MEM = 'member must be a string of 1 to 8 characters'
    POS = 'position must be support, accept, or block'
    DUP = 'each member may vote only once'
    good = [('a', 'support')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, VTS, m.assess, bad)
    _raises(TypeError, VTS, m.assess, L(good * 101))            # subclass refused before the cap
    _raises(ValueError, CAP, m.assess, [('m%d' % n, 'support') for n in range(101)])
    assert m.assess([('m%d' % n, 'support') for n in range(100)])['total'] == 100
    for bad in ('ax', 5, None, ('a',), ('a', 'support', 'x'), (), 'as'):
        _raises(ValueError, ROW, m.assess, [bad])
        _raises(ValueError, ROW, m.assess, [('a', 'support'), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.assess, [K(('a', 'support'))])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, MEM, m.assess, [(bad, 'support')])
        _raises(ValueError, MEM, m.assess, [('a', 'support'), (bad, 'accept')])
    for bad in ('', 'SUPPORT', 'support ', 'yes', None, 5, S('support'), LyingS('support'), I(0)):
        _raises(ValueError, POS, m.assess, [('a', bad)])
        _raises(ValueError, POS, m.assess, [('a', 'support'), ('b', bad)])
    _raises(ValueError, DUP, m.assess, [('a', 'support'), ('a', 'accept')])
    _raises(ValueError, DUP, m.assess, [('a', 'block'), ('b', 'support'), ('a', 'support')])
    assert m.assess([('x' * 8, 'block')])['block'] == 1
    # order: container, cap, rows (shape, member, position), then duplicates
    _raises(TypeError, VTS, m.assess, L(good))
    _raises(ValueError, CAP, m.assess, [('a', 'yes')] * 101)
    _raises(ValueError, ROW, m.assess, [('a', 'support', 'x')])
    _raises(ValueError, MEM, m.assess, [(S('a'), 'support')])
    _raises(ValueError, POS, m.assess, [('a', S('support'))])
    _raises(ValueError, POS, m.assess, [('a', 'yes'), ('a', 'yes')])  # shape/position first
    _raises(ValueError, DUP, m.assess, [('a', 'support'), ('b', 'accept'), ('a', 'block')])
    # the first bad row reports first
    _raises(ValueError, MEM, m.assess, [(5, 'yes'), ('a', 'support', 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    votes = [('a', 'support'), ('b', 'block')]
    assert mod.assess(votes)['consensus'] is False
    assert votes == [('a', 'support'), ('b', 'block')]
    assert mod.assess(votes)['total'] == 2


MUTANTS = [
    ("    if type(votes) not in (list, tuple):", "    if not isinstance(votes, (list, tuple)):"),
    ("    if len(votes) > MAX_ROWS:", "    if len(votes) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(member) is not str or not 1 <= len(member) <= MAX_MEMBER:",
     "        if not isinstance(member, str) or not 1 <= len(member) <= MAX_MEMBER:"),
    ("not 1 <= len(member) <= MAX_MEMBER", "not 1 <= len(member) < MAX_MEMBER"),
    ("MAX_MEMBER = 8", "MAX_MEMBER = 9"),
    ("        if type(position) is not str or position not in POSITIONS:",
     "        if not isinstance(position, str) or position not in POSITIONS:"),
    ("position not in POSITIONS", "position not in POSITIONS[:2]"),
    ("POSITIONS = ('support', 'accept', 'block')", "POSITIONS = ('support', 'accept')"),
    ("        if member in seen:", "        if member not in seen:"),
    ("        seen.add(member)", "        seen.add(position)"),
    ("    counts = {'support': 0, 'accept': 0, 'block': 0}",
     "    counts = {'support': 1, 'accept': 0, 'block': 0}"),
    ("        counts[position] += 1", "        counts[position] += 2"),
    ("        counts[position] += 1", "        counts['support'] += 1"),
    ("            'consensus': counts['block'] == 0 and counts['support'] >= 1,",
     "            'consensus': counts['block'] == 0 and counts['support'] >= 2,"),
    ("            'consensus': counts['block'] == 0 and counts['support'] >= 1,",
     "            'consensus': counts['block'] == 0 or counts['support'] >= 1,"),
    ("            'consensus': counts['block'] == 0 and counts['support'] >= 1,",
     "            'consensus': counts['block'] <= 1 and counts['support'] >= 1,"),
    ("'votes must be a list or tuple'", "'votes must be a sequence'"),
    ("'votes must contain at most 100 rows'", "'votes must contain at most 99 rows'"),
    ("'each vote must be a (member, position) row'", "'each vote must be a (member, position) tuple'"),
    ("'member must be a string of 1 to 8 characters'", "'member must be a string of 1 to 7 characters'"),
    ("'position must be support, accept, or block'", "'position must be support or accept'"),
    ("'each member may vote only once'", "'each member may vote once'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

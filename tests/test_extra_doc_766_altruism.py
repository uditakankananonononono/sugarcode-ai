import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import altruism as mod

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
    assert mod.SCOPE == 'PARTIAL: act ledger over supplied rows, no real altruism'
    assert len(mod.NOT_CLAIMED) >= 4 and 'ethics' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_NAME) == (100, 8)


def _oracle(rows):
    """Independent: per-giver counts in a dict, best by scanning sorted names."""
    counts = {}
    for giver, receiver in rows:
        counts[giver] = counts.get(giver, 0) + 1
    most = None
    best = -1
    for giver in sorted(counts):
        if counts[giver] > best:
            best = counts[giver]
            most = giver
    return {'acts': len(rows), 'givers': len(counts), 'most_generous': most}


def _core(m):
    assert m.ledger([('amy', 'bo'), ('amy', 'cy'), ('bo', 'amy')]) == {
        'acts': 3, 'givers': 2, 'most_generous': 'amy'}
    assert m.ledger([]) == {'acts': 0, 'givers': 0, 'most_generous': None}
    # ties break alphabetically, not by first appearance
    assert m.ledger([('zz', 'a'), ('aa', 'b')])['most_generous'] == 'aa'
    # receivers do not count as givers
    assert m.ledger([('amy', 'bo'), ('amy', 'cy')])['givers'] == 1
    # giving back and forth counts both ways
    assert m.ledger([('a', 'b'), ('b', 'a')])['givers'] == 2
    # ties between reversal cousins break on the real name
    assert m.ledger([('ab', 'x'), ('ba', 'y')])['most_generous'] == 'ab'
    # repeated identical acts all count
    assert m.ledger([('a', 'b'), ('a', 'b')])['acts'] == 2
    # one act makes its giver the most generous
    assert m.ledger([('solo', 'other')])['most_generous'] == 'solo'
    # tuples accepted at every level
    assert m.ledger((('a', 'b'),))['acts'] == 1
    rng = random.Random(766)
    for _ in range(400):
        rows = []
        for _ in range(rng.randint(0, 10)):
            giver = rng.choice(['a', 'b', 'cy'])
            receiver = rng.choice(['a', 'b', 'cy'])
            if giver != receiver:
                rows.append((giver, receiver))
        assert m.ledger(rows) == _oracle(rows)


def _late(m):
    ACT = 'acts must be a list or tuple'
    CAP = 'acts must contain at most 100 rows'
    ROW = 'each act must be a (giver, receiver) row'
    GIV = 'giver must be a string of 1 to 8 characters'
    REC = 'receiver must be a string of 1 to 8 characters'
    DIF = 'giver and receiver must differ'
    good = [('a', 'b')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, ACT, m.ledger, bad)
    _raises(TypeError, ACT, m.ledger, L(good * 101))            # subclass refused before the cap
    _raises(ValueError, CAP, m.ledger, good * 101)
    assert m.ledger(good * 100)['acts'] == 100
    for bad in ('ab', 5, None, ('a',), ('a', 'b', 'x'), ()):
        _raises(ValueError, ROW, m.ledger, [bad])
        _raises(ValueError, ROW, m.ledger, [('a', 'b'), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.ledger, [K(('a', 'b'))])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, GIV, m.ledger, [(bad, 'b')])
        _raises(ValueError, GIV, m.ledger, [('a', 'b'), (bad, 'c')])
    for bad in ('', 'x' * 9, None, 5, b'b', S('b'), LyingS('b'), I(1)):
        _raises(ValueError, REC, m.ledger, [('a', bad)])
        _raises(ValueError, REC, m.ledger, [('a', 'b'), ('c', bad)])
    assert m.ledger([('x' * 8, 'y' * 8)])['acts'] == 1
    assert m.ledger([('x', 'y')])['acts'] == 1                   # single-character names accepted
    _raises(ValueError, DIF, m.ledger, [('a', 'a')])
    _raises(ValueError, DIF, m.ledger, [(''.join(['a', 'b']), 'ab')])  # equal by value, not identity
    _raises(ValueError, DIF, m.ledger, [('a', 'b'), ('cc', 'cc')])
    # order: container, cap, rows (shape, giver, receiver, differ)
    _raises(TypeError, ACT, m.ledger, L(good))
    _raises(ValueError, CAP, m.ledger, [('a', 'a')] * 101)
    _raises(ValueError, ROW, m.ledger, [('a', 'b', 'x')])
    _raises(ValueError, GIV, m.ledger, [(S('a'), 'b')])
    _raises(ValueError, REC, m.ledger, [('a', S('b'))])
    _raises(ValueError, REC, m.ledger, [('a', S('a'))])        # fields before the differ check
    # the first bad row reports first
    _raises(ValueError, GIV, m.ledger, [(5, 5), ('a', 'b', 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    acts = [('a', 'b'), ('a', 'c')]
    assert mod.ledger(acts)['most_generous'] == 'a'
    assert acts == [('a', 'b'), ('a', 'c')]
    assert mod.ledger(acts)['givers'] == 1


MUTANTS = [
    ("    if type(acts) not in (list, tuple):", "    if not isinstance(acts, (list, tuple)):"),
    ("    if len(acts) > MAX_ROWS:", "    if len(acts) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(giver) is not str or not 1 <= len(giver) <= MAX_NAME:",
     "        if not isinstance(giver, str) or not 1 <= len(giver) <= MAX_NAME:"),
    ("not 1 <= len(giver) <= MAX_NAME", "not 1 <= len(giver) < MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("        if type(receiver) is not str or not 1 <= len(receiver) <= MAX_NAME:",
     "        if not isinstance(receiver, str) or not 1 <= len(receiver) <= MAX_NAME:"),
    ("        if giver == receiver:", "        if giver != receiver:"),
    ("    counts = {}", "    counts = {'zz': 1}"),
    ("        counts[giver] = counts.get(giver, 0) + 1", "        counts[giver] = counts.get(giver, 0)"),
    ("        counts[giver] = counts.get(giver, 0) + 1", "        counts[receiver] = counts.get(receiver, 0) + 1"),
    ("        most = min(counts, key=lambda giver: (-counts[giver], giver))",
     "        most = min(counts, key=lambda giver: (counts[giver], giver))"),
    ("        most = min(counts, key=lambda giver: (-counts[giver], giver))",
     "        most = max(counts, key=lambda giver: (-counts[giver], giver))"),
    ("        most = min(counts, key=lambda giver: (-counts[giver], giver))",
     "        most = min(counts)"),
    ("    most = None", "    most = 'nobody'"),
    ("    return {'acts': len(rows), 'givers': len(counts), 'most_generous': most}",
     "    return {'acts': len(rows) + 1, 'givers': len(counts), 'most_generous': most}"),
    ("    return {'acts': len(rows), 'givers': len(counts), 'most_generous': most}",
     "    return {'acts': len(rows), 'givers': len(rows), 'most_generous': most}"),
    ("    for giver, receiver in rows:\n        counts[giver] = counts.get(giver, 0) + 1",
     "    for giver, receiver in rows[1:]:\n        counts[giver] = counts.get(giver, 0) + 1"),
    ("'acts must be a list or tuple'", "'acts must be a sequence'"),
    ("'acts must contain at most 100 rows'", "'acts must contain at most 99 rows'"),
    ("'each act must be a (giver, receiver) row'", "'each act must be a (giver, receiver) tuple'"),
    ("'giver must be a string of 1 to 8 characters'", "'giver must be a string of 1 to 7 characters'"),
    ("'receiver must be a string of 1 to 8 characters'", "'receiver must be a string of 1 to 7 characters'"),
    ("'giver and receiver must differ'", "'giver and receiver must match'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

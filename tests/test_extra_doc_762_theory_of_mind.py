import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import theory_of_mind as mod

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
    assert mod.SCOPE == "PARTIAL: belief pooling over supplied rows, no real theory of mind"
    assert len(mod.NOT_CLAIMED) >= 4 and 'deception' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_HOLDER, mod.MAX_CLAIM) == (50, 8, 20)


def _oracle(rows):
    """Independent: list-based uniqueness, holder sets per claim in a plain dict."""
    unique = []
    for row in rows:
        if row not in unique:
            unique.append(row)
    holders = []
    for holder, claim in rows:
        if holder not in holders:
            holders.append(holder)
    shared = []
    for holder, claim in rows:
        whos = []
        for holder2, claim2 in rows:
            if claim2 == claim and holder2 not in whos:
                whos.append(holder2)
        if len(whos) >= 2 and claim not in shared:
            shared.append(claim)
    return {'beliefs': unique, 'holders': len(holders),
            'shared': sorted(shared), 'total': len(rows)}


def _core(m):
    assert m.infer([('amy', 'sky is blue'), ('bo', 'sky is blue'),
                    ('amy', 'cats rule'), ('amy', 'sky is blue')]) == {
        'beliefs': [('amy', 'sky is blue'), ('bo', 'sky is blue'), ('amy', 'cats rule')],
        'holders': 2, 'shared': ['sky is blue'], 'total': 4}
    assert m.infer([]) == {'beliefs': [], 'holders': 0, 'shared': [], 'total': 0}
    # a claim held by one holder twice is not shared
    assert m.infer([('amy', 'x'), ('amy', 'x')])['shared'] == []
    # shared claims come back sorted
    assert m.infer([('a', 'zz'), ('b', 'zz'), ('a', 'mm'), ('b', 'mm')])['shared'] == ['mm', 'zz']
    # beliefs keep first-seen order, not sorted
    assert m.infer([('a', 'zz'), ('a', 'mm')])['beliefs'] == [('a', 'zz'), ('a', 'mm')]
    # the same claim from two holders counts once per holder
    assert m.infer([('a', 'x'), ('b', 'x'), ('a', 'x')])['beliefs'] == [('a', 'x'), ('b', 'x')]
    # a claim held by one holder only is never shared, even named zz
    assert m.infer([('amy', 'zz')])['shared'] == []
    # holders counts distinct names only
    assert m.infer([('a', 'x'), ('a', 'y'), ('b', 'z')])['holders'] == 2
    # tuples accepted at every level
    assert m.infer((('a', 'x'),))['total'] == 1
    rng = random.Random(762)
    for _ in range(400):
        rows = [(rng.choice(['a', 'b', 'cy']), 'c%d' % rng.randint(0, 4))
                for _ in range(rng.randint(0, 10))]
        assert m.infer(rows) == _oracle(rows)


def _late(m):
    BLF = 'beliefs must be a list or tuple'
    CAP = 'beliefs must contain at most 50 rows'
    ROW = 'each belief must be a (holder, claim) row'
    HOL = 'holder must be a string of 1 to 8 characters'
    CLM = 'claim must be a string of 1 to 20 characters'
    good = [('a', 'x')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, BLF, m.infer, bad)
    _raises(TypeError, BLF, m.infer, L(good * 51))              # subclass refused before the cap
    _raises(ValueError, CAP, m.infer, good * 51)
    assert m.infer(good * 50)['total'] == 50
    for bad in ('ax', 5, None, ('a',), ('a', 'x', 'y'), ()):
        _raises(ValueError, ROW, m.infer, [bad])
        _raises(ValueError, ROW, m.infer, [('a', 'x'), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.infer, [K(('a', 'x'))])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, HOL, m.infer, [(bad, 'x')])
        _raises(ValueError, HOL, m.infer, [('a', 'x'), (bad, 'y')])
    for bad in ('', 'x' * 21, None, 5, b'x', S('x'), LyingS('x'), I(1)):
        _raises(ValueError, CLM, m.infer, [('a', bad)])
        _raises(ValueError, CLM, m.infer, [('a', 'x'), ('b', bad)])
    assert m.infer([('x' * 8, 'x' * 20)])['total'] == 1
    assert m.infer([('x', 'x')])['total'] == 1                   # single-character values accepted
    # order: container, cap, rows (shape, holder, claim)
    _raises(TypeError, BLF, m.infer, L(good))
    _raises(ValueError, CAP, m.infer, [('a', 1, 2)] * 51)
    _raises(ValueError, ROW, m.infer, [('a', 'x', 'y')])
    _raises(ValueError, HOL, m.infer, [(S('a'), 'x')])
    _raises(ValueError, CLM, m.infer, [('a', S('x'))])
    # the first bad row reports first
    _raises(ValueError, HOL, m.infer, [(5, 6), ('a', 'x', 'y')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    beliefs = [('a', 'x'), ('b', 'x')]
    r = mod.infer(beliefs)
    r['beliefs'].append(('bogus', 'zz'))
    assert beliefs == [('a', 'x'), ('b', 'x')]
    assert mod.infer(beliefs)['shared'] == ['x']


MUTANTS = [
    ("    if type(beliefs) not in (list, tuple):", "    if not isinstance(beliefs, (list, tuple)):"),
    ("    if len(beliefs) > MAX_ROWS:", "    if len(beliefs) >= MAX_ROWS:"),
    ("MAX_ROWS = 50", "MAX_ROWS = 51"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(holder) is not str or not 1 <= len(holder) <= MAX_HOLDER:",
     "        if not isinstance(holder, str) or not 1 <= len(holder) <= MAX_HOLDER:"),
    ("not 1 <= len(holder) <= MAX_HOLDER", "not 1 <= len(holder) < MAX_HOLDER"),
    ("MAX_HOLDER = 8", "MAX_HOLDER = 9"),
    ("        if type(claim) is not str or not 1 <= len(claim) <= MAX_CLAIM:",
     "        if not isinstance(claim, str) or not 1 <= len(claim) <= MAX_CLAIM:"),
    ("not 1 <= len(claim) <= MAX_CLAIM", "not 1 <= len(claim) < MAX_CLAIM"),
    ("MAX_CLAIM = 20", "MAX_CLAIM = 21"),
    ("        if (holder, claim) not in seen:", "        if (holder, claim) in seen:"),
    ("            unique.append((holder, claim))", "            unique.append((claim, holder))"),
    ("            unique.append((holder, claim))", "            unique.insert(0, (holder, claim))"),
    ("        holders.add(holder)", "        holders.add(claim)"),
    ("        by_claim.setdefault(claim, set()).add(holder)",
     "        by_claim.setdefault(claim, set()).add(claim)"),
    ("    shared = sorted(claim for claim, whos in by_claim.items() if len(whos) >= 2)",
     "    shared = sorted(claim for claim, whos in by_claim.items() if len(whos) >= 1)"),
    ("    shared = sorted(claim for claim, whos in by_claim.items() if len(whos) >= 2)",
     "    shared = sorted(claim for claim, whos in by_claim.items() if len(whos) >= 3)"),
    ("    shared = sorted(claim for claim, whos in by_claim.items() if len(whos) >= 2)",
     "    shared = [claim for claim, whos in by_claim.items() if len(whos) >= 2]"),
    ("    return {'beliefs': unique, 'holders': len(holders),",
     "    return {'beliefs': unique, 'holders': len(unique),"),
    ("            'shared': shared, 'total': len(rows)}",
     "            'shared': shared, 'total': len(unique)}"),
    ("    for holder, claim in rows:\n        if (holder, claim) not in seen:",
     "    for holder, claim in rows[1:]:\n        if (holder, claim) not in seen:"),
    ("'beliefs must be a list or tuple'", "'beliefs must be a sequence'"),
    ("'beliefs must contain at most 50 rows'", "'beliefs must contain at most 49 rows'"),
    ("'each belief must be a (holder, claim) row'", "'each belief must be a (holder, claim) tuple'"),
    ("'holder must be a string of 1 to 8 characters'", "'holder must be a string of 1 to 7 characters'"),
    ("'claim must be a string of 1 to 20 characters'", "'claim must be a string of 1 to 19 characters'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

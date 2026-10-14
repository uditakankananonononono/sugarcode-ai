import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import compassion as mod

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
    assert mod.SCOPE == 'PARTIAL: severity ordering over supplied cases, no real compassion'
    assert len(mod.NOT_CLAIMED) >= 4 and 'medicine' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_CASE, mod.MAX_SEVERITY) == (100, 8, 5)


def _oracle(rows):
    """Independent: selection-sort by severity then name, threshold loop."""
    remaining = list(rows)
    order = []
    while remaining:
        best = remaining[0]
        for row in remaining[1:]:
            if (0 - row[1], row[0]) < (0 - best[1], best[0]):
                best = row
        order.append(best[0])
        remaining.remove(best)
    critical = 0
    for case, severity in rows:
        if severity >= 4:
            critical += 1
    return {'order': order, 'critical': critical, 'total': len(rows)}


def _core(m):
    assert m.triage([('broken', 4), ('scratch', 1), ('sprain', 4), ('ache', 2)]) == {
        'order': ['broken', 'sprain', 'ache', 'scratch'], 'critical': 2, 'total': 4}
    assert m.triage([]) == {'order': [], 'critical': 0, 'total': 0}
    # ties break by name, not by input order
    assert m.triage([('zz', 3), ('aa', 3)])['order'] == ['aa', 'zz']
    # severity 3 is not critical, 4 is
    assert m.triage([('a', 3), ('b', 4)])['critical'] == 1
    assert m.triage([('a', 5), ('b', 5)])['critical'] == 2
    # a higher severity from a later row leads
    assert m.triage([('aaa', 1), ('zzz', 5)])['order'] == ['zzz', 'aaa']
    # one case is its own order
    assert m.triage([('solo', 2)]) == {'order': ['solo'], 'critical': 0, 'total': 1}
    # tuples accepted at every level
    assert m.triage((('solo', 4),))['critical'] == 1
    rng = random.Random(765)
    for _ in range(400):
        n = rng.randint(0, 8)
        cases = rng.sample(['c%d' % k for k in range(10)], n)
        rows = [(case, rng.randint(1, 5)) for case in cases]
        assert m.triage(rows) == _oracle(rows)


def _late(m):
    CAS = 'cases must be a list or tuple'
    CAP = 'cases must contain at most 100 rows'
    ROW = 'each case must be a (case, severity) row'
    NAM = 'case must be a string of 1 to 8 characters'
    SEV = 'severity must be an integer from 1 to 5'
    DUP = 'each case may appear only once'
    good = [('a', 3)]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, CAS, m.triage, bad)
    _raises(TypeError, CAS, m.triage, L(good * 101))            # subclass refused before the cap
    _raises(ValueError, CAP, m.triage, [('c%d' % n, 3) for n in range(101)])
    assert m.triage([('c%d' % n, 3) for n in range(100)])['total'] == 100
    for bad in ('a3', 5, None, ('a',), ('a', 3, 'x'), ()):
        _raises(ValueError, ROW, m.triage, [bad])
        _raises(ValueError, ROW, m.triage, [('a', 3), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.triage, [K(('a', 3))])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, NAM, m.triage, [(bad, 3)])
        _raises(ValueError, NAM, m.triage, [('a', 3), (bad, 1)])
    for bad in (0, 6, -1, 100, '3', 3.0, None, True, False, I(3), LyingI(3)):
        _raises(ValueError, SEV, m.triage, [('a', bad)])
        _raises(ValueError, SEV, m.triage, [('a', 1), ('b', bad)])
    assert m.triage([('x' * 8, 5)])['critical'] == 1
    assert m.triage([('x', 1)])['total'] == 1                    # single-character case accepted
    _raises(ValueError, DUP, m.triage, [('a', 3), ('a', 4)])
    _raises(ValueError, DUP, m.triage, [('a', 1), ('b', 2), ('a', 3)])
    # order: container, cap, rows (shape, case, severity), then duplicates
    _raises(TypeError, CAS, m.triage, L(good))
    _raises(ValueError, CAP, m.triage, [('a', 9)] * 101)
    _raises(ValueError, ROW, m.triage, [('a', 3, 'x')])
    _raises(ValueError, NAM, m.triage, [(S('a'), 3)])
    _raises(ValueError, SEV, m.triage, [('a', I(3))])
    _raises(ValueError, SEV, m.triage, [('a', 9), ('a', 9)])     # rows before duplicates
    # the first bad row reports first
    _raises(ValueError, NAM, m.triage, [(5, 99), ('a', 3, 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    cases = [('a', 4), ('b', 1)]
    r = mod.triage(cases)
    r['order'].append('bogus')
    assert cases == [('a', 4), ('b', 1)]
    assert mod.triage(cases)['order'] == ['a', 'b']


MUTANTS = [
    ("    if type(cases) not in (list, tuple):", "    if not isinstance(cases, (list, tuple)):"),
    ("    if len(cases) > MAX_ROWS:", "    if len(cases) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(case) is not str or not 1 <= len(case) <= MAX_CASE:",
     "        if not isinstance(case, str) or not 1 <= len(case) <= MAX_CASE:"),
    ("not 1 <= len(case) <= MAX_CASE", "not 1 <= len(case) < MAX_CASE"),
    ("MAX_CASE = 8", "MAX_CASE = 9"),
    ("        if type(severity) is not int or not 1 <= severity <= MAX_SEVERITY:",
     "        if type(severity) is not int or not 1 <= severity < MAX_SEVERITY:"),
    ("not 1 <= severity <= MAX_SEVERITY", "not 0 <= severity <= MAX_SEVERITY"),
    ("MAX_SEVERITY = 5", "MAX_SEVERITY = 6"),
    ("        if case in seen:", "        if case not in seen:"),
    ("        seen.add(case)", "        seen.add(severity)"),
    ("    order = [case for case, severity in sorted(rows, key=lambda kv: (-kv[1], kv[0]))]",
     "    order = [case for case, severity in sorted(rows, key=lambda kv: (kv[1], kv[0]))]"),
    ("    order = [case for case, severity in sorted(rows, key=lambda kv: (-kv[1], kv[0]))]",
     "    order = [case for case, severity in sorted(rows, key=lambda kv: (-kv[1], -len(kv[0])))]"),
    ("    order = [case for case, severity in sorted(rows, key=lambda kv: (-kv[1], kv[0]))]",
     "    order = [case for case, severity in sorted(rows, key=lambda kv: kv[0])]"),
    ("    critical = sum(1 for case, severity in rows if severity >= 4)",
     "    critical = sum(1 for case, severity in rows if severity >= 5)"),
    ("    critical = sum(1 for case, severity in rows if severity >= 4)",
     "    critical = sum(1 for case, severity in rows if severity > 4)"),
    ("    critical = sum(1 for case, severity in rows if severity >= 4)",
     "    critical = sum(2 for case, severity in rows if severity >= 4)"),
    ("    for case, severity in rows:\n        if case in seen:",
     "    for case, severity in rows[:1]:\n        if case in seen:"),
    ("    return {'order': order, 'critical': critical, 'total': len(rows)}",
     "    return {'order': order, 'critical': critical, 'total': len(rows) + 1}"),
    ("'cases must be a list or tuple'", "'cases must be a sequence'"),
    ("'cases must contain at most 100 rows'", "'cases must contain at most 99 rows'"),
    ("'each case must be a (case, severity) row'", "'each case must be a (case, severity) tuple'"),
    ("'case must be a string of 1 to 8 characters'", "'case must be a string of 1 to 7 characters'"),
    ("'severity must be an integer from 1 to 5'", "'severity must be an integer from 1 to 4'"),
    ("'each case may appear only once'", "'each case may appear twice'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

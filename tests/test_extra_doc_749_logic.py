import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import logic as mod

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
    assert mod.SCOPE == 'PARTIAL: propositional modus ponens over supplied facts and rules'
    assert len(mod.NOT_CLAIMED) >= 4 and 'negation' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_FACTS, mod.MAX_RULES, mod.MAX_SYMBOL, mod.MAX_PASSES) == (20, 20, 8, 25)


def _oracle(facts, rows):
    """Independent: list-based known set, one rule sweep per pass."""
    known = list(facts)
    passes = 0
    while True:
        added = False
        for antecedent, consequent in rows:
            if antecedent in known and consequent not in known:
                known.append(consequent)
                added = True
        passes += 1
        if not added:
            break
    initial = set(facts)
    return {'derived': sorted([f for f in known if f not in initial]),
            'passes': passes, 'total': len(known)}


def _core(m):
    # an in-order chain resolves in one productive pass plus the quiet pass
    assert m.derive(['a'], [('a', 'b'), ('b', 'c')]) == {
        'derived': ['b', 'c'], 'passes': 2, 'total': 3}
    # a reversed chain needs one pass per step
    assert m.derive(['x'], [('w', 'v'), ('y', 'w'), ('x', 'y')]) == {
        'derived': ['v', 'w', 'y'], 'passes': 4, 'total': 4}
    # unreachable rules fire nothing; the quiet pass still counts
    assert m.derive(['a'], [('b', 'c')]) == {'derived': [], 'passes': 1, 'total': 1}
    assert m.derive(['a'], []) == {'derived': [], 'passes': 1, 'total': 1}
    assert m.derive([], [('a', 'b')]) == {'derived': [], 'passes': 1, 'total': 0}
    # a rule whose antecedent is a fact fires
    assert m.derive(['p'], [('p', 'q')]) == {'derived': ['q'], 'passes': 2, 'total': 2}
    # derived facts come back sorted
    assert m.derive(['a'], [('a', 'zz'), ('a', 'mm')])['derived'] == ['mm', 'zz']
    # duplicate facts collapse
    assert m.derive(['a', 'a'], [('a', 'b')])['total'] == 2
    # a rule firing back into a known fact adds nothing
    assert m.derive(['a', 'b'], [('a', 'b')]) == {'derived': [], 'passes': 1, 'total': 2}
    # a cycle terminates: a->b, b->a
    assert m.derive(['a'], [('a', 'b'), ('b', 'a')]) == {'derived': ['b'], 'passes': 2, 'total': 2}
    # a fully reversed 20-rule chain needs all 21 passes
    chain = [('g%d' % n, 'g%d' % (n + 1)) for n in range(19, -1, -1)]
    assert m.derive(['g0'], chain) == {
        'derived': sorted('g%d' % n for n in range(1, 21)), 'passes': 21, 'total': 21}
    assert m.derive(['g0'], chain) == _oracle(['g0'], chain)
    # tuples accepted at every level
    assert m.derive(('a',), (('a', 'b'),))['derived'] == ['b']
    rng = random.Random(749)
    for _ in range(400):
        pool = ['a', 'b', 'c', 'd', 'e']
        facts = rng.sample(pool, rng.randint(0, 2))
        rows = [(rng.choice(pool), rng.choice(pool)) for _ in range(rng.randint(0, 8))]
        assert m.derive(facts, rows) == _oracle(facts, rows)


def _late(m):
    FTS = 'facts must be a list or tuple'
    FCP = 'facts must contain at most 20 entries'
    FST = 'facts must be strings of 1 to 8 characters'
    RLS = 'rules must be a list or tuple'
    RCP = 'rules must contain at most 20 rows'
    ROW = 'each rule must be an (antecedent, consequent) row'
    ANT = 'antecedent must be a string of 1 to 8 characters'
    CON = 'consequent must be a string of 1 to 8 characters'
    goodf = ['a']
    goodr = [('a', 'b')]
    for bad in ('ab', None, 5, {}, L(goodf), T(goodf), L(), T()):
        _raises(TypeError, FTS, m.derive, bad, [])
    _raises(TypeError, FTS, m.derive, L(goodf * 21), [])        # subclass refused before the cap
    _raises(ValueError, FCP, m.derive, goodf * 21, [])
    assert m.derive(goodf * 20, [])['total'] == 1
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, FST, m.derive, [bad], [])
        _raises(ValueError, FST, m.derive, ['a', bad], [])
    for bad in ('ab', None, 5, {}, L(goodr), T(goodr), L(), T()):
        _raises(TypeError, RLS, m.derive, [], bad)
    _raises(TypeError, RLS, m.derive, [], L(goodr * 21))
    _raises(ValueError, RCP, m.derive, [], goodr * 21)
    assert m.derive(['a'], goodr * 20)['passes'] == 2
    for bad in ('ab', 5, None, ('a',), ('a', 'b', 'c'), ()):
        _raises(ValueError, ROW, m.derive, [], [bad])
        _raises(ValueError, ROW, m.derive, [], [('a', 'b'), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.derive, [], [K(('a', 'b'))])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, ANT, m.derive, [], [(bad, 'b')])
        _raises(ValueError, ANT, m.derive, [], [('a', 'b'), (bad, 'c')])
        _raises(ValueError, CON, m.derive, [], [('a', bad)])
        _raises(ValueError, CON, m.derive, [], [('a', 'b'), ('c', bad)])
    assert m.derive(['x' * 8], [('x' * 8, 'y' * 8)])['total'] == 2
    # order: facts before rules; within each: container, cap, entries
    _raises(TypeError, FTS, m.derive, L(goodf), L(goodr))
    _raises(ValueError, FST, m.derive, [S('a')], [('a', 5)])
    _raises(ValueError, FCP, m.derive, [5] * 21, [('a', 5)])
    _raises(TypeError, RLS, m.derive, [], L(goodr))
    _raises(ValueError, RCP, m.derive, [], [('a', 5, 6)] * 21)
    _raises(ValueError, ROW, m.derive, [], [('a', 'b', 'c')])
    _raises(ValueError, ANT, m.derive, [], [(S('a'), 'b')])
    _raises(ValueError, CON, m.derive, [], [('a', S('b'))])
    # the first bad rule reports first
    _raises(ValueError, ANT, m.derive, [], [(5, 6), ('a', 'b', 'c')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    facts = ['a']
    rules = [('a', 'b'), ('b', 'c')]
    r = m = mod.derive(facts, rules)
    r['derived'].append('bogus')
    assert facts == ['a'] and rules == [('a', 'b'), ('b', 'c')]
    assert mod.derive(facts, rules)['derived'] == ['b', 'c']


MUTANTS = [
    ("    if type(facts) not in (list, tuple):", "    if not isinstance(facts, (list, tuple)):"),
    ("    if len(facts) > MAX_FACTS:", "    if len(facts) >= MAX_FACTS:"),
    ("MAX_FACTS = 20", "MAX_FACTS = 21"),
    ("        if type(fact) is not str or not 1 <= len(fact) <= MAX_SYMBOL:",
     "        if not isinstance(fact, str) or not 1 <= len(fact) <= MAX_SYMBOL:"),
    ("MAX_SYMBOL = 8", "MAX_SYMBOL = 9"),
    ("    if type(rules) not in (list, tuple):", "    if not isinstance(rules, (list, tuple)):"),
    ("    if len(rules) > MAX_RULES:", "    if len(rules) >= MAX_RULES:"),
    ("MAX_RULES = 20", "MAX_RULES = 21"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(antecedent) is not str or not 1 <= len(antecedent) <= MAX_SYMBOL:",
     "        if not isinstance(antecedent, str) or not 1 <= len(antecedent) <= MAX_SYMBOL:"),
    ("        if type(consequent) is not str or not 1 <= len(consequent) <= MAX_SYMBOL:",
     "        if not isinstance(consequent, str) or not 1 <= len(consequent) <= MAX_SYMBOL:"),
    ("    known = set(facts)", "    known = set(facts + ['zz'])"),
    ("    passes = 0", "    passes = 1"),
    ("    while passes < MAX_PASSES:", "    while passes < 20:"),
    ("            if antecedent in known and consequent not in known:",
     "            if antecedent in known or consequent not in known:"),
    ("            if antecedent in known and consequent not in known:",
     "            if antecedent not in known and consequent not in known:"),
    ("                known.add(consequent)", "                known.add(antecedent)"),
    ("        for antecedent, consequent in rows:",
     "        for antecedent, consequent in reversed(rows):"),
    ("    return {'derived': sorted(known - set(facts)), 'passes': passes,",
     "    return {'derived': sorted(known), 'passes': passes,"),
    ("    return {'derived': sorted(known - set(facts)), 'passes': passes,",
     "    return {'derived': sorted(known - set(facts), reverse=True), 'passes': passes,"),
    ("            'total': len(known)}", "            'total': len(known) + 1}"),
    ("'facts must be a list or tuple'", "'facts must be a sequence'"),
    ("'facts must contain at most 20 entries'", "'facts must contain at most 19 entries'"),
    ("'facts must be strings of 1 to 8 characters'", "'facts must be strings of 1 to 7 characters'"),
    ("'rules must be a list or tuple'", "'rules must be a sequence'"),
    ("'rules must contain at most 20 rows'", "'rules must contain at most 19 rows'"),
    ("'each rule must be an (antecedent, consequent) row'",
     "'each rule must be an (antecedent, consequent) tuple'"),
    ("'antecedent must be a string of 1 to 8 characters'",
     "'antecedent must be a string of 1 to 7 characters'"),
    ("'consequent must be a string of 1 to 8 characters'",
     "'consequent must be a string of 1 to 7 characters'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import prosocial_behavior as mod

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
    assert mod.SCOPE == 'PARTIAL: benefit totaling over supplied rows, no real prosocial behavior'
    assert len(mod.NOT_CLAIMED) >= 4 and 'volunteering' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_ACTOR, mod.MAX_PEOPLE) == (100, 8, 10)


def _oracle(rows):
    """Independent: totals in a dict, top by scanning sorted names."""
    totals = {}
    helped = 0
    for actor, people in rows:
        totals[actor] = totals.get(actor, 0) + people
        helped = helped + people
    top = None
    best = -1
    for actor in sorted(totals):
        if totals[actor] > best:
            best = totals[actor]
            top = actor
    return {'acts': len(rows), 'helped': helped,
            'actors': len(totals), 'top': top}


def _core(m):
    assert m.benefit([('amy', 3), ('bo', 5), ('amy', 4)]) == {
        'acts': 3, 'helped': 12, 'actors': 2, 'top': 'amy'}
    assert m.benefit([]) == {'acts': 0, 'helped': 0, 'actors': 0, 'top': None}
    # totals decide the top, not act counts: one big act beats two small ones
    assert m.benefit([('amy', 9), ('bo', 2), ('bo', 2)])['top'] == 'amy'
    # tied totals break alphabetically
    assert m.benefit([('ab', 3), ('ba', 3)])['top'] == 'ab'  # reversal cousins
    assert m.benefit([('zz', 3), ('aa', 3)])['top'] == 'aa'
    # acts count rows, helped counts people
    assert m.benefit([('amy', 10), ('amy', 10)]) == {
        'acts': 2, 'helped': 20, 'actors': 1, 'top': 'amy'}
    # one act makes its actor the top
    assert m.benefit([('solo', 1)])['top'] == 'solo'
    # floor and cap people count
    assert m.benefit([('a', 1), ('b', 10)])['helped'] == 11
    # tuples accepted at every level
    assert m.benefit((('a', 2),))['acts'] == 1
    rng = random.Random(767)
    for _ in range(400):
        rows = [(rng.choice(['a', 'b', 'cy']), rng.randint(1, 10))
                for _ in range(rng.randint(0, 10))]
        assert m.benefit(rows) == _oracle(rows)


def _late(m):
    ACT = 'acts must be a list or tuple'
    CAP = 'acts must contain at most 100 rows'
    ROW = 'each act must be an (actor, people) row'
    ATR = 'actor must be a string of 1 to 8 characters'
    PPL = 'people must be an integer from 1 to 10'
    good = [('a', 3)]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, ACT, m.benefit, bad)
    _raises(TypeError, ACT, m.benefit, L(good * 101))           # subclass refused before the cap
    _raises(ValueError, CAP, m.benefit, good * 101)
    assert m.benefit(good * 100)['acts'] == 100
    for bad in ('a3', 5, None, ('a',), ('a', 3, 'x'), ()):
        _raises(ValueError, ROW, m.benefit, [bad])
        _raises(ValueError, ROW, m.benefit, [('a', 3), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.benefit, [K(('a', 3))])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, ATR, m.benefit, [(bad, 3)])
        _raises(ValueError, ATR, m.benefit, [('a', 3), (bad, 1)])
    for bad in (0, 11, -1, 100, '3', 3.0, None, True, False, I(3), LyingI(3)):
        _raises(ValueError, PPL, m.benefit, [('a', bad)])
        _raises(ValueError, PPL, m.benefit, [('a', 1), ('b', bad)])
    assert m.benefit([('x' * 8, 10)])['helped'] == 10
    assert m.benefit([('x', 1)])['acts'] == 1                    # single-character actor accepted
    # order: container, cap, rows (shape, actor, people)
    _raises(TypeError, ACT, m.benefit, L(good))
    _raises(ValueError, CAP, m.benefit, [('a', 99)] * 101)
    _raises(ValueError, ROW, m.benefit, [('a', 3, 'x')])
    _raises(ValueError, ATR, m.benefit, [(S('a'), 3)])
    _raises(ValueError, PPL, m.benefit, [('a', I(3))])
    # the first bad row reports first
    _raises(ValueError, ATR, m.benefit, [(5, 99), ('a', 3, 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    acts = [('a', 3), ('b', 5)]
    assert mod.benefit(acts)['top'] == 'b'
    assert acts == [('a', 3), ('b', 5)]
    assert mod.benefit(acts)['helped'] == 8


MUTANTS = [
    ("    if type(acts) not in (list, tuple):", "    if not isinstance(acts, (list, tuple)):"),
    ("    if len(acts) > MAX_ROWS:", "    if len(acts) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(actor) is not str or not 1 <= len(actor) <= MAX_ACTOR:",
     "        if not isinstance(actor, str) or not 1 <= len(actor) <= MAX_ACTOR:"),
    ("not 1 <= len(actor) <= MAX_ACTOR", "not 1 <= len(actor) < MAX_ACTOR"),
    ("MAX_ACTOR = 8", "MAX_ACTOR = 9"),
    ("        if type(people) is not int or not 1 <= people <= MAX_PEOPLE:",
     "        if type(people) is not int or not 1 <= people < MAX_PEOPLE:"),
    ("not 1 <= people <= MAX_PEOPLE", "not 0 <= people <= MAX_PEOPLE"),
    ("MAX_PEOPLE = 10", "MAX_PEOPLE = 11"),
    ("    totals = {}", "    totals = {'zz': 1}"),
    ("        totals[actor] = totals.get(actor, 0) + people", "        totals[actor] = totals.get(actor, 0) + 1"),
    ("        totals[actor] = totals.get(actor, 0) + people", "        totals[actor] = totals.get(actor, 0)"),
    ("        helped += people", "        helped += 1"),
    ("        helped += people", "        helped += people + 1"),
    ("        top = min(totals, key=lambda actor: (-totals[actor], actor))",
     "        top = min(totals, key=lambda actor: (totals[actor], actor))"),
    ("        top = min(totals, key=lambda actor: (-totals[actor], actor))",
     "        top = max(totals, key=lambda actor: (-totals[actor], actor))"),
    ("        top = min(totals, key=lambda actor: (-totals[actor], actor))",
     "        top = min(totals)"),
    ("    top = None", "    top = 'nobody'"),
    ("    return {'acts': len(rows), 'helped': helped,",
     "    return {'acts': len(rows) + 1, 'helped': helped,"),
    ("            'actors': len(totals), 'top': top}",
     "            'actors': len(rows), 'top': top}"),
    ("    for actor, people in rows:\n        totals[actor] = totals.get(actor, 0) + people",
     "    for actor, people in rows[1:]:\n        totals[actor] = totals.get(actor, 0) + people"),
    ("'acts must be a list or tuple'", "'acts must be a sequence'"),
    ("'acts must contain at most 100 rows'", "'acts must contain at most 99 rows'"),
    ("'each act must be an (actor, people) row'", "'each act must be an (actor, people) tuple'"),
    ("'actor must be a string of 1 to 8 characters'", "'actor must be a string of 1 to 7 characters'"),
    ("'people must be an integer from 1 to 10'", "'people must be an integer from 1 to 9'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

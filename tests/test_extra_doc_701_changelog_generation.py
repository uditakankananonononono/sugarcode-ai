import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import changelog_generation as mod

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
    assert mod.SCOPE == 'PARTIAL: category grouping over supplied entries, no real changelog tooling'
    assert len(mod.NOT_CLAIMED) >= 4 and 'git history' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ENTRIES, mod.MAX_TEXT, mod.ORDER) == (100, 40, ('added', 'changed', 'fixed', 'removed'))


def _oracle(entries):
    """Independent: two passes, collect then order by a name rank."""
    rank = {'added': 0, 'changed': 1, 'fixed': 2, 'removed': 3}
    grouped = {}
    for category, text in entries:
        grouped.setdefault(category, []).append(text)
    sections = [(category, grouped[category])
                for category in sorted(grouped, key=rank.get)]
    return {'sections': sections, 'total': len(entries)}


def _core(m):
    # sections follow the canonical order, not the entry order
    assert m.generate([('fixed', 'a'), ('added', 'b'), ('added', 'c')]) == {
        'sections': [('added', ['b', 'c']), ('fixed', ['a'])], 'total': 3}
    # empty sections are skipped
    assert m.generate([('removed', 'x')]) == {'sections': [('removed', ['x'])], 'total': 1}
    assert m.generate([]) == {'sections': [], 'total': 0}
    # supplied order kept inside a section
    assert m.generate([('changed', 'z'), ('changed', 'y'), ('changed', 'x')]) == {
        'sections': [('changed', ['z', 'y', 'x'])], 'total': 3}
    # all four categories interleave into canonical order
    r = m.generate([('removed', 'r1'), ('fixed', 'f1'), ('added', 'a1'), ('changed', 'c1'),
                    ('fixed', 'f2')])
    assert [s for s, _ in r['sections']] == ['added', 'changed', 'fixed', 'removed']
    assert r['sections'][2] == ('fixed', ['f1', 'f2']) and r['total'] == 5
    # tuples accepted at every level
    assert m.generate((('added', 'x'),))['total'] == 1
    rng = random.Random(701)
    for _ in range(400):
        entries = [(rng.choice(['added', 'changed', 'fixed', 'removed']),
                    't%d' % rng.randint(0, 99)) for _ in range(rng.randint(0, 15))]
        assert m.generate(entries) == _oracle(entries)


def _late(m):
    ENT = 'entries must be a list or tuple'
    CAP = 'entries must contain at most 100 rows'
    ROW = 'each entry must be a (category, text) row'
    CAT = 'category must be the string added, changed, fixed, or removed'
    TXT = 'text must be a string of 1 to 40 characters'
    good = [('added', 'x')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, ENT, m.generate, bad)
    _raises(TypeError, ENT, m.generate, L(good * 101))           # subclass refused before the cap
    _raises(ValueError, CAP, m.generate, good * 101)
    assert m.generate(good * 100)['total'] == 100
    for K in (L, T):
        for bad in (K(('added', 'x')), K(('added',))):
            _raises(ValueError, ROW, m.generate, [bad])
    for bad in ('addedx', 5, None, ('added',), ('added', 'x', 'y'), ()):
        _raises(ValueError, ROW, m.generate, [bad])
        _raises(ValueError, ROW, m.generate, [('added', 'x'), bad])
    for bad in ('', 'new', 'fix', 'Added', None, 5, b'added', S('added'), LyingS('added'), ('added',)):
        _raises(ValueError, CAT, m.generate, [(bad, 'x')])
        _raises(ValueError, CAT, m.generate, [('added', 'x'), (bad, 'y')])
    for bad in ('', 'x' * 41, None, 5, b'x', S('x'), LyingS('x'), I(1)):
        _raises(ValueError, TXT, m.generate, [('added', bad)])
        _raises(ValueError, TXT, m.generate, [('added', 'x'), ('fixed', bad)])
    assert m.generate([('added', 'x' * 40)])['total'] == 1
    # order: container, cap, rows (shape, category, text)
    _raises(TypeError, ENT, m.generate, L(good))
    _raises(ValueError, CAP, m.generate, [('bogus', 5)] * 101)
    _raises(ValueError, ROW, m.generate, [('added', 'x', 'y')])
    _raises(ValueError, CAT, m.generate, [(S('added'), 'x')])
    _raises(ValueError, TXT, m.generate, [('added', S('x'))])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    entries = [('added', 'x'), ('fixed', 'y')]
    r = mod.generate(entries)
    r['sections'][0][1].append('bogus')
    assert entries == [('added', 'x'), ('fixed', 'y')]
    assert mod.generate(entries)['sections'] == [('added', ['x']), ('fixed', ['y'])]


MUTANTS = [
    ("    if type(entries) not in (list, tuple):", "    if not isinstance(entries, (list, tuple)):"),
    ("    if len(entries) > MAX_ENTRIES:", "    if len(entries) >= MAX_ENTRIES:"),
    ("MAX_ENTRIES = 100", "MAX_ENTRIES = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(category) is not str or category not in ORDER:",
     "        if not isinstance(category, str) or category not in ORDER:"),
    ("or category not in ORDER", "or category not in ORDER[:2]"),
    ("        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:",
     "        if not isinstance(text, str) or not 1 <= len(text) <= MAX_TEXT:"),
    ("not 1 <= len(text) <= MAX_TEXT", "not 1 <= len(text) < MAX_TEXT"),
    ("not 1 <= len(text) <= MAX_TEXT", "not 0 <= len(text) <= MAX_TEXT"),
    ("MAX_TEXT = 40", "MAX_TEXT = 41"),
    ("ORDER = ('added', 'changed', 'fixed', 'removed')", "ORDER = ('added', 'fixed', 'changed', 'removed')"),
    ("ORDER = ('added', 'changed', 'fixed', 'removed')", "ORDER = ('changed', 'added', 'fixed', 'removed')"),
    ("    grouped = {category: [] for category in ORDER}", "    grouped = {}"),
    ("        grouped[category].append(text)", "        grouped[category].insert(0, text)"),
    ("        grouped[category].append(text)", "        grouped[category].append(category)"),
    ("    return {'sections': [(category, grouped[category]) for category in ORDER if grouped[category]],",
     "    return {'sections': [(category, grouped[category]) for category in ORDER],"),
    ("    return {'sections': [(category, grouped[category]) for category in ORDER if grouped[category]],",
     "    return {'sections': [(category, sorted(grouped[category])) for category in ORDER if grouped[category]],"),
    ("            'total': len(rows)}", "            'total': len(rows) + 1}"),
    ("'entries must be a list or tuple'", "'entries must be a sequence'"),
    ("'entries must contain at most 100 rows'", "'entries must contain at most 99 rows'"),
    ("'each entry must be a (category, text) row'", "'each entry must be a (category, text) tuple'"),
    ("'category must be the string added, changed, fixed, or removed'",
     "'category must be the string added, changed, or fixed'"),
    ("'text must be a string of 1 to 40 characters'", "'text must be a string of 1 to 39 characters'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

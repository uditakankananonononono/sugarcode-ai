import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import documentation_generation as mod

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
    def __hash__(self): return hash('a')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: dotted-number table of contents over supplied sections, no real doc tooling'
    assert len(mod.NOT_CLAIMED) >= 4 and 'templates' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_SECTIONS, mod.MAX_TITLE, mod.MAX_LEVEL) == (50, 40, 3)


def _oracle(rows):
    """Independent: path stack of counters, rebuilt per section."""
    path = []
    toc = []
    for title, level in rows:
        while len(path) < level:
            path.append(0)
        path[level - 1] += 1
        path = path[:level]
        toc.append(('.'.join(str(c) for c in path), title))
    return {'toc': toc, 'sections': len(rows)}


def _core(m):
    # numbering: deeper levels chain, shallow moves reset the deeper counters
    assert m.generate([('Intro', 1), ('Setup', 2), ('Usage', 2), ('Deep', 3),
                       ('Advanced', 1), ('Again', 2)]) == {
        'toc': [('1', 'Intro'), ('1.1', 'Setup'), ('1.2', 'Usage'), ('1.2.1', 'Deep'),
                ('2', 'Advanced'), ('2.1', 'Again')], 'sections': 6}
    # a level-3 chain counts independently per parent
    assert m.generate([('a', 1), ('b', 2), ('c', 3), ('d', 3), ('e', 2), ('f', 3)]) == {
        'toc': [('1', 'a'), ('1.1', 'b'), ('1.1.1', 'c'), ('1.1.2', 'd'), ('1.2', 'e'),
                ('1.2.1', 'f')], 'sections': 6}
    # flat lists number straight through
    assert m.generate([('a', 1), ('b', 1), ('c', 1)]) == {
        'toc': [('1', 'a'), ('2', 'b'), ('3', 'c')], 'sections': 3}
    assert m.generate([]) == {'toc': [], 'sections': 0}
    # returning to level 2 after a level-3 detour continues the level-2 counter
    assert m.generate([('a', 1), ('b', 2), ('c', 3), ('d', 2)])['toc'][-1] == ('1.2', 'd')
    # tuples accepted at every level
    assert m.generate((('a', 1),))['sections'] == 1
    rng = random.Random(703)
    for _ in range(400):
        rows = []
        previous = 0
        for _ in range(rng.randint(0, 12)):
            level = rng.randint(1, min(previous + 1, 3))
            rows.append(('t%d' % rng.randint(0, 99), level))
            previous = level
        assert m.generate(rows) == _oracle(rows)


def _late(m):
    SEC = 'sections must be a list or tuple'
    CAP = 'sections must contain at most 50 rows'
    ROW = 'each section must be a (title, level) row'
    TIT = 'title must be a string of 1 to 40 characters'
    LVL = 'level must be a nonbool integer between 1 and 3'
    STEP = 'levels must step one level at a time'
    good = [('a', 1)]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, SEC, m.generate, bad)
    _raises(TypeError, SEC, m.generate, L(good * 51))            # subclass refused before the cap
    _raises(ValueError, CAP, m.generate, good * 51)
    assert m.generate(good * 50)['sections'] == 50
    for K in (L, T):
        for bad in (K(('a', 1)), K(('a',))):
            _raises(ValueError, ROW, m.generate, [bad])
    for bad in ('a1', 5, None, ('a',), ('a', 1, 2), ()):
        _raises(ValueError, ROW, m.generate, [bad])
        _raises(ValueError, ROW, m.generate, [('a', 1), bad])
    for bad in ('', 'x' * 41, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, TIT, m.generate, [(bad, 1)])
        _raises(ValueError, TIT, m.generate, [('a', 1), (bad, 1)])
    assert m.generate([('x' * 40, 1)])['sections'] == 1
    for bad in (0, 4, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, LVL, m.generate, [('a', bad)])
        _raises(ValueError, LVL, m.generate, [('a', 1), ('b', bad)])
    # the step rule: first section must be level 1, depth grows one at a time
    _raises(ValueError, STEP, m.generate, [('a', 2)])
    _raises(ValueError, STEP, m.generate, [('a', 3)])
    _raises(ValueError, STEP, m.generate, [('a', 1), ('b', 3)])
    _raises(ValueError, STEP, m.generate, [('a', 1), ('b', 2), ('c', 1), ('d', 3)])
    assert m.generate([('a', 1), ('b', 2), ('c', 1), ('d', 2)])['sections'] == 4
    # order: container, cap, rows (shape, title, level, step)
    _raises(TypeError, SEC, m.generate, L(good))
    _raises(ValueError, CAP, m.generate, [('a', 1, 2)] * 51)
    _raises(ValueError, ROW, m.generate, [('a', 1, 2)])
    _raises(ValueError, TIT, m.generate, [(S('a'), 9)])
    _raises(ValueError, LVL, m.generate, [('a', I(1))])
    _raises(ValueError, LVL, m.generate, [('a', 9), ('b', 1)])
    _raises(ValueError, STEP, m.generate, [('a', 1), ('b', 3)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    sections = [('Intro', 1), ('Setup', 2)]
    r = mod.generate(sections)
    r['toc'].append(('9', 'bogus'))
    assert sections == [('Intro', 1), ('Setup', 2)]
    assert mod.generate(sections)['toc'] == [('1', 'Intro'), ('1.1', 'Setup')]


MUTANTS = [
    ("    if type(sections) not in (list, tuple):", "    if not isinstance(sections, (list, tuple)):"),
    ("    if len(sections) > MAX_SECTIONS:", "    if len(sections) >= MAX_SECTIONS:"),
    ("MAX_SECTIONS = 50", "MAX_SECTIONS = 51"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(title) is not str or not 1 <= len(title) <= MAX_TITLE:",
     "        if not isinstance(title, str) or not 1 <= len(title) <= MAX_TITLE:"),
    ("not 1 <= len(title) <= MAX_TITLE", "not 1 <= len(title) < MAX_TITLE"),
    ("MAX_TITLE = 40", "MAX_TITLE = 41"),
    ("        if type(level) is not int or not 1 <= level <= MAX_LEVEL:",
     "        if not isinstance(level, int) or not 1 <= level <= MAX_LEVEL:"),
    ("not 1 <= level <= MAX_LEVEL", "not 1 <= level < MAX_LEVEL"),
    ("not 1 <= level <= MAX_LEVEL", "not 0 <= level <= MAX_LEVEL"),
    ("MAX_LEVEL = 3", "MAX_LEVEL = 4"),
    ("        if level > previous + 1:", "        if level > previous:"),
    ("        if level > previous + 1:", "        if level > previous + 2:"),
    ("        previous = level", "        previous = level + 1"),
    ("    counters = [0, 0, 0]", "    counters = [1, 0, 0]"),
    ("        counters[level - 1] += 1", "        counters[level - 1] += 2"),
    ("        for deeper in range(level, MAX_LEVEL):", "        for deeper in range(level + 1, MAX_LEVEL):"),
    ("            counters[deeper] = 0", "            counters[deeper] = 1"),
    ("        toc.append(('.'.join(str(counters[i]) for i in range(level)), title))",
     "        toc.append(('.'.join(str(counters[i]) for i in range(level - 1)), title))"),
    ("        toc.append(('.'.join(str(counters[i]) for i in range(level)), title))",
     "        toc.append(('-'.join(str(counters[i]) for i in range(level)), title))"),
    ("    return {'toc': toc, 'sections': len(rows)}", "    return {'toc': toc, 'sections': len(rows) + 1}"),
    ("    for title, level in rows:", "    for title, level in reversed(rows):"),
    ("'sections must be a list or tuple'", "'sections must be a sequence'"),
    ("'sections must contain at most 50 rows'", "'sections must contain at most 49 rows'"),
    ("'each section must be a (title, level) row'", "'each section must be a (title, level) tuple'"),
    ("'title must be a string of 1 to 40 characters'", "'title must be a string of 1 to 39 characters'"),
    ("'level must be a nonbool integer between 1 and 3'",
     "'level must be an integer between 1 and 3'"),
    ("'levels must step one level at a time'", "'levels must step one at a time'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

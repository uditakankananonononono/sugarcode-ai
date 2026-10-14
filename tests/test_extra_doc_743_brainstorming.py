import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import brainstorming as mod

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
    assert mod.SCOPE == 'PARTIAL: idea dedup over supplied rows, no real brainstorming'
    assert len(mod.NOT_CLAIMED) >= 4 and 'clustering' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_IDEAS, mod.MAX_AUTHOR, mod.MAX_TEXT) == (100, 8, 40)


def _oracle(rows):
    """Independent: seen-list membership, author counts in a dict."""
    seen = []
    unique = []
    duplicates = 0
    authors = {}
    for author, text in rows:
        if text in seen:
            duplicates += 1
        else:
            seen.append(text)
            unique.append(text)
        authors[author] = authors.get(author, 0) + 1
    return {'ideas': unique, 'duplicates': duplicates,
            'authors': sorted(authors.items()), 'total': len(rows)}


def _core(m):
    assert m.collect([('a', 'x'), ('b', 'y'), ('a', 'x'), ('a', 'z')]) == {
        'ideas': ['x', 'y', 'z'], 'duplicates': 1, 'authors': [('a', 3), ('b', 1)], 'total': 4}
    assert m.collect([]) == {'ideas': [], 'duplicates': 0, 'authors': [], 'total': 0}
    # first-seen order, not sorted
    assert m.collect([('a', 'zz'), ('a', 'mm'), ('a', 'aa')])['ideas'] == ['zz', 'mm', 'aa']
    # the same text from another author is still a duplicate
    assert m.collect([('a', 'x'), ('b', 'x')])['duplicates'] == 1
    # a third repeat counts again
    assert m.collect([('a', 'x'), ('a', 'x'), ('a', 'x')])['duplicates'] == 2
    # duplicate rows still count toward their author
    assert m.collect([('a', 'x'), ('a', 'x')])['authors'] == [('a', 2)]
    # authors sort alphabetically
    assert m.collect([('zz', 'x'), ('aa', 'y')])['authors'] == [('aa', 1), ('zz', 1)]
    # tuples accepted at every level
    assert m.collect((('a', 'x'),))['total'] == 1
    rng = random.Random(743)
    for _ in range(400):
        rows = [(rng.choice(['a', 'b', 'c']), 't%d' % rng.randint(0, 5))
                for _ in range(rng.randint(0, 12))]
        assert m.collect(rows) == _oracle(rows)


def _late(m):
    IDS = 'ideas must be a list or tuple'
    CAP = 'ideas must contain at most 100 rows'
    ROW = 'each idea must be an (author, text) row'
    AUT = 'author must be a string of 1 to 8 characters'
    TXT = 'text must be a string of 1 to 40 characters'
    good = [('a', 'x')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, IDS, m.collect, bad)
    _raises(TypeError, IDS, m.collect, L(good * 101))           # subclass refused before the cap
    _raises(ValueError, CAP, m.collect, good * 101)
    assert m.collect(good * 100)['total'] == 100
    for K in (L, T):
        for bad in (K(('a', 'x')), K(('a',))):
            _raises(ValueError, ROW, m.collect, [bad])
    for bad in ('ax', 5, None, ('a',), ('a', 'x', 'y'), ()):
        _raises(ValueError, ROW, m.collect, [bad])
        _raises(ValueError, ROW, m.collect, [('a', 'x'), bad])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, AUT, m.collect, [(bad, 'x')])
        _raises(ValueError, AUT, m.collect, [('a', 'x'), (bad, 'y')])
    for bad in ('', 'x' * 41, None, 5, b'x', S('x'), LyingS('x'), I(1)):
        _raises(ValueError, TXT, m.collect, [('a', bad)])
        _raises(ValueError, TXT, m.collect, [('a', 'x'), ('b', bad)])
    assert m.collect([('x' * 8, 'x' * 40)])['total'] == 1
    # order: container, cap, rows (shape, author, text)
    _raises(TypeError, IDS, m.collect, L(good))
    _raises(ValueError, CAP, m.collect, [('a', 1, 2)] * 101)
    _raises(ValueError, ROW, m.collect, [('a', 'x', 'y')])
    _raises(ValueError, AUT, m.collect, [(S('a'), 'x')])
    _raises(ValueError, TXT, m.collect, [('a', S('x'))])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    ideas = [('a', 'x'), ('b', 'x')]
    r = mod.collect(ideas)
    r['ideas'].append('bogus')
    assert ideas == [('a', 'x'), ('b', 'x')]
    assert mod.collect(ideas)['ideas'] == ['x']


MUTANTS = [
    ("    if type(ideas) not in (list, tuple):", "    if not isinstance(ideas, (list, tuple)):"),
    ("    if len(ideas) > MAX_IDEAS:", "    if len(ideas) >= MAX_IDEAS:"),
    ("MAX_IDEAS = 100", "MAX_IDEAS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(author) is not str or not 1 <= len(author) <= MAX_AUTHOR:",
     "        if not isinstance(author, str) or not 1 <= len(author) <= MAX_AUTHOR:"),
    ("not 1 <= len(author) <= MAX_AUTHOR", "not 1 <= len(author) < MAX_AUTHOR"),
    ("MAX_AUTHOR = 8", "MAX_AUTHOR = 9"),
    ("        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:",
     "        if not isinstance(text, str) or not 1 <= len(text) <= MAX_TEXT:"),
    ("not 1 <= len(text) <= MAX_TEXT", "not 1 <= len(text) < MAX_TEXT"),
    ("MAX_TEXT = 40", "MAX_TEXT = 41"),
    ("        if text in seen:", "        if text not in seen:"),
    ("            duplicates += 1", "            duplicates += 2"),
    ("            seen.add(text)", "            seen.add(author)"),
    ("            unique.append(text)", "            unique.append(author)"),
    ("            unique.append(text)", "            unique.insert(0, text)"),
    ("        authors[author] = authors.get(author, 0) + 1", "        authors[author] = authors.get(author, 0) + 2"),
    ("    seen = set()", "    seen = set(['x'])"),
    ("    return {'ideas': unique, 'duplicates': duplicates,",
     "    return {'ideas': sorted(unique), 'duplicates': duplicates,"),
    ("    return {'ideas': unique, 'duplicates': duplicates,",
     "    return {'ideas': unique, 'duplicates': duplicates + 1,"),
    ("            'authors': sorted(authors.items()), 'total': len(rows)}",
     "            'authors': sorted(authors.items(), reverse=True), 'total': len(rows)}"),
    ("            'authors': sorted(authors.items()), 'total': len(rows)}",
     "            'authors': sorted(authors.items()), 'total': len(unique)}"),
    ("    for author, text in rows:", "    for author, text in reversed(rows):"),
    ("        rows.append((author, text))", "        rows.append((text, author))"),
    ("'ideas must be a list or tuple'", "'ideas must be a sequence'"),
    ("'ideas must contain at most 100 rows'", "'ideas must contain at most 99 rows'"),
    ("'each idea must be an (author, text) row'", "'each idea must be an (author, text) tuple'"),
    ("'author must be a string of 1 to 8 characters'", "'author must be a string of 1 to 7 characters'"),
    ("'text must be a string of 1 to 40 characters'", "'text must be a string of 1 to 39 characters'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

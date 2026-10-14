import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import idea_novelty as mod

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
    assert mod.SCOPE == 'PARTIAL: compares supplied idea words with supplied known ideas, no creativity is judged'
    assert len(mod.NOT_CLAIMED) == 5 and 'usefulness of ideas' in mod.NOT_CLAIMED and 'learner creativity' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Creative Thinking - Generates novel ideas' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(kn, ids):
    """Independent: sorted word tuples as set identity, vocabulary as a plain list, ranking by a scoring tuple."""
    vocab = []
    sigs = []
    for k in kn:
        ws = k.split(' ')
        vocab += ws
        sigs.append(tuple(sorted(set(ws))))
    out = []
    cnt = {'new': 0, 'remix': 0, 'duplicate': 0}
    for i in ids:
        ws = sorted(set(i.split(' ')))
        new = len([w for w in ws if w not in vocab])
        kind = 'new' if new > 0 else ('duplicate' if tuple(ws) in sigs else 'remix')
        cnt[kind] += 1
        out.append((i, new, kind))
    order = {'new': 0, 'remix': 1, 'duplicate': 2}
    out.sort(key=lambda r: (-r[1], order[r[2]], r[0]))
    return {'ranked': out, 'counts': cnt}


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
    def __hash__(self): return hash('a')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def _core(m):
    f = m.idea_novelty
    assert f(['red cat'], ['blue dog']) == {'ranked': [('blue dog', 2, 'new')], 'counts': {'new': 1, 'remix': 0, 'duplicate': 0}}
    assert f(['red cat'], ['red cat']) == {'ranked': [('red cat', 0, 'duplicate')], 'counts': {'new': 0, 'remix': 0, 'duplicate': 1}}
    # order and repeats do not matter for duplicates
    assert f(['red cat'], ['cat red'])['ranked'] == [('cat red', 0, 'duplicate')]
    assert f(['red cat'], ['cat red cat'])['ranked'] == [('cat red cat', 0, 'duplicate')]
    assert f(['red cat'], ['red red'])['ranked'] == [('red red', 0, 'remix')]
    assert f(['red cat', 'big dog'], ['red dog'])['ranked'] == [('red dog', 0, 'remix')]
    assert f(['red cat', 'big dog'], ['red dog big'])['ranked'] == [('red dog big', 0, 'remix')]
    # new words are counted once each, even when repeated
    assert f(['a'], ['b b'])['ranked'] == [('b b', 1, 'new')]
    assert f(['a'], ['b c a'])['ranked'] == [('b c a', 2, 'new')]
    assert f(['a b'], ['a'])['ranked'] == [('a', 0, 'remix')]
    r = f(['red cat', 'big dog'], ['big dog', 'red dog', 'zebra', 'red zebra', 'cat red', 'moon sun star'])
    assert r['ranked'] == [('moon sun star', 3, 'new'), ('red zebra', 1, 'new'), ('zebra', 1, 'new'), ('red dog', 0, 'remix'), ('big dog', 0, 'duplicate'), ('cat red', 0, 'duplicate')]
    assert r['counts'] == {'new': 3, 'remix': 1, 'duplicate': 2}
    # ties on new words and kind are ordered by text; input order does not matter
    assert [x[0] for x in f(['a'], ['c', 'b', 'd'])['ranked']] == ['b', 'c', 'd']
    assert f(['a b c'], ['a c b', 'b a', 'c a'])['ranked'] == [('b a', 0, 'remix'), ('c a', 0, 'remix'), ('a c b', 0, 'duplicate')]
    assert f(('a',), ('b',))['counts']['new'] == 1 and f(['a'], ('a',))['counts']['duplicate'] == 1
    assert f(['abcdefgh'], ['abcdefgh x'])['ranked'] == [('abcdefgh x', 1, 'new')]
    assert f(['a'], ['q'] + ['r', 's', 't', 'u', 'v'])['counts']['new'] == 6
    assert f(list('abcdef'), ['f'])['ranked'] == [('f', 0, 'duplicate')]
    rng = random.Random(864)
    words = ['a', 'b', 'c', 'd', 'e', 'f']
    def mk():
        return ' '.join(rng.choice(words) for _ in range(rng.randint(1, 3)))
    for _ in range(1500):
        kn = [mk() for _ in range(rng.randint(1, 6))]
        ids = []
        for _ in range(rng.randint(1, 6)):
            c = mk()
            if c not in ids:
                ids.append(c)
        kn = rng.choice((list, tuple))(kn)
        ids = rng.choice((list, tuple))(ids)
        assert f(kn, ids) == _oracle(kn, ids), (kn, ids)


def _late(m):
    f = m.idea_novelty
    KT = 'known must be a list or tuple'
    KS = 'known must contain 1 to 6 entries'
    KE = 'each known idea must be 1 to 3 lowercase words of 1 to 8 ASCII letters'
    IT = 'ideas must be a list or tuple'
    IS = 'ideas must contain 1 to 6 entries'
    IE = 'each idea must be 1 to 3 lowercase words of 1 to 8 ASCII letters'
    ID = 'ideas must be distinct'
    bads = ('', ' ', 'a ', ' a', 'a  b', 'a b c d', 'abcdefghi', 'A', 'aB', 'a1', 'a-b', None, 5, True, S('a'), LyingS('a'), b'a', ['a'],
            '\u00e9', 'caf\u00e9', 'a \u00e9', '\u4e2d', '\u0661', 'a\nb', '\n', 'a\n', '\ta', 'a\x00', '\x7f', 'a\r', 'a\x0b', 'a_b')
    for bad in ('ab', None, 5, {}, L(['a']), T(['a']), L(), T()):
        _raises(TypeError, KT, f, bad, ['a'])
    _raises(ValueError, KS, f, [], ['a'])
    _raises(ValueError, KS, f, list('abcdefg'), ['a'])
    f(list('abcdef'), ['a'])
    for bad in bads:
        _raises(ValueError, KE, f, [bad], ['a'])
        _raises(ValueError, KE, f, ['a', bad], ['a'])
    f(['abcdefgh x y'], ['a'])
    for bad in ('ab', None, 5, {}, L(['a']), T(['a']), L(), T()):
        _raises(TypeError, IT, f, ['a'], bad)
    _raises(ValueError, IS, f, ['a'], [])
    _raises(ValueError, IS, f, ['a'], list('abcdefg'))
    f(['a'], list('abcdef'))
    for bad in bads:
        _raises(ValueError, IE, f, ['a'], [bad])
        _raises(ValueError, IE, f, ['a'], ['b', bad])
    _raises(ValueError, ID, f, ['a'], ['b', 'b'])
    f(['a'], ['b c', 'c b'])
    _raises(TypeError, KT, f, None, None)
    _raises(ValueError, KS, f, [], None)
    _raises(ValueError, KE, f, [1, 1], None)
    _raises(TypeError, IT, f, ['a'], None)
    _raises(ValueError, IS, f, ['a'], [])
    _raises(ValueError, IE, f, ['a'], [1, 1])
    _raises(ValueError, ID, f, ['a'], ['b', 'b'])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


W = "w.isascii() and w.isalpha() and w.islower() and 1 <= len(w) <= 8"
MUTANTS = [
    ("if type(x) is not str:", "if not isinstance(x, str):"),
    ("x.split(' ')", "x.split()"),
    ("if not 1 <= len(words) <= 3:", "if not 1 <= len(words) < 3:"),
    ("if not 1 <= len(words) <= 3:", "if not 1 <= len(words) <= 4:"),
    (W, "w.isalpha() and w.islower() and 1 <= len(w) <= 8"),
    (W, "w.isascii() and w.islower() and 1 <= len(w) <= 8"),
    (W, "w.isascii() and w.isalpha() and 1 <= len(w) <= 8"),
    (W, "w.isascii() and w.isalpha() and w.islower() and 1 <= len(w) < 8"),
    (W, "w.isascii() and w.isalpha() and w.islower() and 1 <= len(w) <= 9"),
    ("return all(", "return any("),
    ("type(known) not in (list, tuple)", "not isinstance(known, (list, tuple))"),
    ("not 1 <= len(known) <= 6", "not 0 <= len(known) <= 6"),
    ("not 1 <= len(known) <= 6", "not 1 <= len(known) < 6"),
    ("not 1 <= len(known) <= 6", "not 1 <= len(known) <= 7"),
    ("type(ideas) not in (list, tuple)", "not isinstance(ideas, (list, tuple))"),
    ("not 1 <= len(ideas) <= 6", "not 0 <= len(ideas) <= 6"),
    ("not 1 <= len(ideas) <= 6", "not 1 <= len(ideas) < 6"),
    ("not 1 <= len(ideas) <= 6", "not 1 <= len(ideas) <= 7"),
    ("if len(set(ideas)) != len(ideas):", "if False:"),
    ("vocab = {w for k in known for w in k.split(' ')}", "vocab = {w for w in known[0].split(' ')}"),
    ("vocab = {w for k in known for w in k.split(' ')}", "vocab = {k for k in known}"),
    ("sets = [frozenset(k.split(' ')) for k in known]", "sets = [tuple(k.split(' ')) for k in known]"),
    ("sets = [frozenset(k.split(' ')) for k in known]", "sets = [frozenset(k.split(' ')) for k in known[:1]]"),
    ("words = frozenset(i.split(' '))", "words = tuple(i.split(' '))"),
    ("fresh = len(words - vocab)", "fresh = len([w for w in i.split(' ') if w not in vocab])"),
    ("fresh = len(words - vocab)", "fresh = min(1, len(words - vocab))"),
    ("elif words in sets:", "elif words in sets and False:"),
    ("elif words in sets:", "elif words <= vocab and len(words) == 1:"),
    ("KIND_ORDER = {'new': 0, 'remix': 1, 'duplicate': 2}", "KIND_ORDER = {'new': 0, 'remix': 2, 'duplicate': 1}"),
    ("rows.append((-fresh, KIND_ORDER[kind], i, kind))", "rows.append((fresh, KIND_ORDER[kind], i, kind))"),
    ("rows.append((-fresh, KIND_ORDER[kind], i, kind))", "rows.append((-fresh, 0, i, kind))"),
    ("rows.sort()", "rows.sort(reverse=True)"),
    ("counts[kind] += 1", "counts[kind] = 1"),
    ("[(i, -f, kind) for f, _, i, kind in rows]", "[(i, f, kind) for f, _, i, kind in rows]"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

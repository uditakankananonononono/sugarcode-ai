import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import named_entity_gazetteer as mod

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



class D(dict):
    pass


G = {'Ada': 'person', 'Ada Lovelace': 'person', 'Paris': 'place', 'Py3': 'tool'}


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: longest-match gazetteer lookup over supplied text, no learned recognition'
    assert len(mod.NOT_CLAIMED) >= 4 and 'accuracy' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_NAMES, mod.MAX_NAME, mod.MAX_TYPE, mod.MAX_TEXT) == (50, 40, 20, 2000)


def _oracle(gaz, text):
    """Independent: regex with boundary lookarounds, alternation ordered longest first."""
    import re
    if not gaz:
        return []
    alt = '|'.join(re.escape(n) for n in sorted(gaz, key=lambda n: (-len(n), n)))
    pat = re.compile(r'(?<![A-Za-z0-9])(?:' + alt + r')(?![A-Za-z0-9])')
    return [(m.start(), m.end(), m.group(), gaz[m.group()]) for m in pat.finditer(text)]


def _core(m):
    assert m.tag({}, 'anything') == [] and m.tag(G, '') == []
    assert m.tag(G, 'Ada met Paris') == [(0, 3, 'Ada', 'person'), (8, 13, 'Paris', 'place')]
    # longest match wins over a shorter prefix name
    assert m.tag(G, 'Ada Lovelace') == [(0, 12, 'Ada Lovelace', 'person')]
    assert m.tag(G, 'Ada Lovelaces') == [(0, 3, 'Ada', 'person')]
    # word boundaries: no hit inside a longer word, digits count as word characters
    assert m.tag(G, 'Parisian') == [] and m.tag(G, 'xParis') == [] and m.tag(G, 'Paris2') == []
    assert m.tag(G, '1Paris') == [] and m.tag(G, '_Paris_') == [(1, 6, 'Paris', 'place')]
    assert m.tag(G, '(Paris),Paris.') == [(1, 6, 'Paris', 'place'), (8, 13, 'Paris', 'place')]
    # case-sensitive
    assert m.tag(G, 'paris PARIS') == []
    # digits in names, edge positions, adjacent entities, no overlap
    assert m.tag(G, 'Py3') == [(0, 3, 'Py3', 'tool')]
    assert m.tag(G, 'Paris Paris') == [(0, 5, 'Paris', 'place'), (6, 11, 'Paris', 'place')]
    assert m.tag({'a b': 'x', 'b c': 'y'}, 'a b c') == [(0, 3, 'a b', 'x')]
    assert m.tag({'aa': 'x'}, 'aaaa') == []
    # a name at the very end of the text, and one after a boundary at the start
    assert m.tag({'End': 'k'}, 'the End') == [(4, 7, 'End', 'k')]
    # equal length tie is impossible for different names at one position, but a failed long name falls back
    assert m.tag({'New York': 'place', 'New': 'word'}, 'New Yorkers') == [(0, 3, 'New', 'word')]
    assert m.tag({'a': 'k'}, 'Za') == [] and m.tag({'a': 'k'}, 'aZ') == []
    assert m.tag({'a': 'z'}, 'a') == [(0, 1, 'a', 'z')] and m.tag({'Z': 'k'}, 'Z') == [(0, 1, 'Z', 'k')]
    # unicode letters are not word characters
    assert m.tag(G, '\u00e9Paris') == [(1, 6, 'Paris', 'place')]
    rng = random.Random(562)
    words = ['a', 'ab', 'a b', 'b', 'abc', 'B1', 'x y z']
    for _ in range(400):
        gaz = {w: rng.choice(['p', 'q']) for w in rng.sample(words, rng.randint(0, 5))}
        text = ''.join(rng.choice(['a', 'b', ' ', 'c', '1', 'B', 'x', 'y', 'z', '.']) for _ in range(rng.randint(0, 25)))
        assert m.tag(gaz, text) == _oracle(gaz, text)


def _late(m):
    GAZ = 'gazetteer must be a dict'
    CAP = 'gazetteer must contain at most 50 names'
    NAME = 'names must be 1 to 40 characters of letters, digits, single spaces'
    TYPE = 'types must be 1 to 20 lowercase letters'
    TXT = 'text must be a str'
    LEN = 'text must be at most 2000 characters'
    for bad in (None, [], (), 'x', 5, D(G)):
        _raises(TypeError, GAZ, m.tag, bad, '')
    _raises(TypeError, GAZ, m.tag, D({'a' * 51: 'k'}), 5)
    big = {'n%d' % i: 'k' for i in range(51)}
    _raises(ValueError, CAP, m.tag, big, '')
    assert m.tag({'n%d' % i: 'k' for i in range(50)}, 'n49') == [(0, 3, 'n49', 'k')]
    for bad in ('', ' a', 'a ', 'a  b', 'a-b', 'a_b', 'a\tb', 'a\nb', 'x' * 41, '\u00e9', None, 5, S('a'), ('a',)):
        _raises(ValueError, NAME, m.tag, {bad: 'k'}, '')
    assert m.tag({'x' * 40: 'k'}, 'x' * 40) == [(0, 40, 'x' * 40, 'k')]
    for bad in ('', 'Ab', 'a1', 'a b', 'a_b', 'k' * 21, None, 5, S('k'), b'k', ['k']):
        _raises(ValueError, TYPE, m.tag, {'a': bad}, '')
    assert m.tag({'a': 'k' * 20}, 'a') == [(0, 1, 'a', 'k' * 20)]
    for bad in (None, 5, b'x', ['x'], S('x')):
        _raises(TypeError, TXT, m.tag, G, bad)
    _raises(ValueError, LEN, m.tag, G, 'x' * 2001)
    assert m.tag(G, 'x' * 2000) == []
    assert m.tag({'x': 'k'}, 'x ' * 1000)[-1] == (1998, 1999, 'x', 'k')
    # order: gazetteer type, cap, names/types in iteration order, text type, text length
    _raises(ValueError, CAP, m.tag, dict(big, **{'bad name!': 'k'}), 5)
    _raises(ValueError, NAME, m.tag, {'bad-name': 'BAD'}, 5)
    _raises(ValueError, TYPE, m.tag, {'ok': 'BAD', 'bad-name': 'k'}, 5)
    _raises(TypeError, TXT, m.tag, G, 5)
    _raises(ValueError, NAME, m.tag, {'bad-name': 'k'}, 'x' * 2001)


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_inputs_unchanged_and_result_fresh():
    g = dict(G)
    r = mod.tag(g, 'Ada')
    r.append(1)
    assert g == G and mod.tag(g, 'Ada') == [(0, 3, 'Ada', 'person')]


MUTANTS = [
    ("    if type(gazetteer) is not dict:", "    if not isinstance(gazetteer, dict):"),
    ("    if len(gazetteer) > MAX_NAMES:", "    if len(gazetteer) >= MAX_NAMES:"),
    ("MAX_NAMES = 50", "MAX_NAMES = 51"),
    ("        if (type(name) is not str or", "        if (not isinstance(name, str) or"),
    ("not 1 <= len(name) <= MAX_NAME", "not 0 <= len(name) <= MAX_NAME"),
    ("not 1 <= len(name) <= MAX_NAME", "not 1 <= len(name) < MAX_NAME"),
    ("MAX_NAME = 40", "MAX_NAME = 41"),
    ("any(ch not in _ALNUM + ' ' for ch in name)", "any(ch not in _ALNUM for ch in name)"),
    ("name[0] == ' ' or", "False or"),
    ("or name[-1] == ' '", "or False"),
    ("or '  ' in name", "or False"),
    ("        if type(kind) is not str or", "        if not isinstance(kind, str) or"),
    ("not 1 <= len(kind) <= MAX_TYPE", "not 0 <= len(kind) <= MAX_TYPE"),
    ("not 1 <= len(kind) <= MAX_TYPE", "not 1 <= len(kind) < MAX_TYPE"),
    ("MAX_TYPE = 20", "MAX_TYPE = 21"),
    ("any(ch not in _LOWER for ch in kind)", "any(ch not in _LOWER + _ALNUM for ch in kind)"),
    ("    if type(text) is not str:", "    if not isinstance(text, str):"),
    ("    if len(text) > MAX_TEXT:", "    if len(text) >= MAX_TEXT:"),
    ("MAX_TEXT = 2000", "MAX_TEXT = 2001"),
    ("_ALNUM = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'", "_ALNUM = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'"),
    ("_ALNUM = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'", "_ALNUM = 'abcdefghijklmnopqrstuvwxyz0123456789'"),
    ("_ALNUM = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'", "_ALNUM = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'"),
    ("_ALNUM = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'", "_ALNUM = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY0123456789'"),
    ("_LOWER = 'abcdefghijklmnopqrstuvwxyz'", "_LOWER = 'abcdefghijklmnopqrstuvwxy'"),
    ("_LOWER = 'abcdefghijklmnopqrstuvwxyz'", "_LOWER = 'bcdefghijklmnopqrstuvwxyz'"),
    ("key=lambda n: (-len(n), n)", "key=lambda n: (len(n), n)"),
    ("key=lambda n: (-len(n), n)", "key=lambda n: n"),
    ("    while i < len(text):", "    while i < len(text) - 1:"),
    ("        if i == 0 or text[i - 1] not in _ALNUM:", "        if True:"),
    ("        if i == 0 or text[i - 1] not in _ALNUM:", "        if i == 0 or text[i - 1] != ' ':"),
    ("        if i == 0 or text[i - 1] not in _ALNUM:", "        if i != 0 and text[i - 1] not in _ALNUM:"),
    ("(j == len(text) or text[j] not in _ALNUM)", "True"),
    ("(j == len(text) or text[j] not in _ALNUM)", "(j == len(text) or text[j] == ' ')"),
    ("(j == len(text) or text[j] not in _ALNUM)", "(j < len(text) and text[j] not in _ALNUM)"),
    ("text.startswith(name, i) and", "text.lower().startswith(name.lower(), i) and"),
    ("            found.append((i, i + len(hit), hit, gazetteer[hit]))", "            found.append((i, i + len(hit) - 1, hit, gazetteer[hit]))"),
    ("            found.append((i, i + len(hit), hit, gazetteer[hit]))", "            found.append((i + 1, i + len(hit), hit, gazetteer[hit]))"),
    ("            found.append((i, i + len(hit), hit, gazetteer[hit]))", "            found.append((i, i + len(hit), hit, 'x'))"),
    ("            i += len(hit)", "            i += 1"),
    ("                    hit = name\n                    break", "                    hit = name"),
    ("'gazetteer must be a dict'", "'gazetteer must be a mapping'"),
    ("'gazetteer must contain at most 50 names'", "'gazetteer must contain at most 49 names'"),
    ("'names must be 1 to 40 characters of letters, digits, single spaces'", "'names must be words'"),
    ("'types must be 1 to 20 lowercase letters'", "'types must be words'"),
    ("'text must be a str'", "'text must be text'"),
    ("'text must be at most 2000 characters'", "'text must be at most 1999 characters'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_not_claimed_pinned_exactly():
    assert mod.NOT_CLAIMED == ('statistical or neural recognition', 'disambiguation', 'aliases', 'coreference', 'multilingual text', 'accuracy', 'production readiness')


def test_type_charset_is_lowercase_ascii_only():
    msg = 'types must be 1 to 20 lowercase letters'
    for bad in ('x-y', 'x_y', 'x y', 'x1', '1', 'X', 'xY', 'Xy', '-', ' ', 'x.', 'x\n', '\u00e9', 'x\u00e9',
                '\u0130', '\u212a', 'x\u00df', '\u4e2d', '\u0661', 'x/', 'x@', 'x[', 'x`', 'x{'):
        _raises(ValueError, msg, mod.tag, {'a': bad}, '')
    for ok in ('a', 'z', 'abcxyz', 'abcdefghijklmnopqrstuvwxyz'[:20]):
        assert mod.tag({'a': ok}, 'a') == [(0, 1, 'a', ok)]
    assert mod.tag({'a': 'abcdefghijklmnopqrstuvwxyz'[:20]}, '') == []

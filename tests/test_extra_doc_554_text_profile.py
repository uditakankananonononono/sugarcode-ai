import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import text_profile as mod

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



EMPTY = {'words': 0, 'distinct': 0, 'sentences': 0, 'longest': None, 'top': []}


def test_scope_and_constants():
    assert mod.SCOPE == 'PARTIAL: word and sentence counting over supplied text, no language understanding'
    assert mod.NOT_CLAIMED == ('part-of-speech tagging', 'parsing', 'meaning', 'sentiment',
                               'abbreviation handling', 'multilingual text', 'accuracy',
                               'production readiness')
    assert 'NOT_CLAIMED' in mod.__doc__ and not (ROOT / '__init__.py').exists()
    assert (mod.MAX_TEXT, mod.TOP_N) == (2000, 3)


def _oracle(text):
    """Independent: regex tokens, re.split sentences, Counter-free ranking."""
    import re
    words = re.findall(r'[a-z0-9]+', re.sub(r'[A-Z]', lambda m: m.group().lower(), text))
    pieces = re.split(r'[.!?]', text)
    sentences = sum(1 for p in pieces if re.search(r'[A-Za-z0-9]', p))
    distinct = sorted(set(words))
    ranked = sorted(distinct, key=lambda w: (-words.count(w), w))[:3]
    longest = None
    for w in words:
        if longest is None or len(w) > len(longest):
            longest = w
    return {'words': len(words), 'distinct': len(distinct), 'sentences': sentences,
            'longest': longest, 'top': [(w, words.count(w)) for w in ranked]}


def test_empty_and_separator_only():
    assert mod.profile('') == EMPTY
    assert mod.profile(' ,;-_\n') == EMPTY
    assert mod.profile('...!?') == EMPTY


def test_counts_and_sentences():
    r = mod.profile('The cat sat. The cat ran! Did it?')
    assert r == {'words': 8, 'distinct': 6, 'sentences': 3, 'longest': 'the',
                 'top': [('cat', 2), ('the', 2), ('did', 1)]}
    assert mod.profile('one')['sentences'] == 1                    # trailing piece without a terminator
    assert mod.profile('one. two')['sentences'] == 2
    assert mod.profile('one. two.')['sentences'] == 2              # nothing after the last stop
    assert mod.profile('one.. two')['sentences'] == 2              # empty piece between stops is not counted
    assert mod.profile('...one')['sentences'] == 1
    assert mod.profile('3.5')['sentences'] == 2 and mod.profile('3.5')['words'] == 2
    assert mod.profile('a! b? c.')['sentences'] == 3
    assert mod.profile('a, b; c')['sentences'] == 1                # commas and semicolons do not split
    assert mod.profile('a . . b')['sentences'] == 2
    assert mod.profile('end?')['sentences'] == 1 and mod.profile('end!')['sentences'] == 1


def test_longest_and_top_rules():
    assert mod.profile('aa bb c')['longest'] == 'aa'               # first on a length tie
    assert mod.profile('c bb aa')['longest'] == 'bb'
    assert mod.profile('a bbb cc')['longest'] == 'bbb'
    assert mod.profile('x')['longest'] == 'x'
    r = mod.profile('d c b a a b b')
    assert r['top'] == [('b', 3), ('a', 2), ('c', 1)]              # count desc then alphabetical, capped at 3
    assert mod.profile('b a')['top'] == [('a', 1), ('b', 1)]
    assert mod.profile('a b c d')['top'] == [('a', 1), ('b', 1), ('c', 1)]
    assert mod.profile('A a A')['top'] == [('a', 3)]
    assert mod.profile('z1 z1 z2')['top'] == [('z1', 2), ('z2', 1)]
    assert mod.profile('b b a')['distinct'] == 2 and mod.profile('b b a')['words'] == 3


def test_tokenizing_rules():
    assert mod.profile('CAR') == mod.profile('car') and mod.profile('CAR')['longest'] == 'car'
    assert mod.profile('v2 V2')['top'] == [('v2', 2)]
    assert mod.profile('a_b')['words'] == 2 and mod.profile('ab')['words'] == 1
    assert mod.profile("don't")['words'] == 2
    assert mod.profile('caf\u00e9')['top'] == [('caf', 1)] and mod.profile('\u00e9a')['top'] == [('a', 1)]
    assert mod.profile('az09 AZ09')['top'] == [('az09', 2)]
    assert mod.profile('zz ZZ aa AA')['top'] == [('aa', 2), ('zz', 2)]
    assert mod.profile('0 9 9')['top'] == [('9', 2), ('0', 1)]
    for ch in ('\u00c9', '\u0130', '\u212a'):
        assert mod.profile(ch) == EMPTY
        assert mod.profile('a%sb' % ch)['words'] == 2
    assert mod.profile('\u212a')['top'] == [] and mod.profile('k \u212a')['top'] == [('k', 1)]
    assert mod.profile('x end')['words'] == 2                      # last word without trailing separator
    # stop characters in non-ASCII lookalikes do not split
    assert mod.profile('a\u3002b')['sentences'] == 1


def test_randomized_against_oracle():
    rng = random.Random(554)
    vocab = ['a', 'B', 'cc', 'D1', '9', ' ', '.', '!', '?', ',', '-', '\n', '\u00e9']
    for _ in range(500):
        text = ''.join(rng.choice(vocab) for _ in range(rng.randint(0, 30)))
        assert mod.profile(text) == _oracle(text)


def test_validation_and_length_boundary():
    for bad in (None, 5, b'x', ['x'], 1.5):
        _raises(TypeError, 'text must be a str', mod.profile, bad)
    _raises(TypeError, 'text must be a str', mod.profile, S('x'))
    _raises(ValueError, 'text must be at most 2000 characters', mod.profile, 'x' * 2001)
    r = mod.profile('x' * 2000)
    assert r['words'] == 1 and r['longest'] == 'x' * 2000
    r = mod.profile('a ' * 1000)
    assert r['words'] == 1000 and r['top'] == [('a', 1000)]
    assert mod.profile('a.' * 1000)['sentences'] == 1000


def test_result_is_fresh():
    r = mod.profile('a b')
    r['top'].append(1)
    assert mod.profile('a b')['top'] == [('a', 1), ('b', 1)]

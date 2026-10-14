import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import metaphor_domains as mod

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
    assert mod.SCOPE == 'PARTIAL: source-domain tally of supplied metaphor labels, no text is read'
    assert len(mod.NOT_CLAIMED) == 5 and 'real metaphor quality' in mod.NOT_CLAIMED and 'meaning' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


DOMS = ['war', 'journey', 'building', 'nature', 'machine']


def _oracle(us, md):
    cnt = [(d, [dd for _, dd in us].count(d)) for d in DOMS]
    dist = len([1 for _, c in cnt if c])
    best = None
    if us:
        mx = max(c for _, c in cnt)
        best = [d for d, c in cnt if c == mx][0]
    return {'counts': cnt, 'distinct': dist, 'dominant': best, 'mixed': dist > md}


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
    def __hash__(self): return hash('war')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def _core(m):
    f = m.metaphor_domains
    Z = [('war', 0), ('journey', 0), ('building', 0), ('nature', 0), ('machine', 0)]
    assert f([]) == {'counts': Z, 'distinct': 0, 'dominant': None, 'mixed': False}
    assert f([('a', 'war')]) == {'counts': [('war', 1)] + Z[1:], 'distinct': 1, 'dominant': 'war', 'mixed': False}
    assert f([('a', 'machine')])['dominant'] == 'machine'
    r = f([('a', 'nature'), ('b', 'journey'), ('c', 'nature')])
    assert r == {'counts': [('war', 0), ('journey', 1), ('building', 0), ('nature', 2), ('machine', 0)], 'distinct': 2, 'dominant': 'nature', 'mixed': False}
    assert f([('a', 'nature'), ('b', 'journey'), ('c', 'war')])['mixed'] is True
    assert f([('a', 'nature'), ('b', 'journey'), ('c', 'war')], 3)['mixed'] is False
    assert f([('a', 'nature'), ('b', 'journey')], 1)['mixed'] is True
    # tie: earlier domain in fixed order wins, whatever the input order
    assert f([('a', 'machine'), ('b', 'journey')])['dominant'] == 'journey'
    assert f([('a', 'journey'), ('b', 'machine')])['dominant'] == 'journey'
    assert f([('a', 'nature'), ('b', 'building'), ('c', 'nature'), ('d', 'building')])['dominant'] == 'building'
    assert f([('a', 'war'), ('b', 'machine'), ('c', 'machine')])['dominant'] == 'machine'
    assert f((['a', 'war'], ('b', 'nature')))['distinct'] == 2
    assert f([(d, 'war') for d in 'abcdefghijkl'])['counts'][0] == ('war', 12)
    assert f([('x' * 16, 'war')])['distinct'] == 1
    # defaults: max_domains 2 vs 1 and 3
    two = [('a', 'war'), ('b', 'nature')]
    three = two + [('c', 'machine')]
    assert f(two)['mixed'] is False and f(two, 1)['mixed'] is True
    assert f(three)['mixed'] is True and f(three, 3)['mixed'] is False and f(three, 2) == f(three)
    assert f([(str(i), DOMS[i % 5]) for i in range(5)], 5)['mixed'] is False and f([(str(i), DOMS[i % 5]) for i in range(5)], 4)['mixed'] is True
    _raises(ValueError, 'uses must contain at most 12 entries', f, [(str(i), 'war') for i in range(13)])
    rng = random.Random(737)
    for _ in range(600):
        us = [(str(i), rng.choice(DOMS)) for i in range(rng.randint(0, 12))]
        md = rng.randint(1, 5)
        assert f(us, md) == _oracle(us, md), (us, md)
        assert f(us) == _oracle(us, 2)


def _late(m):
    f = m.metaphor_domains
    MD = 'max_domains must be a nonbool integer between 1 and 5'
    UT = 'uses must be a list or tuple'
    US = 'uses must contain at most 12 entries'
    UP = 'each use must be a (label, domain) pair'
    LB = 'each label must be a string of 1 to 16 characters'
    DM = 'domain must be war, journey, building, nature or machine'
    LD = 'labels must be distinct'
    ok = [('a', 'war')]
    for bad in (0, 6, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MD, f, [], bad)
    f([], 1)
    f([], 5)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, UT, f, bad)
    for bad in ('ab', None, 5, ('a',), ('a', 'war', 1), (), {'a': 'war'}, L(['a', 'war']), T(('a', 'war'))):
        _raises(ValueError, UP, f, [bad])
        _raises(ValueError, UP, f, [('b', 'war'), bad])
    for bad in ('', 'x' * 17, None, 5, True, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, LB, f, [(bad, 'war')])
        _raises(ValueError, LB, f, [('b', 'war'), (bad, 'war')])
    for bad in ('', 'War', 'sea', None, 5, True, S('war'), LyingS('war'), b'war', ['war']):
        _raises(ValueError, DM, f, [('a', bad)])
        _raises(ValueError, DM, f, [('b', 'war'), ('a', bad)])
    _raises(ValueError, LD, f, [('a', 'war'), ('a', 'nature')])
    _raises(ValueError, LD, f, [('a', 'war'), ('b', 'war'), ('a', 'war')])
    _raises(ValueError, MD, f, None, I(1))
    _raises(TypeError, UT, f, None)
    _raises(ValueError, US, f, [1] * 13)
    _raises(ValueError, UP, f, [1])
    _raises(ValueError, LB, f, [(1, 1)])
    _raises(ValueError, DM, f, [('a', 1), ('a', 1)])
    _raises(ValueError, LD, f, [('a', 'war'), ('a', 'war')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_domains=2", "max_domains=3"),
    ("max_domains=2", "max_domains=1"),
    ("type(max_domains) is not int or not 1 <= max_domains <= 5", "not isinstance(max_domains, int) or not 1 <= max_domains <= 5"),
    ("type(max_domains) is not int or not 1 <= max_domains <= 5", "isinstance(max_domains, bool) or not isinstance(max_domains, int) or not 1 <= max_domains <= 5"),
    ("not 1 <= max_domains <= 5", "not 0 <= max_domains <= 5"),
    ("not 1 <= max_domains <= 5", "not 1 <= max_domains < 5"),
    ("not 1 <= max_domains <= 5", "not 1 <= max_domains <= 6"),
    ("type(uses) not in (list, tuple)", "not isinstance(uses, (list, tuple))"),
    ("len(uses) > 12", "len(uses) >= 12"),
    ("len(uses) > 12", "len(uses) > 13"),
    ("type(u) not in (list, tuple) or len(u) != 2", "not isinstance(u, (list, tuple)) or len(u) != 2"),
    ("type(u) not in (list, tuple) or len(u) != 2", "type(u) not in (list, tuple) or len(u) > 2"),
    ("type(u) not in (list, tuple) or len(u) != 2", "type(u) not in (list, tuple) or len(u) < 2"),
    ("type(label) is not str or not 1 <= len(label) <= 16", "not isinstance(label, str) or not 1 <= len(label) <= 16"),
    ("type(label) is not str or not 1 <= len(label) <= 16", "type(label) is not str or not 0 <= len(label) <= 16"),
    ("type(label) is not str or not 1 <= len(label) <= 16", "type(label) is not str or not 1 <= len(label) < 16"),
    ("type(label) is not str or not 1 <= len(label) <= 16", "type(label) is not str or not 1 <= len(label) <= 17"),
    ("type(dom) is not str or dom not in counts", "not isinstance(dom, str) or dom not in counts"),
    ("counts[dom] += 1", "counts[dom] += 2"),
    ("len(set(labels)) != len(labels)", "False"),
    ("if counts[d] > top:", "if counts[d] >= top:"),
    ("if counts[d] > top:", "if counts[d] < top:"),
    ("top = 0", "top = 1"),
    ("sum(1 for d in DOMAINS if counts[d] > 0)", "sum(counts.values())"),
    ("sum(1 for d in DOMAINS if counts[d] > 0)", "sum(1 for d in DOMAINS if counts[d] > 1)"),
    ("DOMAINS = ('war', 'journey', 'building', 'nature', 'machine')", "DOMAINS = ('journey', 'war', 'building', 'nature', 'machine')"),
    ("DOMAINS = ('war', 'journey', 'building', 'nature', 'machine')", "DOMAINS = ('war', 'journey', 'building', 'machine', 'nature')"),
    ("'mixed': distinct > max_domains", "'mixed': distinct >= max_domains"),
    ("'mixed': distinct > max_domains", "'mixed': distinct > max_domains + 1"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import analogy_mapping as mod

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
    assert mod.SCOPE == 'PARTIAL: one-to-one coverage count of a supplied analogy mapping, no meaning is judged'
    assert len(mod.NOT_CLAIMED) == 5 and 'truth of the analogy' in mod.NOT_CLAIMED and 'persuasiveness' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(src, tgt, mp):
    ms = [s for s, _ in mp]
    mt = [t for _, t in mp]
    us = [n for n in src if n not in ms]
    ut = [n for n in tgt if n not in mt]
    import math
    from fractions import Fraction
    return {'pairs': list(mp), 'unmapped_source': us, 'unmapped_target': ut,
            'percent': math.floor(Fraction(100 * len(mp), len(src))), 'complete': us == [] and ut == []}


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
    f = m.analogy_mapping
    assert f(['a'], ['x'], []) == {'pairs': [], 'unmapped_source': ['a'], 'unmapped_target': ['x'], 'percent': 0, 'complete': False}
    assert f(['a'], ['x'], [('a', 'x')]) == {'pairs': [('a', 'x')], 'unmapped_source': [], 'unmapped_target': [], 'percent': 100, 'complete': True}
    r = f(['a', 'b', 'c'], ['x', 'y'], [('c', 'y')])
    assert r == {'pairs': [('c', 'y')], 'unmapped_source': ['a', 'b'], 'unmapped_target': ['x'], 'percent': 33, 'complete': False}
    r = f(['a', 'b', 'c'], ['x', 'y', 'z'], [('a', 'z'), ('b', 'x')])
    assert r['percent'] == 66 and r['unmapped_source'] == ['c'] and r['unmapped_target'] == ['y']
    assert f(['a', 'b'], ['x', 'y', 'z'], [('a', 'x'), ('b', 'y')]) == {'pairs': [('a', 'x'), ('b', 'y')], 'unmapped_source': [], 'unmapped_target': ['z'], 'percent': 100, 'complete': False}
    assert f(('a', 'b'), ('x', 'y'), (['b', 'x'], ('a', 'y')))['complete'] is True
    assert f(['a', 'b', 'c', 'd'], ['w', 'x', 'y', 'z'], [('d', 'w')])['percent'] == 25
    assert f(['x' * 12], ['y' * 12], [('x' * 12, 'y' * 12)])['complete'] is True
    # default max_parts 4
    s4 = list('abcd')
    t4 = list('wxyz')
    f(s4, t4, list(zip(s4, t4)))
    _raises(ValueError, 'source must contain 1 to max_parts names', f, list('abcde'), t4, [])
    _raises(ValueError, 'target must contain 1 to max_parts names', f, s4, list('vwxyz'), [])
    assert f(list('abcde'), list('vwxyz'), [], 5)['percent'] == 0
    assert f(list('abcdefgh'), list('stuvwxyz'), [('a', 's')], 8)['percent'] == 12
    _raises(ValueError, 'source must contain 1 to max_parts names', f, s4[:3], t4[:2], [], 2)
    f(s4[:2], t4[:2], [], 2)
    rng = random.Random(736)
    for _ in range(500):
        ns, nt = rng.randint(1, 8), rng.randint(1, 8)
        src = ['s%d' % i for i in range(ns)]
        tgt = ['t%d' % i for i in range(nt)]
        k = rng.randint(0, min(ns, nt))
        mp = list(zip(rng.sample(src, k), rng.sample(tgt, k)))
        assert f(src, tgt, mp, 8) == _oracle(src, tgt, mp), (src, tgt, mp)


def _late(m):
    f = m.analogy_mapping
    MP = 'max_parts must be a nonbool integer between 1 and 8'
    a, x = ['a'], ['x']
    for bad in (0, 9, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MP, f, a, x, [], bad)
    f(a, x, [], 1)
    f(a, x, [], 8)
    for label in ('source', 'target'):
        def call(v, label=label):
            return (v, x, []) if label == 'source' else (a, v, [])
        for bad in ('ab', None, 5, {}, L(['a']), T(['a']), L(), T()):
            _raises(TypeError, label + ' must be a list or tuple', f, *call(bad))
        _raises(ValueError, label + ' must contain 1 to max_parts names', f, *call([]))
        _raises(ValueError, label + ' must contain 1 to max_parts names', f, *call(list('abcde')))
        for bad in ('', 'x' * 13, None, 5, True, S('b'), LyingS('b'), b'b', ['b']):
            _raises(ValueError, 'each name must be a string of 1 to 12 characters', f, *call([bad]))
            _raises(ValueError, 'each name must be a string of 1 to 12 characters', f, *call(['q', bad]))
        _raises(ValueError, label + ' names must be distinct', f, *call(['q', 'q']))
        _raises(ValueError, label + ' names must be distinct', f, *call(['q', 'r', 'q']))
    for bad in ('ab', None, 5, {}, L([('a', 'x')]), T([('a', 'x')]), L(), T()):
        _raises(TypeError, 'mapping must be a list or tuple', f, a, x, bad)
    _raises(ValueError, 'mapping must contain at most max_parts pairs', f, a, x, [('a', 'x')] * 5)
    for bad in ('ab', None, 5, ('a',), ('a', 'x', 'x'), (), {'a': 'x'}, L(['a', 'x']), T(('a', 'x'))):
        _raises(ValueError, 'each pair must be a (source_name, target_name) pair', f, a, x, [bad])
        _raises(ValueError, 'each pair must be a (source_name, target_name) pair', f, ['a', 'b'], ['x', 'y'], [('a', 'x'), bad])
    for bad in ('z', '', None, 5, True, S('a'), LyingS('a'), b'a', ['a'], 'x'):
        _raises(ValueError, 'mapped source name must be listed in source', f, a, x, [(bad, 'x')])
    for bad in ('z', '', None, 5, True, S('x'), LyingS('x'), b'x', ['x'], 'a'):
        _raises(ValueError, 'mapped target name must be listed in target', f, a, x, [('a', bad)])
    _raises(ValueError, 'each name may be used once', f, ['a', 'b'], ['x', 'y'], [('a', 'x'), ('a', 'y')])
    _raises(ValueError, 'each name may be used once', f, ['a', 'b'], ['x', 'y'], [('a', 'x'), ('b', 'x')])
    # validation order
    _raises(ValueError, MP, f, None, None, None, I(1))
    _raises(TypeError, 'source must be a list or tuple', f, None, None, None)
    _raises(ValueError, 'each name must be a string of 1 to 12 characters', f, [1], None, None)
    _raises(ValueError, 'source names must be distinct', f, ['a', 'a'], None, None)
    _raises(TypeError, 'target must be a list or tuple', f, a, None, None)
    _raises(TypeError, 'mapping must be a list or tuple', f, a, x, None)
    _raises(ValueError, 'mapping must contain at most max_parts pairs', f, a, x, [1] * 5)
    _raises(ValueError, 'each pair must be a (source_name, target_name) pair', f, a, x, [1])
    _raises(ValueError, 'mapped source name must be listed in source', f, a, x, [('z', 'q')])
    _raises(ValueError, 'mapped target name must be listed in target', f, a, x, [('a', 'q'), ('a', 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_parts=4", "max_parts=5"),
    ("max_parts=4", "max_parts=3"),
    ("type(max_parts) is not int or not 1 <= max_parts <= 8", "not isinstance(max_parts, int) or not 1 <= max_parts <= 8"),
    ("type(max_parts) is not int or not 1 <= max_parts <= 8", "isinstance(max_parts, bool) or not isinstance(max_parts, int) or not 1 <= max_parts <= 8"),
    ("not 1 <= max_parts <= 8", "not 0 <= max_parts <= 8"),
    ("not 1 <= max_parts <= 8", "not 1 <= max_parts < 8"),
    ("not 1 <= max_parts <= 8", "not 1 <= max_parts <= 9"),
    ("type(seq) not in (list, tuple)", "not isinstance(seq, (list, tuple))"),
    ("not 1 <= len(seq) <= max_parts", "not 0 <= len(seq) <= max_parts"),
    ("not 1 <= len(seq) <= max_parts", "not 1 <= len(seq) < max_parts"),
    ("type(n) is not str or not 1 <= len(n) <= 12", "not isinstance(n, str) or not 1 <= len(n) <= 12"),
    ("type(n) is not str or not 1 <= len(n) <= 12", "type(n) is not str or not 0 <= len(n) <= 12"),
    ("type(n) is not str or not 1 <= len(n) <= 12", "type(n) is not str or not 1 <= len(n) < 12"),
    ("type(n) is not str or not 1 <= len(n) <= 12", "type(n) is not str or not 1 <= len(n) <= 13"),
    ("len(set(seq)) != len(seq)", "False"),
    ("_names('source', source, max_parts)\n    _names('target', target, max_parts)", "_names('target', target, max_parts)\n    _names('source', source, max_parts)"),
    ("type(mapping) not in (list, tuple)", "not isinstance(mapping, (list, tuple))"),
    ("len(mapping) > max_parts", "len(mapping) >= max_parts"),
    ("type(p) not in (list, tuple) or len(p) != 2", "not isinstance(p, (list, tuple)) or len(p) != 2"),
    ("type(p) not in (list, tuple) or len(p) != 2", "type(p) not in (list, tuple) or len(p) > 2"),
    ("type(p) not in (list, tuple) or len(p) != 2", "type(p) not in (list, tuple) or len(p) < 2"),
    ("type(s) is not str or s not in source", "not isinstance(s, str) or s not in source"),
    ("type(s) is not str or s not in source", "type(s) is not str or s not in target"),
    ("type(t) is not str or t not in target", "not isinstance(t, str) or t not in target"),
    ("type(t) is not str or t not in target", "type(t) is not str or t not in source"),
    ("len({s for s, _ in pairs}) != len(pairs) or len({t for _, t in pairs}) != len(pairs)", "len({t for _, t in pairs}) != len(pairs)"),
    ("len({s for s, _ in pairs}) != len(pairs) or len({t for _, t in pairs}) != len(pairs)", "len({s for s, _ in pairs}) != len(pairs)"),
    ("us = [n for n in source if n not in used_s]", "us = [n for n in source if n in used_s]"),
    ("ut = [n for n in target if n not in used_t]", "ut = [n for n in target if n in used_t]"),
    ("ut = [n for n in target if n not in used_t]", "ut = [n for n in target if n not in used_s]"),
    ("len(pairs) * 100 // len(source)", "len(pairs) * 100 // len(target)"),
    ("len(pairs) * 100 // len(source)", "round(len(pairs) * 100 / len(source))"),
    ("len(pairs) * 100 // len(source)", "len(pairs) * 100 // (len(source) + 1)"),
    ("'complete': not us and not ut", "'complete': not us"),
    ("'complete': not us and not ut", "'complete': not ut"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

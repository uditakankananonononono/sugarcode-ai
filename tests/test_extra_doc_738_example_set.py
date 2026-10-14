import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import example_set as mod

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
    assert mod.SCOPE == 'PARTIAL: kind tally and order check of supplied example labels, no example is judged'
    assert len(mod.NOT_CLAIMED) == 5 and 'coverage of the idea' in mod.NOT_CLAIMED and 'real clarity' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(ex):
    ks = [k for _, k in ex]
    cnt = [('typical', sum(1 for k in ks if k == 'typical')), ('edge', sum(1 for k in ks if k == 'edge')),
           ('counter', sum(1 for k in ks if k == 'counter'))]
    miss = [k for k, c in cnt if not c]
    st = bool(ks) and ks[0] == 'typical'
    return {'counts': cnt, 'missing': miss, 'starts_typical': st, 'ok': miss == [] and st}


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
    def __hash__(self): return hash('edge')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def _core(m):
    f = m.example_set
    assert f([]) == {'counts': [('typical', 0), ('edge', 0), ('counter', 0)], 'missing': ['typical', 'edge', 'counter'], 'starts_typical': False, 'ok': False}
    assert f([('a', 'typical')]) == {'counts': [('typical', 1), ('edge', 0), ('counter', 0)], 'missing': ['edge', 'counter'], 'starts_typical': True, 'ok': False}
    assert f([('a', 'typical'), ('b', 'edge'), ('c', 'counter')])['ok'] is True
    r = f([('a', 'edge'), ('b', 'typical'), ('c', 'counter')])
    assert r['missing'] == [] and r['starts_typical'] is False and r['ok'] is False
    assert f([('a', 'typical'), ('b', 'counter')])['missing'] == ['edge']
    assert f([('a', 'typical'), ('b', 'edge')])['missing'] == ['counter']
    assert f([('a', 'counter'), ('b', 'edge')])['missing'] == ['typical']
    assert f([('a', 'typical'), ('b', 'typical'), ('c', 'edge'), ('d', 'counter'), ('e', 'counter')])['counts'] == [('typical', 2), ('edge', 1), ('counter', 2)]
    assert f((['a', 'typical'], ('b', 'edge'), ('c', 'counter')))['ok'] is True
    assert f([('x' * 16, 'typical')])['starts_typical'] is True
    # default max_examples 6
    e6 = [('n%d' % i, 'typical') for i in range(6)]
    f(e6)
    _raises(ValueError, 'examples must contain at most max_examples entries', f, e6 + [('z', 'edge')])
    assert f(e6 + [('z', 'edge')], 7)['counts'][1] == ('edge', 1)
    assert f([('n%d' % i, 'edge') for i in range(12)], 12)['counts'][1] == ('edge', 12)
    _raises(ValueError, 'examples must contain at most max_examples entries', f, e6[:3], 2)
    f(e6[:2], 2)
    rng = random.Random(738)
    for _ in range(500):
        ex = [('n%d' % i, rng.choice(('typical', 'edge', 'counter'))) for i in range(rng.randint(0, 12))]
        assert f(ex, 12) == _oracle(ex), ex


def _late(m):
    f = m.example_set
    ME = 'max_examples must be a nonbool integer between 1 and 12'
    ET = 'examples must be a list or tuple'
    ES = 'examples must contain at most max_examples entries'
    EP = 'each example must be a (name, kind) pair'
    NM = 'each name must be a string of 1 to 16 characters'
    KD = 'kind must be typical, edge or counter'
    ND = 'names must be distinct'
    ok = [('a', 'typical')]
    for bad in (0, 13, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, ME, f, [], bad)
    f([], 1)
    f([], 12)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, ET, f, bad)
    for bad in ('ab', None, 5, ('a',), ('a', 'edge', 1), (), {'a': 'edge'}, L(['a', 'edge']), T(('a', 'edge'))):
        _raises(ValueError, EP, f, [bad])
        _raises(ValueError, EP, f, [('b', 'edge'), bad])
    for bad in ('', 'x' * 17, None, 5, True, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, NM, f, [(bad, 'edge')])
        _raises(ValueError, NM, f, [('b', 'edge'), (bad, 'edge')])
    for bad in ('', 'Edge', 'odd', None, 5, True, S('edge'), LyingS('edge'), b'edge', ['edge']):
        _raises(ValueError, KD, f, [('a', bad)])
        _raises(ValueError, KD, f, [('b', 'edge'), ('a', bad)])
    _raises(ValueError, ND, f, [('a', 'edge'), ('a', 'edge')])
    _raises(ValueError, ND, f, [('a', 'edge'), ('b', 'edge'), ('a', 'typical')])
    _raises(ValueError, ME, f, None, I(1))
    _raises(TypeError, ET, f, None)
    _raises(ValueError, ES, f, [1] * 7)
    _raises(ValueError, EP, f, [1])
    _raises(ValueError, NM, f, [(1, 1)])
    _raises(ValueError, KD, f, [('a', 1), ('a', 1)])
    _raises(ValueError, ND, f, [('a', 'edge'), ('a', 'edge')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_examples=6", "max_examples=7"),
    ("max_examples=6", "max_examples=5"),
    ("type(max_examples) is not int or not 1 <= max_examples <= 12", "not isinstance(max_examples, int) or not 1 <= max_examples <= 12"),
    ("type(max_examples) is not int or not 1 <= max_examples <= 12", "isinstance(max_examples, bool) or not isinstance(max_examples, int) or not 1 <= max_examples <= 12"),
    ("not 1 <= max_examples <= 12", "not 0 <= max_examples <= 12"),
    ("not 1 <= max_examples <= 12", "not 1 <= max_examples < 12"),
    ("not 1 <= max_examples <= 12", "not 1 <= max_examples <= 13"),
    ("type(examples) not in (list, tuple)", "not isinstance(examples, (list, tuple))"),
    ("len(examples) > max_examples", "len(examples) >= max_examples"),
    ("type(e) not in (list, tuple) or len(e) != 2", "not isinstance(e, (list, tuple)) or len(e) != 2"),
    ("type(e) not in (list, tuple) or len(e) != 2", "type(e) not in (list, tuple) or len(e) > 2"),
    ("type(e) not in (list, tuple) or len(e) != 2", "type(e) not in (list, tuple) or len(e) < 2"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "not isinstance(name, str) or not 1 <= len(name) <= 16"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "type(name) is not str or not 0 <= len(name) <= 16"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "type(name) is not str or not 1 <= len(name) < 16"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "type(name) is not str or not 1 <= len(name) <= 17"),
    ("type(kind) is not str or kind not in KINDS", "not isinstance(kind, str) or kind not in KINDS"),
    ("len(set(names)) != len(names)", "False"),
    ("KINDS = ('typical', 'edge', 'counter')", "KINDS = ('edge', 'typical', 'counter')"),
    ("KINDS = ('typical', 'edge', 'counter')", "KINDS = ('typical', 'counter', 'edge')"),
    ("missing = [k for k, c in counts if c == 0]", "missing = [k for k, c in counts if c == 1]"),
    ("missing = [k for k, c in counts if c == 0]", "missing = [k for k, c in counts if c <= 1]"),
    ("first = len(kinds) > 0 and kinds[0] == 'typical'", "first = kinds[-1:] == ['typical']"),
    ("first = len(kinds) > 0 and kinds[0] == 'typical'", "first = 'typical' in kinds"),
    ("first = len(kinds) > 0 and kinds[0] == 'typical'", "first = len(kinds) > 0"),
    ("'ok': not missing and first", "'ok': not missing"),
    ("'ok': not missing and first", "'ok': first"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

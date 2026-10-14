import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import adapter_fields as mod

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
    assert mod.SCOPE == 'PARTIAL: field renaming over one supplied flat record, no real interfaces'
    assert len(mod.NOT_CLAIMED) >= 4 and 'schemas' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(mp, rec):
    """Independent: index scans over both pair lists."""
    conv = [(d, next(v for f, v in rec if f == s)) for s, d in mp if any(f == s for f, _ in rec)]
    miss = [s for s, _ in mp if not any(f == s for f, _ in rec)]
    unm = [f for f, _ in rec if not any(s == f for s, _ in mp)]
    return {'converted': conv, 'missing': miss, 'unmapped': unm}


def _core(m):
    assert m.adapter_fields([], []) == {'converted': [], 'missing': [], 'unmapped': []}
    r = m.adapter_fields([('a', 'x'), ('b', 'y'), ('c', 'z')], [('c', 3), ('q', 9), ('a', 1)])
    assert r == {'converted': [('x', 1), ('z', 3)], 'missing': ['b'], 'unmapped': ['q']}
    assert m.adapter_fields([('a', 'b'), ('b', 'a')], [('a', 1), ('b', 2)])['converted'] == [('b', 1), ('a', 2)]   # swap is fine
    assert m.adapter_fields([('a', 'a')], [('a', -1000)])['converted'] == [('a', -1000)]
    assert m.adapter_fields([['a', 'x']], (('a', 1000),))['converted'] == [('x', 1000)]
    assert m.adapter_fields([], [('only', 0)]) == {'converted': [], 'missing': [], 'unmapped': ['only']}
    assert m.adapter_fields([('a', 'x')], []) == {'converted': [], 'missing': ['a'], 'unmapped': []}
    assert m.adapter_fields([('a', 'x')], [('a', 0)])['converted'] == [('x', 0)]       # a zero value is still present
    # the target name of one rule does not make a record field mapped
    assert m.adapter_fields([('a', 'x')], [('x', 5)]) == {'converted': [], 'missing': ['a'], 'unmapped': ['x']}
    mp = [('s%d' % i, 't%d' % i) for i in range(8)]
    rec = [('s%d' % i, i) for i in range(7, -1, -1)] + [('u1', 1), ('u2', 2)]
    r = m.adapter_fields(mp, rec)
    assert r['converted'] == [('t%d' % i, i) for i in range(8)] and r['unmapped'] == ['u1', 'u2'] and r['missing'] == []
    assert m.adapter_fields([('n' * 12, 'm' * 12)], [('n' * 12, 1)])['converted'] == [('m' * 12, 1)]
    rng = random.Random(661)
    for _ in range(500):
        names = ['f%d' % i for i in range(14)]
        mp = list(zip(rng.sample(names, rng.randint(0, 8)), rng.sample(['t%d' % i for i in range(10)], 8)))
        mp = mp[:rng.randint(0, len(mp))]
        rec = [(n, rng.randint(-1000, 1000)) for n in rng.sample(names, rng.randint(0, 10))]
        assert m.adapter_fields(mp, rec) == _oracle(mp, rec), (mp, rec)


def _late(m):
    MT = 'mapping must be a list or tuple'
    MS = 'mapping must contain at most 8 entries'
    RT = 'record must be a list or tuple'
    RS = 'record must contain at most 10 entries'
    MP = 'each mapping entry must be a (source, target) pair'
    SR = 'sources must be strings of 1 to 12 characters'
    DS = 'duplicate source'
    TG = 'targets must be strings of 1 to 12 characters'
    DT = 'duplicate target'
    RP = 'each record entry must be a (field, value) pair'
    FD = 'fields must be strings of 1 to 12 characters'
    DF = 'duplicate field'
    VL = 'value must be a nonbool integer between -1000 and 1000'
    mok = ('a', 'x')
    rok = ('a', 1)
    for bad in ('ab', None, 5, {}, L([mok]), T([mok]), L(), T()):
        _raises(TypeError, MT, m.adapter_fields, bad, [])
    _raises(TypeError, MT, m.adapter_fields, L([mok] * 9), [])
    _raises(ValueError, MS, m.adapter_fields, [mok] * 9, [])
    assert m.adapter_fields([('s%d' % i, 't%d' % i) for i in range(8)], [])['missing'][-1] == 's7'
    for bad in ('ab', None, 5, {}, L([rok]), T([rok]), L(), T()):
        _raises(TypeError, RT, m.adapter_fields, [], bad)
    _raises(TypeError, RT, m.adapter_fields, [], L([rok] * 11))
    _raises(ValueError, RS, m.adapter_fields, [], [rok] * 11)
    assert m.adapter_fields([], [('f%d' % i, 1) for i in range(10)])['unmapped'][-1] == 'f9'
    for K in (L, T):
        for bad in (K(mok), K(('a',))):
            _raises(ValueError, MP, m.adapter_fields, [bad], [])
            _raises(ValueError, MP, m.adapter_fields, [mok, bad], [])
        for bad in (K(rok), K(('a',))):
            _raises(ValueError, RP, m.adapter_fields, [], [bad])
            _raises(ValueError, RP, m.adapter_fields, [], [rok, bad])
    for bad in ('ab', None, 5, ('a',), ('a', 'x', 'y'), ()):
        _raises(ValueError, MP, m.adapter_fields, [bad], [])
        _raises(ValueError, MP, m.adapter_fields, [mok, bad], [])
        _raises(ValueError, RP, m.adapter_fields, [], [bad])
        _raises(ValueError, RP, m.adapter_fields, [], [rok, bad])
    for bad in ('', 'x' * 13, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, SR, m.adapter_fields, [(bad, 'y')], [])
        _raises(ValueError, SR, m.adapter_fields, [mok, (bad, 'y')], [])
        _raises(ValueError, TG, m.adapter_fields, [('b', bad)], [])
        _raises(ValueError, TG, m.adapter_fields, [mok, ('b', bad)], [])
        _raises(ValueError, FD, m.adapter_fields, [], [(bad, 1)])
        _raises(ValueError, FD, m.adapter_fields, [], [rok, (bad, 1)])
    _raises(ValueError, DS, m.adapter_fields, [mok, ('a', 'y')], [])
    _raises(ValueError, DS, m.adapter_fields, [mok, ('b', 'y'), ('a', 'z')], [])
    _raises(ValueError, DT, m.adapter_fields, [mok, ('b', 'x')], [])
    _raises(ValueError, DT, m.adapter_fields, [mok, ('b', 'y'), ('c', 'x')], [])
    _raises(ValueError, DF, m.adapter_fields, [], [rok, ('a', 2)])
    _raises(ValueError, DF, m.adapter_fields, [], [rok, ('b', 1), ('a', 1)])
    for bad in (-1001, 1001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, VL, m.adapter_fields, [], [('b', bad)])
        _raises(ValueError, VL, m.adapter_fields, [], [rok, ('b', bad)])
    # order: mapping type, size, record type, size, mapping rows (shape, source, dup source, target, dup target), record rows
    _raises(TypeError, MT, m.adapter_fields, L([1]), L([1]))
    _raises(ValueError, MS, m.adapter_fields, [1] * 9, L([1]))
    _raises(TypeError, RT, m.adapter_fields, [1], L([1]))
    _raises(ValueError, RS, m.adapter_fields, [1], [1] * 11)
    _raises(ValueError, MP, m.adapter_fields, [1], [1])
    _raises(ValueError, SR, m.adapter_fields, [(5, 5)], [1])
    _raises(ValueError, DS, m.adapter_fields, [mok, ('a', 5)], [1])
    _raises(ValueError, TG, m.adapter_fields, [('b', 5)], [1])
    _raises(ValueError, DT, m.adapter_fields, [mok, ('b', 'x')], [1])
    _raises(ValueError, RP, m.adapter_fields, [mok], [1])
    _raises(ValueError, FD, m.adapter_fields, [mok], [(5, I(1))])
    _raises(ValueError, DF, m.adapter_fields, [mok], [rok, ('a', I(1))])
    _raises(ValueError, VL, m.adapter_fields, [mok], [('b', I(1))])


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
    def __hash__(self): return hash('b')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(v) is not str or not 1 <= len(v) <= 12", "not isinstance(v, str) or not 1 <= len(v) <= 12"),
    ("not 1 <= len(v) <= 12", "not 0 <= len(v) <= 12"),
    ("not 1 <= len(v) <= 12", "not 1 <= len(v) < 12"),
    ("not 1 <= len(v) <= 12", "not 1 <= len(v) <= 13"),
    ("type(mapping) not in (list, tuple)", "not isinstance(mapping, (list, tuple))"),
    ("len(mapping) > 8", "len(mapping) >= 8"),
    ("len(mapping) > 8", "len(mapping) > 9"),
    ("type(record) not in (list, tuple)", "not isinstance(record, (list, tuple))"),
    ("len(record) > 10", "len(record) >= 10"),
    ("len(record) > 10", "len(record) > 11"),
    ("type(p) not in (list, tuple) or len(p) != 2", "not isinstance(p, (list, tuple)) or len(p) != 2"),
    ("or len(p) != 2", "or len(p) > 2"),
    ("or len(p) != 2", "or len(p) < 2"),
    ("if src in sources:", "if False:"),
    ("if dst in targets:", "if False:"),
    ("if field in values:", "if False:"),
    ("type(value) is not int or not -1000 <= value <= 1000", "not isinstance(value, int) or not -1000 <= value <= 1000"),
    ("type(value) is not int or not -1000 <= value <= 1000", "isinstance(value, bool) or not isinstance(value, int) or not -1000 <= value <= 1000"),
    ("not -1000 <= value <= 1000", "not -999 <= value <= 1000"),
    ("not -1000 <= value <= 1000", "not -1000 <= value <= 999"),
    ("if src in values:", "if src not in values:"),
    ("converted.append((dst, values[src]))", "converted.append((src, values[src]))"),
    ("missing.append(src)", "missing.append(dst)"),
    ("unmapped = [f for f in values if f not in sources]", "unmapped = [f for f in values if f not in sources and f not in targets]"),
    ("unmapped = [f for f in values if f not in sources]", "unmapped = [f for f in values if f in sources]"),
    ("unmapped = [f for f in values if f not in sources]", "unmapped = sorted(f for f in values if f not in sources)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)

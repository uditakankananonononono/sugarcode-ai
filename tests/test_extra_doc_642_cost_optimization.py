import datetime
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import cost_optimization as mod

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
    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
    return True


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(items, target):
    # DP for the minimum impact, then enumerate by size to confirm the tie-break
    n = len(items)
    INF = 10 ** 9
    best = {0: 0}
    for _, cost, imp in items:
        nxt = dict(best)
        for s, v in best.items():
            k = min(s + cost, target)
            if k not in nxt or v + imp < nxt[k]:
                nxt[k] = v + imp
        best = nxt
    if target not in best:
        return None
    min_imp = best[target]
    for size in range(n + 1):
        for combo in itertools.combinations(range(n), size):
            if sum(items[i][1] for i in combo) >= target and sum(items[i][2] for i in combo) == min_imp:
                return combo, min_imp
    raise AssertionError('unreachable')


def _core(m):
    items = [('cdn', 50, 3), ('logs', 30, 1), ('gpu', 100, 9), ('wiki', 20, 1)]
    r = m.cut_costs(items, 50)
    assert r == {'feasible': True, 'cut': ['logs', 'wiki'], 'savings': 50, 'impact': 2}
    assert m.cut_costs(items, 0) == {'feasible': True, 'cut': [], 'savings': 0, 'impact': 0}
    assert m.cut_costs(items, 201) == {'feasible': False, 'cut': [], 'savings': 0, 'impact': 0}
    assert m.cut_costs(items, 200)['cut'] == ['cdn', 'logs', 'gpu', 'wiki']
    assert m.cut_costs([], 0)['feasible'] is True and m.cut_costs([], 1)['feasible'] is False
    # tie-break: equal impact, fewer items first, then smallest index tuple
    assert m.cut_costs([('a', 5, 2), ('b', 5, 2), ('c', 10, 4)], 10)['cut'] == ['c']
    assert m.cut_costs([('a', 5, 2), ('b', 5, 2), ('c', 5, 2)], 10)['cut'] == ['a', 'b']
    rng = random.Random(642)
    for _ in range(250):
        items = [('i%d' % i, rng.randint(1, 20), rng.randint(1, 10)) for i in range(rng.randint(0, 9))]
        target = rng.randint(0, 120)
        r = m.cut_costs(tuple(items), target)
        o = _oracle(items, target)
        if o is None:
            assert r == {'feasible': False, 'cut': [], 'savings': 0, 'impact': 0}
        else:
            combo, imp = o
            assert r == {'feasible': True, 'cut': [items[i][0] for i in combo],
                         'savings': sum(items[i][1] for i in combo), 'impact': imp}
    assert m.cut_costs([('x%d' % i, 100000, 10) for i in range(12)], 1000000)['feasible'] is True
    _raises(TypeError, 'items must be a list or tuple', m.cut_costs, 'ab', 0)
    _raises(ValueError, 'items must contain at most 12 entries', m.cut_costs, [('a%d' % i, 1, 1) for i in range(13)], 0)
    for bad in (-1, 1000001, True, 1.0):
        _raises(ValueError, 'target must be a nonbool integer between 0 and 1000000', m.cut_costs, [], bad)
    _raises(ValueError, 'each item must be a (name, cost, impact) triple', m.cut_costs, [('a', 1)], 0)
    _raises(ValueError, 'each item must be a (name, cost, impact) triple', m.cut_costs, ['abc'], 0)
    for bad in ('', 'x' * 17, 1):
        _raises(ValueError, 'item names must be strings of 1 to 16 characters', m.cut_costs, [(bad, 1, 1)], 0)
    for bad in (0, 100001, True, 1.0):
        _raises(ValueError, 'cost must be a nonbool integer between 1 and 100000', m.cut_costs, [('a', bad, 1)], 0)
    for bad in (0, 11, True, 1.0):
        _raises(ValueError, 'impact must be a nonbool integer between 1 and 10', m.cut_costs, [('a', 1, bad)], 0)
    _raises(ValueError, 'item names must be unique', m.cut_costs, [('a', 1, 1), ('a', 2, 2)], 0)
    _raises(ValueError, 'items must contain at most 12 entries', m.cut_costs, [None] * 13, 'zzz')



class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class Dc(dict):
    pass


class S(str):
    pass


def _late(m):
    _raises(TypeError, 'items must be a list or tuple', m.cut_costs, L([('a', 1, 1)]), 0)
    _raises(ValueError, 'each item must be a (name, cost, impact) triple', m.cut_costs, [('a', 1, 1), T(('b', 1, 1))], 0)
    _raises(ValueError, 'item names must be strings of 1 to 16 characters', m.cut_costs, [('a', 1, 1), (S('b'), 1, 1)], 0)
    _raises(ValueError, 'target must be a nonbool integer between 0 and 1000000', m.cut_costs, [('a', 1, 1)], I(1))
    _raises(ValueError, 'cost must be a nonbool integer between 1 and 100000', m.cut_costs, [('a', 1, 1), ('b', I(2), 1)], 0)
    _raises(ValueError, 'impact must be a nonbool integer between 1 and 10', m.cut_costs, [('a', 1, 1), ('b', 2, I(1))], 0)
    ok = ('a', 1, 1)
    _raises(ValueError, 'each item must be a (name, cost, impact) triple', m.cut_costs, [ok, ('b', 1)], 0)
    _raises(ValueError, 'item names must be strings of 1 to 16 characters', m.cut_costs, [ok, ('', 1, 1)], 0)
    _raises(ValueError, 'cost must be a nonbool integer between 1 and 100000', m.cut_costs, [ok, ('b', 0, 1)], 0)
    _raises(ValueError, 'cost must be a nonbool integer between 1 and 100000', m.cut_costs, [ok, ('b', True, 1)], 0)
    _raises(ValueError, 'impact must be a nonbool integer between 1 and 10', m.cut_costs, [ok, ('b', 1, 11)], 0)
    _raises(ValueError, 'impact must be a nonbool integer between 1 and 10', m.cut_costs, [ok, ('b', 1, True)], 0)
    _raises(ValueError, 'item names must be unique', m.cut_costs, [ok, ('b', 1, 1), ('a', 2, 2)], 0)
    _raises(ValueError, 'cost must be a nonbool integer between 1 and 100000', m.cut_costs, [('x%d' % i, 1, 1) for i in range(11)] + [('z', 100001, 1)], 0)


def battery(m):
    _core(m)
    _late(m)

MUTANTS = [
    ('type(items) not in (list, tuple)', 'not isinstance(items, (list, tuple))'),
    ('saved < target', 'saved <= target'), ('key < best[0]', 'key > best[0]'),
    ('key = (sum(items[i][2] for i in idx), len(idx), idx)', 'key = (len(idx), sum(items[i][2] for i in idx), idx)'),
    ('key = (sum(items[i][2] for i in idx), len(idx), idx)', 'key = (sum(items[i][2] for i in idx), idx)'),
    ('key = (sum(items[i][2] for i in idx), len(idx), idx)', 'key = (sum(items[i][2] for i in idx), len(idx), idx[::-1])'),
    ('best is None or', 'best is not None and'), ("'savings': saved", "'savings': target"),
    ('len(items) > 12', 'len(items) > 13'), ('_int(target, 0, 1000000, ', '_int(target, 1, 1000000, '),
    ('_int(target, 0, 1000000, ', '_int(target, 0, 1000001, '), ('_int(it[1], 1, 100000, ', '_int(it[1], 1, 100001, '),
    ('_int(it[1], 1, 100000, ', '_int(it[1], 0, 100000, '), ('_int(it[2], 1, 10, ', '_int(it[2], 1, 11, '),
    ('_int(it[2], 1, 10, ', '_int(it[2], 0, 10, '), ('type(v) is not int', 'isinstance(v, bool) or not isinstance(v, int)'),
    ('len({it[0] for it in items}) != len(items)', 'False'), ('1 <= len(it[0]) <= 16', '1 <= len(it[0]) <= 17'),
    ('1 <= len(it[0]) <= 16', '0 <= len(it[0]) <= 16'), ('len(it) != 3', 'len(it) != 4'),
    ("'feasible': False", "'feasible': True"), ('1 << n', '(1 << n) - 1'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    battery(mod)

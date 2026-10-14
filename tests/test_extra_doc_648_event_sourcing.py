import datetime
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import event_sourcing as mod

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


def _oracle(events, upto):
    """Returns (state, None) or (None, index of first inconsistent remove)."""
    prefix = events[:upto]
    for i, e in enumerate(prefix):
        if e[0] == 'remove':
            last_clear = max([j for j in range(i) if prefix[j][0] == 'clear'], default=-1)
            have = sum(x[2] if x[0] == 'add' else -x[2] for x in prefix[last_clear + 1:i] if x[0] != 'clear' and x[1] == e[1])
            if have < e[2]:
                return None, i
    last_clear = max([j for j in range(len(prefix)) if prefix[j][0] == 'clear'], default=-1)
    tail = prefix[last_clear + 1:]
    state = {}
    for sku in {x[1] for x in tail}:
        q = sum(x[2] if x[0] == 'add' else -x[2] for x in tail if x[1] == sku)
        if q:
            state[sku] = q
    return state, None


def _rand_log(rng, n):
    log = []
    for _ in range(n):
        k = rng.random()
        if k < 0.08:
            log.append(('clear',))
        elif k < 0.6:
            log.append(('add', rng.choice('abc'), rng.randint(1, 5)))
        else:
            log.append(('remove', rng.choice('abc'), rng.randint(1, 5)))
    return log


def _core(m):
    log = [('add', 'x', 5), ('add', 'y', 2), ('remove', 'x', 5), ('add', 'x', 1)]
    assert m.replay(log) == {'state': {'y': 2, 'x': 1}, 'version': 4}
    assert m.replay(log, 2) == {'state': {'x': 5, 'y': 2}, 'version': 2}
    assert m.replay(log, 0) == {'state': {}, 'version': 0}
    assert m.replay([('add', 'x', 1), ('clear',), ('add', 'y', 1)]) == {'state': {'y': 1}, 'version': 3}
    assert m.replay([]) == {'state': {}, 'version': 0}
    _raises(ValueError, 'remove exceeds quantity at event 1', m.replay, [('add', 'x', 1), ('remove', 'x', 2)])
    _raises(ValueError, 'remove exceeds quantity at event 2', m.replay, [('add', 'x', 1), ('clear',), ('remove', 'x', 1)])
    assert m.replay([('add', 'x', 1), ('remove', 'x', 2)], 1)['version'] == 1
    rng = random.Random(648)
    for _ in range(400):
        events = _rand_log(rng, rng.randint(0, 30))
        upto = rng.randint(0, len(events))
        want, bad = _oracle(events, upto)
        if bad is None:
            assert m.replay(events, upto) == {'state': want, 'version': upto}
            full, fbad = _oracle(events, len(events))
            if fbad is None:
                assert m.replay(tuple(events)) == {'state': full, 'version': len(events)}
        else:
            _raises(ValueError, 'remove exceeds quantity at event %d' % bad, m.replay, events, upto)
    # append: optimistic concurrency
    assert m.append([], ('add', 'x', 2), 0) == [('add', 'x', 2)]
    base = [('add', 'x', 2)]
    assert m.append(base, ('remove', 'x', 2), 1) == [('add', 'x', 2), ('remove', 'x', 2)] and base == [('add', 'x', 2)]
    _raises(ValueError, 'version conflict: expected 0, found 1', m.append, base, ('add', 'x', 1), 0)
    _raises(ValueError, 'version conflict: expected 2, found 1', m.append, base, ('add', 'x', 1), 2)
    _raises(ValueError, 'remove exceeds quantity at event 1', m.append, base, ('remove', 'x', 3), 1)
    assert len(m.append([('add', 'x', 1)] * 99, ('clear',), 99)) == 100
    _raises(ValueError, 'events must contain at most 100 entries', m.append, [('add', 'x', 1)] * 100, ('clear',), 100)
    _raises(ValueError, 'events must contain at most 100 entries', m.replay, [('clear',)] * 101)
    assert m.replay([('clear',)] * 100)['version'] == 100
    _raises(TypeError, 'events must be a list or tuple', m.replay, 'ab')
    for bad in (['x'], [()], [('boom', 'x', 1)], [(1, 'x', 1)], ['add'], [None]):
        _raises(ValueError, 'each event must be add, remove or clear', m.replay, bad)
    _raises(ValueError, 'clear takes no arguments', m.replay, [('clear', 1)])
    for bad in ([('add', 'x')], [('add', 'x', 1, 2)], [('remove',)]):
        _raises(ValueError, 'add and remove take a sku and a quantity', m.replay, bad)
    for bad in ('', 'x' * 17, 1):
        _raises(ValueError, 'sku must be a string of 1 to 16 characters', m.replay, [('add', bad, 1)])
    for bad in (0, 1001, True, 1.0, '1'):
        _raises(ValueError, 'quantity must be a nonbool integer between 1 and 1000', m.replay, [('add', 'x', bad)])
    for bad in (-1, 2, True, 1.0, '1'):
        _raises(ValueError, 'upto must be a nonbool integer between 0 and the number of events', m.replay, [('clear',)], bad)
    for bad in (-1, True, 1.0, None):
        _raises(ValueError, 'expected_version must be a nonbool integer of at least 0', m.append, [], ('clear',), bad)
    _raises(ValueError, 'each event must be add, remove or clear', m.append, [], 'x', 0)
    _raises(TypeError, 'events must be a list or tuple', m.append, 'ab', ('clear',), 0)
    _raises(ValueError, 'events must contain at most 100 entries', m.replay, [None] * 101, 'zzz')



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
    _raises(TypeError, 'events must be a list or tuple', m.replay, L([('clear',)]))
    _raises(ValueError, 'each event must be add, remove or clear', m.replay, [('clear',), T(('clear',))])
    _raises(ValueError, 'each event must be add, remove or clear', m.replay, [('clear',), (S('add'), 'x', 1)])
    _raises(ValueError, 'sku must be a string of 1 to 16 characters', m.replay, [('clear',), ('add', S('x'), 1)])
    _raises(ValueError, 'quantity must be a nonbool integer between 1 and 1000', m.replay, [('add', 'x', 1), ('add', 'x', I(1))])
    _raises(ValueError, 'upto must be a nonbool integer between 0 and the number of events', m.replay, [('add', 'x', 1)], I(1))
    _raises(ValueError, 'expected_version must be a nonbool integer of at least 0', m.append, [], ('clear',), I(0))
    two = [('add', 'x', 2), ('add', 'y', 3)]
    assert m.replay(two) == {'state': {'x': 2, 'y': 3}, 'version': 2}
    assert m.replay(two, None) == m.replay(two)
    ok = ('add', 'x', 1)
    _raises(ValueError, 'each event must be add, remove or clear', m.replay, [ok, 'bad'])
    _raises(ValueError, 'each event must be add, remove or clear', m.replay, [ok, ('boom', 'x', 1)])
    _raises(ValueError, 'clear takes no arguments', m.replay, [ok, ('clear', 1)])
    _raises(ValueError, 'add and remove take a sku and a quantity', m.replay, [ok, ('add', 'x')])
    _raises(ValueError, 'sku must be a string of 1 to 16 characters', m.replay, [ok, ('add', '', 1)])
    _raises(ValueError, 'quantity must be a nonbool integer between 1 and 1000', m.replay, [ok, ('add', 'x', 0)])
    _raises(ValueError, 'quantity must be a nonbool integer between 1 and 1000', m.replay, [ok, ('add', 'x', True)])
    _raises(ValueError, 'quantity must be a nonbool integer between 1 and 1000', m.replay, [ok] * 99 + [('add', 'x', 1001)])
    _raises(ValueError, 'each event must be add, remove or clear', m.append, [ok, 'bad'], ok, 2)


def battery(m):
    _core(m)
    _late(m)

MUTANTS = [
    ('type(events) not in (list, tuple)', 'not isinstance(events, (list, tuple))'),
    ('if upto is None:\n        upto = len(events)', 'if upto is None:\n        upto = 0'),
    ('if upto is None:\n        upto = len(events)', 'if upto is None:\n        upto = len(events) - 1'),
    ("stock = {}\n        elif", "pass\n        elif"), ("left = stock.get(e[1], 0) - e[2]", "left = stock.get(e[1], 0) + e[2]"),
    ('if left < 0:', 'if left <= 0:'), ('if left:\n                stock[e[1]] = left', 'if True:\n                stock[e[1]] = left'),
    ("stock[e[1]] = stock.get(e[1], 0) + e[2]", "stock[e[1]] = e[2]"), ('events[:upto]', 'events[:upto + 1]'),
    ("'version': upto", "'version': len(events)"), ("% i)", "% (i + 1))"), ('expected_version != len(events)', 'expected_version > len(events)'),
    ('replay(extended)', 'pass'), ('list(events) + [event]', 'list(events)'), ('len(events) > 100', 'len(events) > 101'),
 ('expected_version < 0', 'expected_version < 1'),
    ('type(expected_version) is not int', 'isinstance(expected_version, bool) or not isinstance(expected_version, int)'), ('type(upto) is not int', 'isinstance(upto, bool) or not isinstance(upto, int)'), ('not 0 <= upto <= len(events)', 'not 0 <= upto < len(events)'),
    ('1 <= e[2] <= 1000', '1 <= e[2] <= 1001'), ('1 <= e[2] <= 1000', '0 <= e[2] <= 1000'), ('type(e[2]) is not int', 'isinstance(e[2], bool) or not isinstance(e[2], int)'),
    ('1 <= len(e[1]) <= 16', '1 <= len(e[1]) <= 17'), ('1 <= len(e[1]) <= 16', '0 <= len(e[1]) <= 16'), ('type(e[1]) is not str or ', ''),
    ('len(e) != 3', 'len(e) != 2'), ('len(e) != 1', 'len(e) != 2'), ("e[0] not in ('add', 'remove', 'clear')", "e[0] not in ('add', 'remove')"),
    ('not e or ', ''), ("version conflict: expected %d, found %d' % (expected_version, len(events))", "version conflict: expected %d, found %d' % (len(events), expected_version)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    battery(mod)

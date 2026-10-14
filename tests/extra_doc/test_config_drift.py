import random
import pytest
from sugarcode.extra_doc.config_drift import config_drift as cd

T, V = TypeError, ValueError


class StrSub(str):
    pass


class IntSub(int):
    pass


class DictSub(dict):
    pass


class ListSub(list):
    pass


def oracle(layers, actual):
    keys = sorted({k for layer in layers for k in layer})
    merged, source, over = [], [], 0
    for k in keys:
        holders = [i for i, layer in enumerate(layers) if k in layer]      # every layer that sets this key
        win = holders[-1]                                                   # the last one wins
        over += len(holders) - 1
        merged.append((k, layers[win][k]))
        source.append((k, win))
    mk = dict(merged)
    missing = [k for k in keys if k not in actual]
    extra = sorted(set(actual) - set(keys))
    changed = [k for k in keys if k in actual and not (type(actual[k]) is type(mk[k]) and actual[k] == mk[k])]
    return {'merged': merged, 'source': source, 'overridden': over, 'missing': missing, 'extra': extra,
            'changed': changed, 'in_sync': not (missing or extra or changed)}


def test_hand_cases():
    r = cd([{'a': 1, 'b': 2}, {'b': 3, 'c.d': 'x'}], {'a': 1, 'b': 2, 'z': 0})
    assert r == {'merged': [('a', 1), ('b', 3), ('c.d', 'x')], 'source': [('a', 0), ('b', 1), ('c.d', 1)],
                 'overridden': 1, 'missing': ['c.d'], 'extra': ['z'], 'changed': ['b'], 'in_sync': False}
    assert cd([{}], {}) == {'merged': [], 'source': [], 'overridden': 0, 'missing': [], 'extra': [],
                            'changed': [], 'in_sync': True}
    assert cd([{'a': 1}], {'a': 1})['in_sync'] is True
    assert cd([{'a': 1}], {'a': '1'})['changed'] == ['a']            # "1" and 1 differ
    assert cd([{'a': '1'}], {'a': 1})['changed'] == ['a']
    assert cd([{'a': 'x'}, {'a': 'y'}, {'a': 'x'}], {})['overridden'] == 2
    assert cd([{'a': 1}, {'a': 1}], {'a': 1})['overridden'] == 1 and cd([{'a': 1}, {'a': 1}], {'a': 1})['source'] == [('a', 1)]
    assert cd([{'a': 0}], {'a': 0})['in_sync'] and cd([{'a': 0}], {'a': ''})['changed'] == ['a']
    assert cd([{'a': ''}], {'a': ''})['in_sync']
    assert cd([{'a.b': 1, 'a2': 2}], {})['merged'] == [('a.b', 1), ('a2', 2)]       # "a2" is not under "a"


def test_random_vs_independent_oracle():
    rnd = random.Random(613)
    keys = ['a', 'b', 'c.d', 'c.e', 'f', 'g.h.i', 'j2']
    vals = [0, 1, -1, 7, '', '1', 'x', 'hello world']
    for _ in range(500):
        layers = [{k: rnd.choice(vals) for k in rnd.sample(keys, rnd.randint(0, 5))} for _ in range(rnd.randint(1, 5))]
        actual = {k: rnd.choice(vals) for k in rnd.sample(keys + ['zz'], rnd.randint(0, 6))}
        assert cd(layers, actual) == oracle(layers, actual)
    layers, actual = [{'a': 1}, {'a': 2}], {'a': 2}
    cd(layers, actual)
    assert layers == [{'a': 1}, {'a': 2}] and actual == {'a': 2}


def test_limits_accepted():
    cd([{}] * 8, {})
    cd([{'k%d' % i: i for i in range(16)}], {})
    cd([{'k%d' % i: 0 for i in range(16)}, {'m%d' % i: 0 for i in range(16)}] * 4, {})
    cd([{'a': 1000000}, {'b': -1000000}], {})
    cd([{'a': 'x' * 32}], {})
    cd([{'a': ' ~'}], {})
    cd([{'a' * 16 + '.' + 'b' * 16 + '.' + 'c' * 16 + '.' + 'd' * 16: 1}], {})
    big = {'q%03d' % i: 0 for i in range(128)}
    cd([{'q%03d' % i: 0 for i in range(16)}], big)
    layers = [{'p%d_%d' % (j, i): 0 for i in range(16)} for j in range(8)]
    assert len(cd(layers, {})['merged']) == 128


def err(exc, msg, *a):
    with pytest.raises(exc) as e:
        cd(*a)
    assert str(e.value) == msg


def test_pins():
    for bad in (None, (), 'x', {}, DictSub(), ListSub([{}])):
        err(T, 'layers must be an exact list', bad, {})
    err(V, 'layer count must be between 1 and 8', [], {})
    err(V, 'layer count must be between 1 and 8', [{}] * 9, {})
    for bad in (None, [], (), DictSub()):
        err(T, 'layer 0: must be an exact dict', [bad], {})
        err(T, 'layer 1: must be an exact dict', [{}, bad], {})
        err(T, 'actual: must be an exact dict', [{}], bad)
    err(V, 'layer 0: at most 16 settings', [{'k%d' % i: 0 for i in range(17)}], {})
    err(V, 'actual: at most 128 settings', [{}], {'k%03d' % i: 0 for i in range(129)})
    for bad in (None, 5, b'a', StrSub('a')):
        err(T, 'layer 0: key must be an exact string', [{bad: 1}], {})
        err(T, 'actual: key must be an exact string', [{}], {bad: 1})
    for bad in ('', 'A', '1a', 'a.', '.a', 'a..b', 'a-b', 'a b', 'a\n', 'é', 'a.b.c.d.e', 'a' * 17, 'a.' + 'b' * 17, '_a', 'a.B'):
        err(V, 'layer 0: key must be 1 to 4 dotted lowercase identifiers', [{bad: 1}], {})
        err(V, 'actual: key must be 1 to 4 dotted lowercase identifiers', [{}], {bad: 1})
    for bad in (True, False, 1.0, None, b'x', [1], IntSub(1), StrSub('x')):
        err(T, 'layer 0: value must be an exact int or str', [{'a': bad}], {})
        err(T, 'actual: value must be an exact int or str', [{}], {'a': bad})
    for bad in (1000001, -1000001):
        err(V, 'layer 0: int value must be between -1000000 and 1000000', [{'a': bad}], {})
        err(V, 'actual: int value must be between -1000000 and 1000000', [{}], {'a': bad})
    for bad in ('x' * 33, '\n', 'a\tb', '\x7f', 'é', '\x1f'):
        err(V, 'layer 0: string value must be at most 32 printable ASCII characters', [{'a': bad}], {})
        err(V, 'actual: string value must be at most 32 printable ASCII characters', [{}], {'a': bad})
    err(V, 'key conflicts with a longer key: a', [{'a': 1}, {'a.b': 2}], {})
    err(V, 'key conflicts with a longer key: a', [{'a.b': 1, 'a': 1}], {})
    err(V, 'key conflicts with a longer key: a.b', [{'a.b': 1, 'a.b.c': 1}], {})
    err(V, 'key conflicts with a longer key: a', [{'z': 1, 'a': 1, 'a.b': 1, 'b': 1, 'b.c': 1}], {})


def test_order_of_checks():
    err(T, 'layers must be an exact list', 'x', 'y')
    err(V, 'layer count must be between 1 and 8', [], 'y')
    err(V, 'layer count must be between 1 and 8', [None] * 9, 'y')
    err(T, 'layer 0: must be an exact dict', [None, {'A': 1}], 'y')
    err(V, 'layer 0: at most 16 settings', [{'A%d' % i: 0 for i in range(17)}], 'y')
    err(T, 'layer 0: key must be an exact string', [{5: 'x', 'A': 1}], 'y')
    err(V, 'layer 0: key must be 1 to 4 dotted lowercase identifiers', [{'A': 'x', 5: 1}], 'y')
    err(T, 'layer 0: value must be an exact int or str', [{'a': 1.5, 'b': 10 ** 9}], 'y')
    err(V, 'layer 0: int value must be between -1000000 and 1000000', [{'a': 10 ** 9, 'b': 1.5}], 'y')
    err(V, 'layer 0: key must be 1 to 4 dotted lowercase identifiers', [{'A': 1}, {5: 1}], 'y')
    err(T, 'layer 1: key must be an exact string', [{'a': 1}, {5: 1}], 'y')
    err(T, 'actual: must be an exact dict', [{'a': 1}], 'y')
    err(V, 'actual: key must be 1 to 4 dotted lowercase identifiers', [{'a': 1}], {'A': 1})
    err(V, 'layer 0: key must be 1 to 4 dotted lowercase identifiers', [{'A': 1}], 'y')
    layers = [{'p%d_%d' % (j, i): 0 for i in range(16)} for j in range(8)]
    err(V, 'actual: key must be 1 to 4 dotted lowercase identifiers', [{'a': 1}, {'a.b': 1}], {'A': 1})

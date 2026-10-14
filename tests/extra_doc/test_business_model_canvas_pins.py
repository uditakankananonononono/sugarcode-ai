"""Row 364 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import random

import pytest

from sugarcode.extra_doc.business_model_canvas import BLOCKS, map_canvas as mc


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


def refuses(error, msg, blocks, links=(), *a):
    with pytest.raises(error) as e:
        mc(blocks, links, *a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'inputs must be lists or tuples'
NINE = 'exactly nine blocks required'
LN = 'at most 128 links allowed'
ENT8 = 'blocks must contain at most eight entries'
PAIR = 'links must be pairs'
STR = 'entries must be strings of length 1 through 64'
IDX = 'links must contain nonbool valid distinct entry indices'
UNI = 'links must be unique'


def mk(*filled):
    b = [[] for _ in range(9)]
    for i, row in filled:
        b[i] = row
    return b


def test_names():
    assert BLOCKS == ('partners', 'activities', 'resources', 'value_propositions', 'relationships',
                      'channels', 'segments', 'costs', 'revenues')


def closure(n, edges):
    out = []
    for s in range(n):
        seen, todo = set(), [s]
        while todo:
            x = todo.pop()
            for a, b in edges:
                if a == x and b not in seen:
                    seen.add(b)
                    todo.append(b)
        seen.discard(s)
        out.append(sorted(seen))
    return out


def test_literals():
    r = mc(mk((0, ['a']), (3, ['b', 'c']), (8, ['d'])), [[0, 1], [1, 3], [3, 1]])
    assert r == {'nodes': [{'block': 'partners', 'entry': 'a'}, {'block': 'value_propositions', 'entry': 'b'},
                           {'block': 'value_propositions', 'entry': 'c'}, {'block': 'revenues', 'entry': 'd'}],
                 'links': [[0, 1], [1, 3], [3, 1]], 'reachable': [[1, 3], [3], [], [1]],
                 'isolated': [2], 'business_viability_validated': False}
    r = mc(mk(), [])
    assert r['nodes'] == [] and r['reachable'] == [] and r['isolated'] == []
    assert mc(mk((0, ['a', 'b'])), [(0, 1)])['links'] == [[0, 1]]
    assert mc(tuple(tuple(x) for x in mk((0, ['a', 'b']))), ((1, 0),))['reachable'] == [[], [0]]
    assert mc(mk((1, ['x']), (2, ['y'])), [])['isolated'] == [0, 1]
    assert mc(mk((0, ['a', 'b', 'c'])), [[0, 1], [1, 2], [2, 0]])['reachable'] == [[1, 2], [0, 2], [0, 1]]
    assert mc(mk((0, ['a', 'b', 'c'])), [[2, 1], [1, 0]])['reachable'] == [[], [0], [0, 1]]


def test_random_oracle():
    rnd = random.Random(5)
    for _ in range(60):
        n = rnd.randint(1, 8)
        blocks = mk((rnd.randrange(9), [str(i) for i in range(n)]))
        pairs = [(a, b) for a in range(n) for b in range(n) if a != b]
        edges = rnd.sample(pairs, rnd.randint(0, min(len(pairs), 12))) if pairs else []
        r = mc(blocks, [list(e) for e in edges])
        used = {x for e in edges for x in e}
        assert r['reachable'] == closure(n, edges)
        assert r['isolated'] == [i for i in range(n) if i not in used]
        assert r['links'] == [list(e) for e in edges]


def test_caps_n_and_n_plus_1():
    full = [[str(j) for j in range(8)] for _ in range(9)]
    assert len(mc(full, [])['nodes']) == 72
    refuses(ValueError, ENT8, mk((8, ['a'] * 9)))
    refuses(ValueError, ENT8, [[], [], [], [], [], [], [], [], ['a'] * 8 + ['b']])
    refuses(ValueError, NINE, mk()[:8], [])
    refuses(ValueError, NINE, mk() + [[]], [])
    big = [[str(j) for j in range(8)] for _ in range(9)]
    edges = [[a, b] for a in range(16) for b in range(16) if a != b][:128]
    assert len(mc(big, edges)['links']) == 128
    refuses(ValueError, LN, big, edges + [[16, 17]])
    refuses(ValueError, LN, mk(), [[0, 1]] * 129)
    assert mc(mk((0, ['a' * 64])), [])['nodes'][0]['entry'] == 'a' * 64
    refuses(ValueError, STR, mk((0, ['a' * 65])))
    refuses(ValueError, STR, mk((0, ['a', ''])))
    refuses(ValueError, STR, mk((0, ['']), (1, ['b'])))
    refuses(ValueError, IDX, mk((0, ['a', 'b'])), [[0, 2]])
    refuses(ValueError, IDX, mk((0, ['a', 'b'])), [[-1, 0]])
    refuses(ValueError, IDX, mk((0, ['a', 'b'])), [[0, -1]])
    refuses(ValueError, IDX, mk((0, ['a', 'b'])), [[2, 0]])
    refuses(ValueError, IDX, mk((0, ['a', 'b'])), [[0, 1], [1, 1]])
    refuses(ValueError, IDX, mk((0, ['a', 'b'])), [[0, 1], [0, 0]])
    refuses(ValueError, UNI, mk((0, ['a', 'b'])), [[0, 1], [0, 1]])
    refuses(ValueError, UNI, mk((0, ['a', 'b'])), [[0, 1], [1, 0], [0, 1]])
    assert mc(mk((0, ['a', 'b'])), [[0, 1], [1, 0]])['reachable'] == [[1], [0]]


def test_exact_types():
    refuses(TypeError, TY, L(mk()), [])
    refuses(TypeError, TY, mk(), L())
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, [])
        refuses(TypeError, TY, mk(), b)
    refuses(ValueError, ENT8, [L(), [], [], [], [], [], [], [], []])
    refuses(ValueError, ENT8, [[], [], [], [], [], [], [], [], 'ab'])
    refuses(ValueError, ENT8, [[], [], [], [], [], [], [], [], None])
    refuses(ValueError, PAIR, mk((0, ['a', 'b'])), [[0]])
    refuses(ValueError, PAIR, mk((0, ['a', 'b'])), [[0, 1, 1]])
    refuses(ValueError, PAIR, mk((0, ['a', 'b'])), [[0, 1], L([1, 0])])
    refuses(ValueError, PAIR, mk((0, ['a', 'b'])), [[0, 1], 'ab'])
    refuses(ValueError, PAIR, mk((0, ['a', 'b'])), [[0, 1], None])
    for b in (S('a'), 1, None, b'a', ['a']):
        refuses(ValueError, STR, mk((0, [b])))
        refuses(ValueError, STR, mk((0, ['a', b])))
        refuses(ValueError, STR, mk((0, ['a']), (5, [b])))
    for b in (True, False, 1.0, I(1), '1', None):
        refuses(ValueError, IDX, mk((0, ['a', 'b'])), [[b, 0]])
        refuses(ValueError, IDX, mk((0, ['a', 'b'])), [[0, b]])
        refuses(ValueError, IDX, mk((0, ['a', 'b'])), [[0, 1], [1, b]])
    r = mc(mk((0, ['a', 'b'])), [(0, 1)])
    assert type(r['links'][0]) is list and type(r['nodes']) is list
    blocks = mk((0, ['a', 'b']))
    r = mc(blocks, [[0, 1]])
    r['nodes'][0]['entry'] = 'z'
    assert blocks == mk((0, ['a', 'b']))


def test_check_order():
    refuses(TypeError, TY, 1, 2)
    refuses(ValueError, NINE, [], [[0, 0]] * 200)
    refuses(ValueError, LN, [[]] * 9, [5] * 129)
    refuses(ValueError, ENT8, [['a'] * 9] + [[]] * 8, [5])
    refuses(ValueError, PAIR, [[1]] + [[]] * 8, [5])
    refuses(ValueError, STR, [[1]] + [[]] * 8, [[0, 0]])
    refuses(ValueError, IDX, [['a', 'b']] + [[]] * 8, [[0, 0], [0, 0]])

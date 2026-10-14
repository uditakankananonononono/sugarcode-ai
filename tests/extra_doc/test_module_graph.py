import pytest
from fractions import Fraction as F
from sugarcode.extra_doc.module_graph import analyse_modules as f, NOT_CLAIMED

G = [('A', 100, ['B']), ('B', 50, ['C']), ('C', 50, ['A']), ('D', 200, ['A', 'B'])]


def test_oracle():
    r = f(G)
    assert [(m['fan_out'], m['fan_in'], m['line_share'], m['on_cycle']) for m in r['modules']] == [
        (1, 2, F(1, 4), True), (1, 2, F(1, 8), True), (1, 1, F(1, 8), True), (2, 0, F(1, 2), False)]
    assert r['cyclic_modules'] == ('A', 'B', 'C') and r['largest_module'] == 'D' and r['edge_count'] == 5
    assert r['design_validated'] is False and r['not_claimed'] == NOT_CLAIMED and len(NOT_CLAIMED) == 7


def test_long_cycle_and_acyclic():
    r = f([('a', 1, ['b']), ('b', 1, ['c']), ('c', 1, ['d']), ('d', 1, ['e']), ('e', 1, ['a']), ('x', 1, ['a'])])
    assert r['cyclic_modules'] == ('a', 'b', 'c', 'd', 'e')
    assert f([('a', 1, ['b']), ('b', 1, [])])['cyclic_modules'] == ()
    assert f([('p', 5, []), ('q', 5, ['p'])])['largest_module'] == 'p'


def test_ties_and_zero():
    assert f([('p', 5, []), ('q', 5, [])])['largest_module'] == 'p'
    r = f([('p', 0, [])])
    assert r['modules'][0]['line_share'] is None and r['edge_count'] == 0


def test_bounds_ok():
    f([(str(i), 10 ** 7, []) for i in range(12)])
    f([('x' * 40, 0, [])])


@pytest.mark.parametrize('bad,exc,msg', [
    ('x', TypeError, 'list or tuple'), ([], ValueError, 'between 1 and 12'),
    ([('a', 1, [])] * 13, ValueError, 'between 1 and 12'),
    ([('a', 1)], ValueError, 'each module'), ([['a', 1, [], 0]], ValueError, 'each module'),
    ([{'a': 1}], ValueError, 'each module'), (['abc'], ValueError, 'each module'),
    ([(1, 1, [])], TypeError, 'names must be str'), ([('', 1, [])], ValueError, '1 to 40'),
    ([('x' * 41, 1, [])], ValueError, '1 to 40'),
    ([('a', 1, []), ('a', 1, [])], ValueError, 'unique'),
    ([('a', True, [])], TypeError, 'nonbool'), ([('a', 1.0, [])], TypeError, 'nonbool'),
    ([('a', -1, [])], ValueError, '0 and 10000000'), ([('a', 10 ** 7 + 1, [])], ValueError, '0 and 10000000'),
    ([('a', 1, 'b')], TypeError, 'depends_on must be'), ([('a', 1, {'b'})], TypeError, 'depends_on must be'),
    ([('a', 1, [1]), ('b', 1, [])], TypeError, 'str names'),
    ([('a', 1, ['z'])], ValueError, 'too many'),
    ([('a', 1, ['z']), ('b', 1, [])], ValueError, 'unknown'),
    ([('a', 1, ['a']), ('b', 1, [])], ValueError, 'itself'),
    ([('a', 1, ['b', 'b']), ('b', 1, []), ('c', 1, [])], ValueError, 'repeat'),
])
def test_refusals(bad, exc, msg):
    with pytest.raises(exc, match=msg):
        f(bad)


def test_cap_before_scan():
    class Boom:
        def __iter__(self):
            raise AssertionError('scanned')
    with pytest.raises(ValueError, match='between 1 and 12'):
        f([('a', 1, [])] * 13)
    with pytest.raises(ValueError, match='too many'):
        f([('a', 1, ['b'] * 10 ** 6), ('b', 1, [])])


def test_validate_before_use_no_mutation():
    deps = ['B']
    mods = [('A', 1, deps), ('B', 1, [])]
    f(mods)
    assert deps == ['B'] and mods[0][2] == ['B']

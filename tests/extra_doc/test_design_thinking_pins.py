"""Row 353 tests-only hardening: container, str and number subclass pins at every slot, non-first positions, exact messages."""
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc.design_thinking import cover_needs as cn


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


class Fr(F):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        cn(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'needs and ideas must be lists or tuples'
IDEA = 'each idea must be (id, covered_needs, cost)'
COV = 'covered needs must be a list or tuple of at most 8 ids'
IDT = 'ids must be str'
NUM = 'cost must be nonbool int or Fraction'
OK = [('i', ['a'], 1)]


def test_container_subclasses_refused():
    refuses(TypeError, TY, L(['a']), OK)
    refuses(TypeError, TY, T(('a',)), OK)
    refuses(TypeError, TY, ['a'], L(OK))
    refuses(TypeError, TY, ['a'], T(OK))
    for bad in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, bad, OK)
        refuses(TypeError, TY, ['a'], bad)
    refuses(ValueError, IDEA, ['a'], [L(['i', ['a'], 1])])
    refuses(ValueError, IDEA, ['a'], [('i', ['a'], 1), T(('j', ['a'], 1))])
    refuses(ValueError, IDEA, ['a'], [('i', ['a'], 1), ('j', ['a'])])
    refuses(ValueError, IDEA, ['a'], [('i', ['a'], 1), 'abc'])
    refuses(ValueError, COV, ['a'], [('i', L(['a']), 1)])
    refuses(ValueError, COV, ['a'], [('i', ['a'], 1), ('j', T(('a',)), 1)])
    refuses(ValueError, COV, ['a'], [('i', ['a'], 1), ('j', 'a', 1)])
    refuses(ValueError, COV, ['a'], [('i', ['a'], 1), ('j', ['a'] * 9, 1)])
    assert cn(['a'], [('i', ['a'] * 8, 1)])['chosen_indices'] == [0]


def test_str_subclass_and_non_str_ids_refused_at_every_slot():
    for bad in (S('a'), b'a', 5, None, True, ['a']):
        refuses(TypeError, IDT, [bad], OK)
        refuses(TypeError, IDT, ['a', bad], OK)
        refuses(TypeError, IDT, ['a'], [(bad, ['a'], 1)])
        refuses(TypeError, IDT, ['a'], [('i', ['a'], 1), (bad, ['a'], 1)])
        refuses(TypeError, IDT, ['a'], [('i', [bad], 1)])
        refuses(TypeError, IDT, ['a', 'b'], [('i', ['a'], 1), ('j', ['a', bad], 1)])


def test_number_subclasses_bool_and_float_refused_non_first():
    for bad in (I(1), Fr(1, 2), True, False, 1.0, '1', None):
        refuses(TypeError, NUM, ['a'], [('i', ['a'], bad)])
        refuses(TypeError, NUM, ['a'], [('i', ['a'], 1), ('j', ['a'], bad)])
    refuses(ValueError, 'cost must fit 32 bits', ['a'], [('i', ['a'], 1), ('j', ['a'], 2 ** 32)])
    refuses(ValueError, 'cost must fit 32 bits', ['a'], [('i', ['a'], F(1, 2 ** 32))])
    refuses(ValueError, 'cost must fit 32 bits', ['a'], [('i', ['a'], F(2 ** 32, 3))])
    assert cn(['a'], [('i', ['a'], 2 ** 32 - 1)])['cost'] == 2 ** 32 - 1
    assert cn(['a'], [('i', ['a'], F(1, 2 ** 32 - 1))])['cost'] == F(1, 2 ** 32 - 1)
    refuses(ValueError, 'cost must be nonnegative', ['a'], [('i', ['a'], 1), ('j', ['a'], -1)])
    refuses(ValueError, 'cost must be nonnegative', ['a'], [('i', ['a'], F(-1, 2))])


def test_id_length_bounds_at_n_and_n_plus_1_in_every_position():
    m = 'ids must be 1 to 40 characters'
    long_ = 'x' * 40
    assert cn([long_], [(long_, [long_], 0)])['chosen_ideas'] == [long_]
    for bad in ('', 'x' * 41):
        refuses(ValueError, m, [bad], OK)
        refuses(ValueError, m, ['a', bad], OK)
        refuses(ValueError, m, ['a'], [(bad, ['a'], 1)])
        refuses(ValueError, m, ['a'], [('i', [bad], 1)])
        refuses(ValueError, m, ['a', 'b'], [('i', ['a'], 1), ('j', ['a', bad], 1)])


def test_cap_counts_and_uniqueness_and_membership():
    refuses(ValueError, 'need count must be between 1 and 8', [], OK)
    refuses(ValueError, 'need count must be between 1 and 8', list('abcdefghi'), OK)
    refuses(ValueError, 'idea count must be between 1 and 10', ['a'], [])
    refuses(ValueError, 'idea count must be between 1 and 10', ['a'], [(str(i), ['a'], 1) for i in range(11)])
    assert cn(['a'], [(str(i), ['a'], 1) for i in range(10)])['chosen_indices'] == [0]
    r = cn(list('abcdefgh'), [(str(i), [list('abcdefgh')[i]], 1) for i in range(8)])
    assert r['chosen_indices'] == list(range(8)) and r['cost'] == 8
    refuses(ValueError, 'need ids must be unique', ['a', 'a'], OK)
    refuses(ValueError, 'idea ids must be unique', ['a'], [('i', ['a'], 1), ('i', ['a'], 1)])
    refuses(ValueError, 'ideas may only cover listed needs', ['a'], [('i', ['a'], 1), ('j', ['z'], 1)])
    refuses(ValueError, 'no set of ideas covers every need', ['a', 'b'], OK)


def test_tie_breaks_and_result_literal():
    r = cn(['a', 'b'], [('x', ['a'], 1), ('y', ['b'], 1), ('z', ['a', 'b'], 2)])
    assert r['chosen_indices'] == [2] and r['cost'] == 2                      # equal cost: fewer ideas
    assert cn(['a'], [('x', ['a'], 1), ('y', ['a'], 1)])['chosen_ideas'] == ['x']
    r = cn(['a'], [('x', ['a'], F(1, 2)), ('y', ['a'], 0)])
    assert r['chosen_ideas'] == ['y'] and r['coverage'] == {'a': ['y']} and type(r['cost']) is F
    assert r['user_research_validated'] is False
    assert cn(('a',), (('x', ('a',), 1),)) == cn(['a'], [['x', ['a'], 1]])

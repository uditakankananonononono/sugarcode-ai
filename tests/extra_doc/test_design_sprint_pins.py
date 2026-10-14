"""Row 354 tests-only hardening: container, str and number subclass pins, caps at N and N+1, exact messages."""
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc.design_sprint import plan_sprint as ps


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
        ps(*a)
    assert type(e.value) is error and str(e.value) == msg


NUM = 'values must be nonbool int or Fraction'
FEAT = 'each feature must be (id, value, hours)'
OK = [('a', 1, 1)]


def test_container_subclasses_and_non_containers_refused():
    refuses(TypeError, 'features must be a list or tuple', L(OK), 1)
    refuses(TypeError, 'features must be a list or tuple', T(tuple(OK)), 1)
    for bad in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, 'features must be a list or tuple', bad, 1)
    refuses(ValueError, FEAT, [L(['a', 1, 1])], 1)
    refuses(ValueError, FEAT, OK + [T(('b', 1, 1))], 1)
    refuses(ValueError, FEAT, OK + [('b', 1)], 1)
    refuses(ValueError, FEAT, OK + ['abc'], 1)


def test_ids_str_only_and_length_bounds():
    for bad in (S('a'), b'a', 5, None, True):
        refuses(TypeError, 'feature ids must be str', [(bad, 1, 1)], 1)
        refuses(TypeError, 'feature ids must be str', OK + [(bad, 1, 1)], 1)
    m = 'feature ids must be 1 to 40 characters'
    assert ps([('x' * 40, 1, 1)], 1)['chosen'] == ['x' * 40]
    for bad in ('', 'x' * 41):
        refuses(ValueError, m, [(bad, 1, 1)], 1)
        refuses(ValueError, m, OK + [(bad, 1, 1)], 1)
    refuses(ValueError, 'feature ids must be unique', OK + [('a', 2, 2)], 1)


def test_number_slots_subclass_bool_float_and_non_first():
    for bad in (I(1), Fr(1, 2), True, False, 1.0, '1', None):
        refuses(TypeError, NUM, [('a', bad, 1)], 1)
        refuses(TypeError, NUM, [('a', 1, bad)], 1)
        refuses(TypeError, NUM, OK + [('b', bad, 1)], 1)
        refuses(TypeError, NUM, OK + [('b', 1, bad)], 1)
        refuses(TypeError, NUM, OK, bad)
    for bad in (I(1), True, 1.0, '1', None, F(1)):
        refuses(TypeError, 'days must be nonbool int', OK, 1, bad)
    for bad in (0, 6, -1):
        refuses(ValueError, 'days must be between 1 and 5', OK, 1, bad)
    assert ps(OK, 1, 5)['capacity_hours'] == 5 and ps(OK, 1, 1)['capacity_hours'] == 1
    refuses(ValueError, 'hours per day must be positive', OK, 0)
    refuses(ValueError, 'hours per day must be positive', OK, -1)
    refuses(ValueError, 'values and hours must be nonnegative', [('a', -1, 1)], 1)
    refuses(ValueError, 'values and hours must be nonnegative', OK + [('b', 1, -1)], 1)
    for bad in (2 ** 32, F(2 ** 32, 3), F(1, 2 ** 32)):
        refuses(ValueError, 'values must fit 32 bits', [('a', bad, 1)], 1)
        refuses(ValueError, 'values must fit 32 bits', OK + [('b', 1, bad)], 1)
        refuses(ValueError, 'values must fit 32 bits', OK, bad)
    assert ps([('a', 2 ** 32 - 1, 0)], 1)['total_value'] == 2 ** 32 - 1


def test_count_cap_and_budget_boundary_and_ties():
    assert ps([(str(i), 1, 1) for i in range(12)], 1, 5)['chosen_indices'] == [0, 1, 2, 3, 4]
    refuses(ValueError, 'feature count must be between 1 and 12', [(str(i), 1, 1) for i in range(13)], 1)
    refuses(ValueError, 'feature count must be between 1 and 12', [], 1)
    assert ps([('a', 5, 3)], 3, 1)['chosen'] == ['a']                      # hours == capacity is inclusive
    r = ps([('a', 5, 3)], F(5, 2), 1)
    assert r['chosen'] == [] and r['deferred'] == ['a'] and r['spare_hours'] == F(5, 2)
    r = ps([('a', 3, 2), ('b', 3, 1), ('c', 3, 1)], 2, 1)
    assert r['chosen'] == ['b', 'c'] and r['total_value'] == 6               # same value: fewer hours first
    r = ps([('a', 3, 1), ('b', 3, 1)], 1, 1)
    assert r['chosen'] == ['a']                                              # full tie: lowest index
    r = ps([('a', 0, 0), ('b', 0, 0)], 1, 1)
    assert r['chosen'] == [] and r['deferred'] == ['a', 'b']                 # fewer features beats more at equal value/hours
    assert r['sprint_outcome_validated'] is False
    assert ps(tuple(OK), 1) == ps([['a', 1, 1]], 1)

"""Row 356 tests-only hardening: container and str subclass pins at every slot, caps at N and N+1, exact messages."""
import pytest

from sugarcode.extra_doc.critical_design import challenge_assumptions as ca


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        ca(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'assumptions and claims must be lists or tuples'
CL = 'each claim must be (id, assumption_ids)'
AI = 'assumption ids must be a list or tuple of at most 8 ids'
IDT = 'ids must be str'
IDL = 'ids must be 1 to 40 characters'
OK = [('c', ['a'])]


def test_container_subclasses_and_non_containers():
    refuses(TypeError, TY, L(['a']), OK)
    refuses(TypeError, TY, T(('a',)), OK)
    refuses(TypeError, TY, ['a'], L(OK))
    refuses(TypeError, TY, ['a'], T(tuple(OK)))
    for bad in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, bad, OK)
        refuses(TypeError, TY, ['a'], bad)
    refuses(ValueError, CL, ['a'], [L(['c', ['a']])])
    refuses(ValueError, CL, ['a'], OK + [T(('d', ['a']))])
    refuses(ValueError, CL, ['a'], OK + [('d',)])
    refuses(ValueError, CL, ['a'], OK + [('d', ['a'], 1)])
    refuses(ValueError, CL, ['a'], OK + ['ab'])
    refuses(ValueError, AI, ['a'], [('c', L(['a']))])
    refuses(ValueError, AI, ['a'], OK + [('d', T(('a',)))])
    refuses(ValueError, AI, ['a'], OK + [('d', 'a')])
    refuses(ValueError, AI, ['a'], OK + [('d', None)])


def test_str_subclass_and_non_str_ids_at_every_slot():
    for bad in (S('a'), b'a', 5, None, True, ['a']):
        refuses(TypeError, IDT, [bad], OK)
        refuses(TypeError, IDT, ['a', bad], OK)
        refuses(TypeError, IDT, ['a'], [(bad, ['a'])])
        refuses(TypeError, IDT, ['a'], OK + [(bad, ['a'])])
        refuses(TypeError, IDT, ['a'], [('c', [bad])])
        refuses(TypeError, IDT, ['a', 'b'], OK + [('d', ['a', bad])])


def test_length_bounds_and_caps_n_and_n_plus_1():
    x = 'x' * 40
    r = ca([x], [(x, [x])])
    assert r['ranking'] == [x] and r['falls_if_negated'] == {x: [x]}
    for bad in ('', 'x' * 41):
        refuses(ValueError, IDL, [bad], OK)
        refuses(ValueError, IDL, ['a', bad], OK)
        refuses(ValueError, IDL, ['a'], [(bad, ['a'])])
        refuses(ValueError, IDL, ['a'], [('c', [bad])])
        refuses(ValueError, IDL, ['a', 'b'], OK + [('d', ['a', bad])])
    names = list('abcdefgh')
    assert ca(names, [('c', names)])['most_critical'] == names
    assert ca(names, [('c', names)])['falls_if_negated']['h'] == ['c']
    refuses(ValueError, 'assumption count must be between 1 and 8', list('abcdefghi'), OK)
    refuses(ValueError, 'assumption count must be between 1 and 8', [], OK)
    refuses(ValueError, 'claim count must be between 1 and 10', ['a'], [])
    refuses(ValueError, 'claim count must be between 1 and 10', ['a'], [(str(i), []) for i in range(11)])
    assert ca(['a'], [(str(i), []) for i in range(10)])['unconditional_claims'] == [str(i) for i in range(10)]
    refuses(ValueError, AI, names, [('c', names + ['i'])])
    refuses(ValueError, AI, names, OK + [('d', list('abcdefghi'))])
    refuses(ValueError, 'assumption ids must be unique', ['a', 'a'], OK)
    refuses(ValueError, 'a claim may list each assumption once', ['a'], [('c', ['a', 'a'])])
    refuses(ValueError, 'a claim may list each assumption once', ['a'], OK + [('d', ['a', 'a'])])
    refuses(ValueError, 'claim ids must be unique', ['a'], [('c', []), ('c', [])])
    refuses(ValueError, 'claims may only depend on listed assumptions', ['a'], OK + [('d', ['z'])])


def test_exact_results_ranking_and_ties():
    r = ca(['a', 'b', 'c'], [('x', ['a', 'b']), ('y', ['b']), ('z', []), ('w', ['b', 'c'])])
    assert r == {'falls_if_negated': {'a': ['x'], 'b': ['x', 'y', 'w'], 'c': ['w']}, 'ranking': ['b', 'a', 'c'],
                 'most_critical': ['b'], 'unused_assumptions': [], 'unconditional_claims': ['z'],
                 'assumptions_validated': False, 'not_claimed': r['not_claimed']}
    r = ca(['a', 'b', 'c'], [('x', ['c']), ('y', ['b'])])
    assert r['ranking'] == ['b', 'c', 'a'] and r['most_critical'] == ['b', 'c'] and r['unused_assumptions'] == ['a']
    r = ca(['a', 'b'], [('x', [])])
    assert r['most_critical'] == [] and r['unused_assumptions'] == ['a', 'b'] and r['ranking'] == ['a', 'b']
    assert r['falls_if_negated'] == {'a': [], 'b': []}
    assert ca(('a',), (('c', ('a',)),)) == ca(['a'], [['c', ['a']]])
    assert ca(['b', 'a'], [('x', ['a'])])['ranking'] == ['a', 'b']

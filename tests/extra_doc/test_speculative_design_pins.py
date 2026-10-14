"""Row 355 tests-only hardening: container and str subclass pins at every slot, caps at N and N+1, exact messages."""
import pytest

from sugarcode.extra_doc.speculative_design import explore_futures as ef


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        ef(*a)
    assert type(e.value) is error and str(e.value) == msg


AX = [('e', ['lo', 'hi']), ('w', ['a', 'b'])]
NM = 'names and values must be str'


def test_container_subclasses_and_non_containers():
    refuses(TypeError, 'axes must be a list or tuple', L(AX))
    refuses(TypeError, 'axes must be a list or tuple', T(tuple(AX)))
    refuses(TypeError, 'forbidden_pairs must be a list or tuple', AX, L([]))
    refuses(TypeError, 'forbidden_pairs must be a list or tuple', AX, 'ab')
    for bad in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, 'axes must be a list or tuple', bad)
    for bad in (None, {1}, 5, {1: 1}):
        refuses(TypeError, 'forbidden_pairs must be a list or tuple', AX, bad)
    refuses(ValueError, 'each axis must be (name, values)', [L(['e', ['a']])])
    refuses(ValueError, 'each axis must be (name, values)', AX + [T(('x', ['a']))])
    refuses(ValueError, 'each axis must be (name, values)', AX + [('x',)])
    refuses(ValueError, 'each axis must be (name, values)', AX + ['ab'])
    m = 'each axis must have between 1 and 4 values'
    refuses(ValueError, m, [('e', L(['a']))])
    refuses(ValueError, m, AX + [('x', T(('a',)))])
    refuses(ValueError, m, AX + [('x', 'abc')])
    refuses(ValueError, m, [('e', [])])
    refuses(ValueError, m, [('e', list('abcde'))])
    assert ef([('e', list('abcd'))])['consistent_count'] == 4
    pm = 'each forbidden pair must contain two (axis, value) choices'
    refuses(ValueError, pm, AX, [L([('e', 'lo'), ('w', 'a')])])
    refuses(ValueError, pm, AX, [(('e', 'lo'),)])
    refuses(ValueError, pm, AX, [[('e', 'lo'), ('w', 'a'), ('e', 'hi')]])
    refuses(ValueError, pm, AX, [[('e', 'lo'), ('w', 'a')], 'ab'])
    cm = 'each choice must be (axis, value)'
    refuses(ValueError, cm, AX, [[L(['e', 'lo']), ('w', 'a')]])
    refuses(ValueError, cm, AX, [[('e', 'lo'), T(('w',))]])
    refuses(ValueError, cm, AX, [[('e', 'lo'), ['w', 'a', 'x']]])
    refuses(ValueError, cm, AX, [[('e', 'lo'), 'wa']])


def test_str_subclass_and_non_str_names_at_every_slot():
    for bad in (S('a'), b'a', 5, None, True, ['a']):
        refuses(TypeError, NM, [(bad, ['a'])])
        refuses(TypeError, NM, AX + [(bad, ['a'])])
        refuses(TypeError, NM, [('e', [bad])])
        refuses(TypeError, NM, [('e', ['a', bad])])
        refuses(TypeError, NM, AX, [[(bad, 'lo'), ('w', 'a')]])
        refuses(TypeError, NM, AX, [[('e', bad), ('w', 'a')]])
        refuses(TypeError, NM, AX, [[('e', 'lo'), (bad, 'a')]])
        refuses(TypeError, NM, AX, [[('e', 'lo'), ('w', bad)]])
        refuses(TypeError, NM, AX, [[('e', 'lo'), ('w', 'a')], [('e', 'hi'), ('w', bad)]])


def test_length_bounds_and_caps_n_and_n_plus_1():
    m = 'names and values must be 1 to 40 characters'
    assert ef([('x' * 40, ['y' * 40])])['scenarios'] == [{'x' * 40: 'y' * 40}]
    for bad in ('', 'x' * 41):
        refuses(ValueError, m, [(bad, ['a'])])
        refuses(ValueError, m, [('e', [bad])])
        refuses(ValueError, m, AX, [[(bad, 'lo'), ('w', 'a')]])
        refuses(ValueError, m, AX, [[('e', 'lo'), ('w', bad)]])
    refuses(ValueError, 'axis count must be between 1 and 4', [])
    refuses(ValueError, 'axis count must be between 1 and 4', [(c, ['a']) for c in 'abcde'])
    r = ef([(c, list('wxyz')) for c in 'abcd'])
    assert r['candidate_count'] == 256 and r['consistent_count'] == 256
    pair = [('e', 'lo'), ('w', 'a')]
    assert ef(AX, [pair] * 16)['excluded_count'] == 1
    refuses(ValueError, 'at most 16 forbidden pairs', AX, [pair] * 17)
    refuses(ValueError, 'axis names must be unique', [('e', ['a']), ('e', ['b'])])
    refuses(ValueError, 'values within an axis must be unique', [('e', ['a', 'a'])])
    refuses(ValueError, 'values within an axis must be unique', AX + [('x', ['a', 'b', 'a'])])
    refuses(ValueError, 'forbidden pairs may only use listed axes and values', AX, [[('e', 'lo'), ('zz', 'a')]])
    refuses(ValueError, 'forbidden pairs may only use listed axes and values', AX, [[('e', 'lo'), ('w', 'zz')]])
    refuses(ValueError, 'a forbidden pair must name two different axes', AX, [[('e', 'lo'), ('e', 'hi')]])


def test_exact_results_usage_and_order():
    r = ef(AX, [[('e', 'lo'), ('w', 'a')]])
    assert r['scenarios'] == [{'e': 'lo', 'w': 'b'}, {'e': 'hi', 'w': 'a'}, {'e': 'hi', 'w': 'b'}]
    assert r['consistent_count'] == 3 and r['candidate_count'] == 4 and r['excluded_count'] == 1
    assert r['value_usage'] == {'e': {'lo': 1, 'hi': 2}, 'w': {'a': 1, 'b': 2}} and r['forecast_validated'] is False
    assert ef(AX, [[('w', 'a'), ('e', 'lo')]]) == r                                  # pair order is irrelevant
    assert ef(tuple(AX), ()) == ef([['e', ['lo', 'hi']], ['w', ['a', 'b']]])
    r = ef([('e', ['lo'])], [])
    assert r['scenarios'] == [{'e': 'lo'}]
    r = ef(AX, [[('e', 'lo'), ('w', 'a')], [('e', 'lo'), ('w', 'b')], [('e', 'hi'), ('w', 'a')], [('e', 'hi'), ('w', 'b')]])
    assert r['scenarios'] == [] and r['value_usage'] == {'e': {'lo': 0, 'hi': 0}, 'w': {'a': 0, 'b': 0}}

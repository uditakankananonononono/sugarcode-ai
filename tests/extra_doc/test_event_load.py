import pytest
from fractions import Fraction as F
from sugarcode.extra_doc.event_load import event_load as f, NOT_CLAIMED

E = [('e1', 100), ('e2', 50), ('e3', 7)]
C = [('c1', ['e1', 'e2'], 10, 2), ('c2', ['e1'], 40, 2), ('c3', [], 5, 1)]


def test_oracle():
    r = f(E, C)
    assert [(c['rate'], c['utilisation'], c['overloaded']) for c in r['consumers']] == [
        (150, F(3, 4), False), (100, F(2), True), (0, F(0), False)]
    assert r['overloaded'] == ('c2',) and r['unhandled_events'] == ('e3',) and r['most_utilised'] == 'c2'
    assert r['design_validated'] is False and r['not_claimed'] == NOT_CLAIMED and len(NOT_CLAIMED) == 6


def test_boundary_one_overloaded_and_just_under():
    assert f([('e', 100)], [('c', ['e'], 10, 1)])['overloaded'] == ('c',)
    r = f([('e', 99)], [('c', ['e'], 10, 1)])
    assert r['overloaded'] == () and r['consumers'][0]['utilisation'] == F(99, 100)


def test_zero_rate_ok():
    r = f([('e', 0)], [('c', ['e'], 1, 1)])
    assert r['consumers'][0]['rate'] == 0 and r['consumers'][0]['utilisation'] == 0


def test_tie_first_and_handled():
    r = f([('e', 10)], [('a', ['e'], 1, 1), ('b', ['e'], 1, 1)])
    assert r['most_utilised'] == 'a' and r['unhandled_events'] == ()


def test_long_names_ok():
    n = 'n' * 40
    r = f([(n, 1)], [('c' * 40, [n], 1, 1)])
    assert r['consumers'][0]['rate'] == 1 and r['most_utilised'] == 'c' * 40


def test_bounds_ok():
    f([(str(i), 10 ** 6) for i in range(12)], [(str(i), [], 10000, 1000) for i in range(10)])
    assert f([('e', 10 ** 6)], [('c', ['e'], 10000, 1000)])['consumers'][0]['utilisation'] == F(10 ** 10, 10 ** 6)


@pytest.mark.parametrize('ev,co,exc,msg', [
    ('x', C, TypeError, 'list or tuple'), (E, 'x', TypeError, 'list or tuple'),
    ([], C, ValueError, 'event count'), ([('e', 1)] * 13, C, ValueError, 'event count'),
    (E, [], ValueError, 'consumer count'), (E, C[:1] * 11, ValueError, 'consumer count'),
    ([('e',)], C, ValueError, 'each event'), (['ab'], C, ValueError, 'each event'), ([{'e': 1}], C, ValueError, 'each event'),
    ([(1, 1)], C, TypeError, 'names must be str'), ([('', 1)], C, ValueError, '1 to 40'),
    ([('e' * 41, 1)], C, ValueError, '1 to 40'),
    ([('e', True)], C, TypeError, 'rate'), ([('e', 1.0)], C, TypeError, 'rate'),
    ([('e', -1)], C, ValueError, 'rate'), ([('e', 10 ** 6 + 1)], C, ValueError, 'rate'),
    ([('e', 1), ('e', 2)], C, ValueError, 'event names must be unique'),
    ([('e', 1)], [('c', [], 1)], ValueError, 'each consumer'), ([('e', 1)], ['abcd'], ValueError, 'each consumer'),
    ([('e', 1)], [{'a': 1}], ValueError, 'each consumer'),
    ([('e', 1)], [(1, [], 1, 1)], TypeError, 'names must be str'),
    ([('e', 1)], [('c', 'e', 1, 1)], TypeError, 'subscribes must be'),
    ([('e', 1)], [('c', ['e', 'e'], 1, 1)], ValueError, 'more names'),
    ([('e', 1), ('f', 1)], [('c', ['e', 'e'], 1, 1)], ValueError, 'repeat'),
    ([('e', 1)], [('c', [1], 1, 1)], TypeError, 'str names'),
    ([('e', 1)], [('c', ['z'], 1, 1)], ValueError, 'unknown'),
    ([('e', 1)], [('c', [], True, 1)], TypeError, 'nonbool'), ([('e', 1)], [('c', [], 1, 1.0)], TypeError, 'nonbool'),
    ([('e', 1)], [('c', [], 1, True)], TypeError, 'nonbool'),
    ([('e', 1)], [('c', [], 0, 1)], ValueError, 'service_ms'), ([('e', 1)], [('c', [], 10001, 1)], ValueError, 'service_ms'),
    ([('e', 1)], [('c', [], 1, 0)], ValueError, 'workers'), ([('e', 1)], [('c', [], 1, 1001)], ValueError, 'workers'),
    ([('e', 1)], [('c', [], 1, 1), ('c', [], 1, 1)], ValueError, 'consumer names must be unique'),
])
def test_refusals(ev, co, exc, msg):
    with pytest.raises(exc, match=msg):
        f(ev, co)


def test_cap_before_scan():
    with pytest.raises(ValueError, match='more names'):
        f([('e', 1)], [('c', ['e'] * 10 ** 6, 1, 1)])

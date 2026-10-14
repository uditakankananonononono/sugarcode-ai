import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import antenna_length1603 as m03
from sugarcode.extra_doc import rf_budget1604 as m04


def test_audpin_scope_1603():
    assert m03.SCOPE == 'caller ideal wavelength-length arithmetic only; no antenna performance claims'


def test_audpin_behavior_1603():
    r = m03.lengths([3, 1], 12, 1, 2)
    assert r == {'lengths': ((1, F(12), F(6)), (3, F(4), F(2))), 'scope': m03.SCOPE}
    # sorted by frequency, not input order
    assert [t[0] for t in m03.lengths([9, 2, 7], 10, 1, 4)['lengths']] == [2, 7, 9]
    # duplicate frequencies refused
    try:
        m03.lengths([5, 5], 10, 1, 2); assert False
    except ValueError as e:
        assert 'unique' in str(e)
    # bool refused (type is not int)
    for bad_args in [([True], 10, 1, 2), ([1], True, 1, 2), ([1], 10, True, 2), ([1], 10, 1, True)]:
        try:
            m03.lengths(*bad_args); assert False
        except ValueError:
            pass
    # scale bounds
    for bad in (0, 1001, '2', 1.5):
        try:
            m03.lengths([1], 10, bad, 2); assert False
        except ValueError:
            pass
        try:
            m03.lengths([1], 10, 1, bad); assert False
        except ValueError:
            pass


def test_audpin_scope_1604():
    assert m04.SCOPE == 'caller signed additive link budget only; no RF propagation or compliance claims'


def test_audpin_behavior_1604():
    r = m04.budget([('a', 2), ('b', -1)], 1, 3)
    assert r == {'stages': (('a', F(3)), ('b', F(2))), 'final': F(2),
                 'margin': F(-1), 'within': False, 'scope': m04.SCOPE}
    # empty rows allowed: final == initial
    r2 = m04.budget([], 5, 5)
    assert r2['stages'] == () and r2['final'] == F(5) and r2['within'] is True
    # caller order preserved, not sorted
    assert [t[0] for t in m04.budget([('z', 1), ('a', 1)], 0, 0)['stages']] == ['z', 'a']
    # inclusive within at equality
    assert m04.budget([('a', 1)], 1, 2)['within'] is True
    # float spelling decimal-exact: 0.1 + 0.2 = 3/10 exactly
    assert m04.budget([('a', 0.1), ('b', 0.2)], 0, 0)['final'] == F(3, 10)
    try:
        m04.budget([('a', 1), ('a', 2)], 0, 0); assert False
    except ValueError as e:
        assert 'unique' in str(e)


def test_audpin_shipped_suite_1603_1604():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1603_1604.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1603_1604.py')
    spec = importlib.util.spec_from_file_location('shipped_1603_1604', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

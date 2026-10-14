import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import desal_partition1655 as m55, conservation_periods1656 as m56

def test_audpin_scope_1655():
    assert m55.SCOPE == 'caller feed-product partition arithmetic only; no desalination performance claims'
    assert "PARTIAL: caller feed/product quantity partition only" in m55.__doc__

def test_audpin_scope_1656():
    assert m56.SCOPE == 'caller baseline-current-period arithmetic only; no verified water conservation claims'
    assert "PARTIAL: caller baseline/current/period savings arithmetic only" in m56.__doc__

def test_audpin_behavior_1655():
    r = m55.partition([('a',10,4),('b',0,0)])
    assert r == {'partition': (('a',6,F(2,5)),('b',0,None)), 'feed': 10,
                 'product': 4, 'remainder': 6, 'recovery_fraction': F(2,5), 'scope': m55.SCOPE}
    # all-zero feed: aggregate None
    assert m55.partition([('z',0,0)])['recovery_fraction'] is None
    try:
        m55.partition([('x',3,4)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1656():
    # repeated labels aggregate baseline*periods and current*periods
    r = m56.savings([('a',10,4,2),('a',1,1,3),('b',5,9,1)])
    assert r == {'savings': (('a',23,11,12),('b',5,9,-4)), 'total_savings': 8,
                 'negative': ('b',), 'scope': m56.SCOPE}
    # negative savings not clamped, zero not negative
    assert m56.savings([('x',3,3,2)])['negative'] == ()
    try:
        m56.savings([('x',1,1,0)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1655_1656():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1655_1656.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1655_1656.py')
    spec = importlib.util.spec_from_file_location('shipped_1655_1656', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

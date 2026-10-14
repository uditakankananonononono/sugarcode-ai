import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import reforest_cohorts1637 as m37, biochar_yield1638 as m38

def test_audpin_scope_1637():
    assert m37.SCOPE == 'caller cohort count ledger only; no ecological recovery or carbon claims'
    assert "PARTIAL: caller cohort surviving-count ledger only" in m37.__doc__

def test_audpin_scope_1638():
    assert m38.SCOPE == 'caller feedstock-product mass ratios only; no biochar stability or soil claims'
    assert "PARTIAL: caller feedstock/product mass-ratio arithmetic only" in m38.__doc__

def test_audpin_behavior_1637():
    r = m37.cohorts([('b',10,4),('a',0,0)])
    assert r == {'cohorts': (('a',0,None),('b',6,F(2,5))), 'initial_total': 10,
                 'surviving_total': 4, 'lost_total': 6, 'fraction': F(2,5), 'scope': m37.SCOPE}
    # all-initial-zero: overall fraction None
    assert m37.cohorts([('x',0,0)])['fraction'] is None
    # full survival: lost 0
    assert m37.cohorts([('x',7,7)])['lost_total'] == 0
    try:
        m37.cohorts([('x',3,4)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1638():
    r = m38.yield_ratio([('x',10,3),('y',5,5)])
    assert r == {'yields': (('x',F(3,10),7),('y',F(1),0)), 'feed_total': 15,
                 'product_total': 8, 'aggregate_ratio': F(8,15), 'scope': m38.SCOPE}
    # zero product
    assert m38.yield_ratio([('a',4,0)])['aggregate_ratio'] == 0
    try:
        m38.yield_ratio([('a',0,0)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1637_1638():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1637_1638.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1637_1638.py')
    spec = importlib.util.spec_from_file_location('shipped_1637_1638', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

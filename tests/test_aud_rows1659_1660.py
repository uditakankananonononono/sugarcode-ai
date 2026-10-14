import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import watershed_weights1659 as m59, water_allocations1660 as m60

def test_audpin_scope_1659():
    assert m59.SCOPE == 'caller area-weight ledger only; no watershed or runoff prediction'
    assert "PARTIAL: caller area/weight ledger only" in m59.__doc__

def test_audpin_scope_1660():
    assert m60.SCOPE == 'caller supply-demand allocation ledger only; no water resources planning advice'
    assert "PARTIAL: caller supply/demand allocation ledger only" in m60.__doc__

def test_audpin_behavior_1659():
    r = m59.weights([('a',10,1,2),('b',0,1,1)])
    assert r == {'weighted_areas': (('a',F(5)),('b',F(0))), 'area': 10,
                 'weighted_total': F(5), 'weighted_average': F(1,2), 'scope': m59.SCOPE}
    # all-zero area: average None
    assert m59.weights([('z',0,1,2)])['weighted_average'] is None
    try:
        m59.weights([('x',1,3,2)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1660():
    r = m60.allocations([('a',10,4),('b',3,9)])
    assert r == {'allocations': (('a',4,0,6),('b',3,6,0)), 'total_unmet': 6,
                 'total_unused': 6, 'unmet': ('b',), 'scope': m60.SCOPE}
    # exact match: neither unmet nor unused
    assert m60.allocations([('x',5,5)])['allocations'] == (('x',5,0,0),)
    assert m60.allocations([('x',5,5)])['unmet'] == ()
    try:
        m60.allocations([('x',-1,0)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1659_1660():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1659_1660.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1659_1660.py')
    spec = importlib.util.spec_from_file_location('shipped_1659_1660', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

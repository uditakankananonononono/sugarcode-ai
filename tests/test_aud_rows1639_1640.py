import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import soil_weighted1639 as m39, blue_area1640 as m40

def test_audpin_scope_1639():
    assert m39.SCOPE == 'caller weighted layer-value arithmetic only; no soil carbon stock or sequestration claims'
    assert "PARTIAL: caller weighted layer-value arithmetic only" in m39.__doc__

def test_audpin_scope_1640():
    assert m40.SCOPE == 'caller area-intensity products only; no coastal carbon stocks or credit claims'
    assert "PARTIAL: caller area/intensity product arithmetic only" in m40.__doc__

def test_audpin_behavior_1639():
    r = m39.layers([('a',2,10),('b',3,4)])
    assert r == {'weighted': (('a',20),('b',12)), 'weight_total': 5,
                 'weighted_total': 32, 'mean': F(32,5), 'scope': m39.SCOPE}
    # zero value allowed
    assert m39.layers([('a',5,0)])['mean'] == 0
    try:
        m39.layers([('a',0,5)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1640():
    r = m40.products([('x',10,1,2),('y',0,5,1)])
    assert r == {'products': (('x',F(5)),('y',F(0))), 'area_total': 10,
                 'product_total': F(5), 'weighted_intensity': F(1,2), 'scope': m40.SCOPE}
    # all-zero area: weighted_intensity None
    assert m40.products([('z',0,3,2)])['weighted_intensity'] is None
    try:
        m40.products([('a',1,1,0)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1639_1640():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1639_1640.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1639_1640.py')
    spec = importlib.util.spec_from_file_location('shipped_1639_1640', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

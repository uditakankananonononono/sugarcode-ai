import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import water_residual1653 as m53, wastewater_load1654 as m54

def test_audpin_scope_1653():
    assert m53.SCOPE == 'caller concentration-removal arithmetic only; no water safety claims'
    assert "PARTIAL: caller concentration/removal-fraction arithmetic only" in m53.__doc__

def test_audpin_scope_1654():
    assert m54.SCOPE == 'caller flow-concentration load ledger only; no wastewater compliance claims'
    assert "PARTIAL: caller flow/concentration load ledger only" in m54.__doc__

def test_audpin_behavior_1653():
    r = m53.residuals([('a',10,1,4),('b',0,1,1)])
    assert r == {'residuals': (('a',F(15,2),F(5,2)),('b',F(0),F(0))), 'total_residual': F(15,2),
                 'scope': m53.SCOPE}
    # full removal leaves zero
    assert m53.residuals([('x',7,1,1)])['total_residual'] == 0
    try:
        m53.residuals([('x',1,2,1)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1654():
    # repeated labels aggregate flow and flow*concentration
    r = m54.loads([('a',10,3),('a',2,5),('b',0,9)])
    assert r == {'loads': (('a',12,40),('b',0,0)), 'total_load': 40,
                 'zero_flow': ('b',), 'scope': m54.SCOPE}
    try:
        m54.loads([('x',-1,0)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1653_1654():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1653_1654.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1653_1654.py')
    spec = importlib.util.spec_from_file_location('shipped_1653_1654', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

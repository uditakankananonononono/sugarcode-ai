import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import waste_delta1647 as m47, recovery_ledger1648 as m48

def test_audpin_scope_1647():
    assert m47.SCOPE == 'caller baseline-current arithmetic only; no verified waste reduction claims'
    assert "PARTIAL: caller baseline/current waste arithmetic only" in m47.__doc__

def test_audpin_scope_1648():
    assert m48.SCOPE == 'caller input-recovered ledger only; no verified recycling claims'
    assert "PARTIAL: caller input/recovered quantity ledger only" in m48.__doc__

def test_audpin_behavior_1647():
    r = m47.reductions([('a',10,4),('b',0,5),('c',2,2)])
    assert r == {'reductions': (('a',6,F(3,5)),('b',-5,None),('c',0,F(0))),
                 'total_delta': 1, 'increased': ('b',), 'scope': m47.SCOPE}
    # zero delta is not an increase
    assert m47.reductions([('x',3,3)])['increased'] == ()
    try:
        m47.reductions([('x',0,-1)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1648():
    # repeated labels aggregate; zero-input group gets None fraction
    r = m48.recovery([('a',10,4),('a',0,0),('b',5,5)])
    assert r == {'recovery': (('a',10,4,6,F(2,5)),('b',5,5,0,F(1))),
                 'total_residual': 6, 'scope': m48.SCOPE}
    assert m48.recovery([('z',0,0)])['recovery'] == (('z',0,0,0,None),)
    try:
        m48.recovery([('x',3,4)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1647_1648():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1647_1648.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1647_1648.py')
    spec = importlib.util.spec_from_file_location('shipped_1647_1648', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

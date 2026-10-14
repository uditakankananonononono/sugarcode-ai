import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import compost_mix1649 as m49, digestion_retention1650 as m50

def test_audpin_scope_1649():
    assert m49.SCOPE == 'caller carbon-nitrogen mixture arithmetic only; no composting advice'
    assert "PARTIAL: caller carbon/nitrogen mixture arithmetic only" in m49.__doc__

def test_audpin_scope_1650():
    assert m50.SCOPE == 'caller volume-flow retention arithmetic only; no anaerobic digestion advice'
    assert "PARTIAL: caller volume/flow retention arithmetic only" in m50.__doc__

def test_audpin_behavior_1649():
    r = m49.mixture([('a',30,10),('b',0,0)])
    assert r == {'components': (('a',F(3)),('b',None)), 'carbon': 30,
                 'nitrogen': 10, 'ratio': F(3), 'scope': m49.SCOPE}
    # all-zero nitrogen: aggregate None
    assert m49.mixture([('x',5,0)])['ratio'] is None
    try:
        m49.mixture([('x',-1,0)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1650():
    r = m50.retention([('a',10,3),('b',5,5)], 3)
    assert r == {'retention': (('a',F(10,3)),('b',F(1))), 'below': ('b',),
                 'maximum': F(10,3), 'scope': m50.SCOPE}
    # equality not below
    assert m50.retention([('x',6,2)], 3)['below'] == ()
    # zero volume allowed
    assert m50.retention([('x',0,5)], 0)['maximum'] == 0
    try:
        m50.retention([('x',1,0)], 0); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1649_1650():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1649_1650.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1649_1650.py')
    spec = importlib.util.spec_from_file_location('shipped_1649_1650', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

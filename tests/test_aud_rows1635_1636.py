import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import ocean_limits1635 as m35, afforestation_grid1636 as m36

def test_audpin_scope_1635():
    assert m35.SCOPE == 'caller abstract limiting-resource ratios only; no ocean productivity or uptake claims'
    assert "PARTIAL: caller abstract resource/requirement limiting-ratio arithmetic only" in m35.__doc__

def test_audpin_scope_1636():
    assert m36.SCOPE == 'caller rectangular interior lattice counts only; no planting or carbon recommendations'
    assert "PARTIAL: caller rectangular interior lattice count arithmetic only" in m36.__doc__

def test_audpin_behavior_1635():
    r = m35.limits([('a',7,2),('b',9,3),('c',3,1)])
    assert r == {'limits': (('a',F(7,2)),('b',F(3)),('c',F(3))),
                 'supported_units': F(3), 'limiting': ('b','c'), 'scope': m35.SCOPE}
    # zero available -> supported 0
    assert m35.limits([('a',0,5)])['supported_units'] == 0
    try:
        m35.limits([('a',1,0)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1636():
    r = m36.plots([('p',10,7),('q',1,1)], 3)
    assert r == {'plots': (('p',3,2,6),('q',0,0,0)), 'total_sites': 6, 'scope': m36.SCOPE}
    # boundary excluded: dimension exactly spacing -> 0 sites
    assert m36.plots([('a',3,3)], 3)['plots'] == (('a',0,0,0),)
    # zero dimension supported
    assert m36.plots([('a',0,5)], 1)['total_sites'] == 0
    # spacing larger than dimension -> 0
    assert m36.plots([('a',2,2)], 100)['total_sites'] == 0
    try:
        m36.plots([('a',1,1)], 0); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1635_1636():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1635_1636.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1635_1636.py')
    spec = importlib.util.spec_from_file_location('shipped_1635_1636', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import renewable_mix1641 as m41, efficiency_delta1642 as m42

def test_audpin_scope_1641():
    assert m41.SCOPE == 'caller generation-unit portfolio arithmetic only; no renewable output or emissions claims'
    assert "PARTIAL: caller generation-unit portfolio arithmetic only" in m41.__doc__

def test_audpin_scope_1642():
    assert m42.SCOPE == 'caller before-after input arithmetic only; no verified energy savings or efficiency claims'
    assert "PARTIAL: caller before/after input arithmetic only" in m42.__doc__

def test_audpin_behavior_1641():
    r = m41.mix([('b',7,True),('a',3,False)])
    assert r == {'portfolio': (('a',3,False),('b',7,True)), 'total': 10,
                 'flagged_total': 7, 'unflagged_total': 3, 'flagged_fraction': F(7,10), 'scope': m41.SCOPE}
    # all-zero total -> fraction None
    assert m41.mix([('z',0,True)])['flagged_fraction'] is None
    # int 1 is not exactbool
    try:
        m41.mix([('a',0,1)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1642():
    r = m42.changes([('a',10,4),('b',0,5)])
    assert r == {'changes': (('a',6,F(3,5)),('b',-5,None)), 'before_total': 10,
                 'after_total': 9, 'difference': 1, 'aggregate_fraction': F(1,10), 'scope': m42.SCOPE}
    # negative savings kept
    assert m42.changes([('x',2,9)])['difference'] == -7
    # all before zero -> aggregate None
    assert m42.changes([('x',0,0)])['aggregate_fraction'] is None
    try:
        m42.changes([('a',-1,0)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1641_1642():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1641_1642.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1641_1642.py')
    spec = importlib.util.spec_from_file_location('shipped_1641_1642', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

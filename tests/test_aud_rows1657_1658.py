import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import water_bounds1657 as m57, groundwater_balance1658 as m58

def test_audpin_scope_1657():
    assert m57.SCOPE == 'caller measurement-bound comparisons only; no water quality or safety claims'
    assert "PARTIAL: caller measurement/bound comparison only" in m57.__doc__

def test_audpin_scope_1658():
    assert m58.SCOPE == 'caller initial-recharge-withdrawal balances only; no groundwater management advice'
    assert "PARTIAL: caller initial/recharge/withdrawal balance only" in m58.__doc__

def test_audpin_behavior_1657():
    r = m57.compare([('a',5,1,9),('b',0,1,9),('c',10,1,9),('d',5,5,5)])
    assert r == {'comparisons': (('a','within',4,4),('b','below',-1,9),('c','above',9,-1),('d','within',0,0)),
                 'outside': ('b','c'), 'within_count': 2, 'scope': m57.SCOPE}
    # bound edges inclusive
    assert m57.compare([('x',1,1,9)])['within_count'] == 1
    assert m57.compare([('x',9,1,9)])['outside'] == ()
    try:
        m57.compare([('x',0,5,4)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1658():
    r = m58.balances([('a',10,4,9),('b',0,0,0)])
    assert r == {'balances': (('a',5,-5),('b',0,0)), 'negative': (),
                 'total_final': 5, 'total_change': -5, 'scope': m58.SCOPE}
    # strictly negative final flagged; not clamped
    r2 = m58.balances([('x',1,0,5)])
    assert r2['balances'] == (('x',-4,-5),) and r2['negative'] == ('x',)
    try:
        m58.balances([('x',0,0,-1)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1657_1658():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1657_1658.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1657_1658.py')
    spec = importlib.util.spec_from_file_location('shipped_1657_1658', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

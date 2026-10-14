import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import sequestration_decay1631 as m31, negative_net1632 as m32

def test_audpin_scope_1631():
    assert m31.SCOPE == 'caller stock-retention recurrence only; no sequestration permanence or emissions claims'
    assert "PARTIAL: caller stock-retention recurrence only" in m31.__doc__

def test_audpin_scope_1632():
    assert m32.SCOPE == 'caller removal-emission bookkeeping only; no carbon credits or net-zero certification'
    assert "PARTIAL: caller removal/emission bookkeeping only" in m32.__doc__

def test_audpin_behavior_1631():
    r = m31.retain([10,20], 5, 1, 2)
    assert r == {'stocks': (F(25,2), F(105,4)), 'losses': (F(5,2), F(25,4)),
                 'final_stock': F(105,4), 'total_losses': F(35,4), 'scope': m31.SCOPE}
    # full retention: no losses
    r2 = m31.retain([3], 4, 1, 1)
    assert r2['total_losses'] == 0 and r2['final_stock'] == 7
    # zero retention: stock replaced by addition each step
    r3 = m31.retain([5,7], 100, 0, 1)
    assert r3['stocks'] == (F(5), F(7))
    try:
        m31.retain([1], 0, 1, 0); assert False
    except ValueError:
        pass

def test_audpin_behavior_1632():
    r = m32.net([('b',3,5),('a',10,2),('c',4,4)])
    assert r == {'net': (('a',8),('b',-2),('c',0)), 'removed_total': 17,
                 'emitted_total': 11, 'net_total': 6, 'positive': ('a',), 'scope': m32.SCOPE}
    # zero net is not positive
    assert m32.net([('x',5,5)])['positive'] == ()
    # all-negative net_total
    assert m32.net([('x',0,9)])['net_total'] == -9
    try:
        m32.net([('a',0,0),('a',1,1)]); assert False
    except ValueError as e:
        assert 'unique' in str(e)

def test_audpin_shipped_suite_1631_1632():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1631_1632.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1631_1632.py')
    spec = importlib.util.spec_from_file_location('shipped_1631_1632', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

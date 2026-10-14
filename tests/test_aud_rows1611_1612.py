import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import satellite_paths1611 as m11, deep_retry1612 as m12

def test_audpin_scope_1611():
    assert m11.SCOPE == 'caller path-length propagation arithmetic only; no satellite visibility or link claims'
    assert "PARTIAL: caller path-length propagation arithmetic only" in m11.__doc__

def test_audpin_scope_1612():
    assert m12.SCOPE == 'caller independent retry arithmetic only; no space-channel or mission reliability claims'
    assert "PARTIAL: caller independent retry probability arithmetic only" in m12.__doc__

def test_audpin_behavior_1611():
    r = m11.delay([10,5], 2)
    assert r == {'segment_delays': (F(5), F(5,2)), 'one_way': F(15,2), 'doubled': F(15),
                 'scope': m11.SCOPE}
    assert m11.delay([0], 1000000000)['one_way'] == 0
    # order preserved, repeats kept
    assert m11.delay([3,1,3], 2)['segment_delays'] == (F(3,2), F(1,2), F(3,2))
    try:
        m11.delay([], 1); assert False
    except ValueError:
        pass

def test_audpin_behavior_1612():
    r = m12.retries(1,2,3,10)
    assert r == {'first_success': ((1,F(1,2)),(2,F(1,4)),(3,F(1,8))), 'exhausted': F(1,8),
                 'expected_attempts': F(7,4), 'expected_ticks': F(35,2), 'scope': m12.SCOPE}
    # certain success: exactly one attempt expected
    r2 = m12.retries(1,1,64,1000000)
    assert r2['expected_attempts'] == 1 and r2['expected_ticks'] == 1000000 and r2['exhausted'] == 0
    # zero success: all attempts spent, exhausted 1
    r3 = m12.retries(0,5,2,0)
    assert r3['expected_attempts'] == 2 and r3['exhausted'] == 1 and r3['expected_ticks'] == 0
    try:
        m12.retries(1,2,0,0); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1611_1612():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1611_1612.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1611_1612.py')
    spec = importlib.util.spec_from_file_location('shipped_1611_1612', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

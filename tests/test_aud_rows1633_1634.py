import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import geo_sensitivity1633 as m33, solar_balance1634 as m34

def test_audpin_scope_1633():
    assert m33.SCOPE == 'caller perturbation sensitivity arithmetic only; no geoengineering effects or safety'
    assert "PARTIAL: caller finite perturbation sensitivity arithmetic only" in m33.__doc__

def test_audpin_scope_1634():
    assert m34.SCOPE == 'caller incoming/reflected arithmetic only; no radiative forcing or intervention claims'
    assert "PARTIAL: caller incoming/reflected arithmetic only" in m34.__doc__

def test_audpin_behavior_1633():
    r = m33.slopes([('x',4,8),('y',-2,6)])
    assert r == {'slopes': (('x',F(2)),('y',F(-3))), 'minimum': F(-3),
                 'maximum': F(2), 'scope': m33.SCOPE}
    # negative dy allowed
    assert m33.slopes([('a',2,-4)])['slopes'] == (('a',F(-2)),)
    # single row: min == max
    r2 = m33.slopes([('a',3,7)])
    assert r2['minimum'] == r2['maximum'] == F(7,3)
    # zero dx refused
    try:
        m33.slopes([('a',0,5)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1634():
    r = m34.balance([('x',10,1,4),('y',7,1,1)])
    assert r == {'balance': (('x',F(5,2),F(15,2)),('y',F(7),F(0))), 'incoming_total': 17,
                 'reflected_total': F(19,2), 'remainder_total': F(15,2), 'scope': m34.SCOPE}
    # full reflection: remainder zero
    assert m34.balance([('a',8,1,1)])['remainder_total'] == 0
    # zero incoming rows fine
    assert m34.balance([('a',0,1,2)])['reflected_total'] == 0
    try:
        m34.balance([('a',1,3,2)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1633_1634():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1633_1634.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1633_1634.py')
    spec = importlib.util.spec_from_file_location('shipped_1633_1634', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

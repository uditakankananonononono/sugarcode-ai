import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import climate_recurrence1621 as m21, warming_scenarios1622 as m22

def test_audpin_scope_1621():
    assert m21.SCOPE == 'caller scalar affine recurrence only; no climate modeling or forecasts'
    assert "PARTIAL: caller scalar affine recurrence arithmetic only" in m21.__doc__

def test_audpin_scope_1622():
    assert m22.SCOPE == 'caller linear scenario arithmetic only; no global-warming projections'
    assert "PARTIAL: caller linear scenario arithmetic only" in m22.__doc__

def test_audpin_behavior_1621():
    r = m21.evolve([1,2], 3, 1, 2)
    assert r == {'states': (F(3), F(5,2), F(13,4)), 'final': F(13,4), 'scope': m21.SCOPE}
    # zero coefficient wipes history
    assert m21.evolve([7], -5, 0, 1)['states'] == (F(-5), F(7))
    # negative forcing and initial allowed
    assert m21.evolve([-1], -1, 1, 1)['final'] == F(-2)
    try:
        m21.evolve([1], 0, 2, 1); assert False
    except ValueError:
        pass

def test_audpin_behavior_1622():
    r = m22.scenarios([('b',1,1,2),('a',0,1,1)], [2,0])
    assert r == {'scenarios': (('a', ((0,F(0)),(2,F(2)))), ('b', ((0,F(1)),(2,F(2))))),
                 'envelope': ((0,F(0),F(1)), (2,F(2),F(2))), 'scope': m22.SCOPE}
    # steps sorted in output regardless of input order; labels sorted
    assert [l for l,_ in m22.scenarios([('z',0,1,1),('a',0,1,1)], [5,1])['scenarios']] == ['a','z']
    assert [s for s,_ in m22.scenarios([('a',0,1,1)], [5,1])['scenarios'][0][1]] == [1,5]
    # negative slope allowed
    assert m22.scenarios([('a',10,-1,2)], [4])['scenarios'][0][1] == ((4, F(8)),)
    try:
        m22.scenarios([('a',0,1,1)], [1,1]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1621_1622():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1621_1622.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1621_1622.py')
    spec = importlib.util.spec_from_file_location('shipped_1621_1622', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

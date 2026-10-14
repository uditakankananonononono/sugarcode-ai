import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import attribution_ratios1627 as m27, mitigation_subsets1628 as m28

def test_audpin_scope_1627():
    assert m27.SCOPE == 'caller event-frequency ratios only; no causal climate attribution claims'
    assert "PARTIAL: caller event-frequency ratio arithmetic only" in m27.__doc__

def test_audpin_scope_1628():
    assert m28.SCOPE == 'caller option cost/value subsets only; no mitigation impacts or policy advice'
    assert "PARTIAL: caller option cost/value subset arithmetic only" in m28.__doc__

def test_audpin_behavior_1627():
    r = m27.ratio((3,4),(1,2))
    assert r == {'left_frequency': F(3,4), 'right_frequency': F(1,2), 'ratio': F(3,2),
                 'relative_fraction': F(1,3), 'scope': m27.SCOPE}
    # equal frequencies: ratio 1, relative 0
    assert m27.ratio((1,2),(2,4))['relative_fraction'] == 0
    # count==total allowed (frequency 1)
    assert m27.ratio((5,5),(1,2))['ratio'] == 2
    try:
        m27.ratio((0,5),(1,2)); assert False
    except ValueError:
        pass

def test_audpin_behavior_1628():
    r = m28.options([('a',3,4),('b',5,6)], 5)
    assert r == {'feasible': (((),0,0),(('a',),3,4),(('b',),5,6)), 'best_value': 6,
                 'ties': (('b',),), 'scope': m28.SCOPE}
    # empty rows: only empty subset
    assert m28.options([], 0)['feasible'] == (((),0,0),)
    # ties listed when values equal
    r2 = m28.options([('a',1,5),('b',2,5)], 2)
    assert r2['best_value'] == 5 and r2['ties'] == (('a',),('b',))
    # zero-cost options always feasible
    r3 = m28.options([('a',0,9)], 0)
    assert r3['best_value'] == 9
    try:
        m28.options([], 12000001); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1627_1628():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1627_1628.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1627_1628.py')
    spec = importlib.util.spec_from_file_location('shipped_1627_1628', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import adaptation_regret1629 as m29, capture_fraction1630 as m30

def test_audpin_scope_1629():
    assert m29.SCOPE == 'caller scenario cost regret arithmetic only; no climate adaptation or policy advice'
    assert "PARTIAL: caller rectangular option/scenario cost regret arithmetic only" in m29.__doc__

def test_audpin_scope_1630():
    assert m30.SCOPE == 'caller stream fraction ledger only; no capture efficiency or emissions claims'
    assert "PARTIAL: caller stream fraction ledger arithmetic only" in m30.__doc__

def test_audpin_behavior_1629():
    r = m29.regret([('b',[3,1]),('a',(2,4))])
    assert r == {'regrets': (('a',(0,3),3),('b',(1,0),1)), 'minimax': 1,
                 'ties': ('b',), 'scope': m29.SCOPE}
    # single row: all regrets zero, minimax 0
    assert m29.regret([('x',[5,9])])['minimax'] == 0
    # ties when worst regrets equal
    r2 = m29.regret([('a',[1,2]),('b',[2,1])])
    assert r2['minimax'] == 1 and r2['ties'] == ('a','b')
    try:
        m29.regret([('a',[1,2]),('b',[1])]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1630():
    r = m30.streams([('x',10,1,2),('y',7,1,1)])
    assert r == {'streams': (('x',F(5),F(5)),('y',F(7),F(0))), 'input_total': 17,
                 'retained_total': F(12), 'remainder_total': F(5), 'retained_fraction': F(12,17),
                 'scope': m30.SCOPE}
    # zero input -> retained_fraction None
    assert m30.streams([('z',0,1,2)])['retained_fraction'] is None
    # zero fraction retains nothing
    assert m30.streams([('z',9,0,5)])['retained_total'] == 0
    try:
        m30.streams([('a',0,1,0)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1629_1630():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1629_1630.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1629_1630.py')
    spec = importlib.util.spec_from_file_location('shipped_1629_1630', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

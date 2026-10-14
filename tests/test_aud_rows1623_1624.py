import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import carbon_transfer1623 as m23, ocean_ratio1624 as m24

def test_audpin_scope_1623():
    assert m23.SCOPE == 'caller pool-transfer ledger only; no carbon flux or climate analysis claims'
    assert "PARTIAL: caller nonnegative pool-transfer ledger arithmetic only" in m23.__doc__

def test_audpin_scope_1624():
    assert m24.SCOPE == 'caller positive concentration ratios only; no ocean chemistry or pH predictions'
    assert "PARTIAL: caller positive concentration-ratio arithmetic only" in m24.__doc__

def test_audpin_behavior_1623():
    r = m23.transfer([('a',10),('b',5)], [('a','b',4)])
    assert r == {'balances': (('a',6),('b',9)), 'total': 15, 'scope': m23.SCOPE}
    # chained moves: overdraw checked against CURRENT balance
    r2 = m23.transfer([('a',1),('b',0),('c',0)], [('a','b',1),('b','c',1)])
    assert r2['balances'] == (('a',0),('b',0),('c',1))
    # zero-amount move allowed
    assert m23.transfer([('a',1),('b',0)], [('a','b',0)])['total'] == 1
    # overdraw refused
    try:
        m23.transfer([('a',1),('b',0)], [('a','b',1),('a','b',1)]); assert False
    except ValueError as e:
        assert 'overdraw' in str(e)
    # unicode labels
    assert m23.transfer([('Ω',1),('É',0)], [('Ω','É',1)])['balances'][0][0] == 'É'

def test_audpin_behavior_1624():
    r = m24.ratios([('x',1,2),('y',3,4)], (1,4))
    assert r == {'ratios': (('x',F(2),F(1)),('y',F(3),F(2))), 'scope': m24.SCOPE}
    # equal to reference -> ratio 1, deviation 0
    assert m24.ratios([('a',2,8)], (1,4))['ratios'] == (('a',F(1),F(0)),)
    # sorted by label not caller order
    assert [t[0] for t in m24.ratios([('z',1,1),('a',1,1)], (1,1))['ratios']] == ['a','z']
    try:
        m24.ratios([('a',1,1)], (0,1)); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1623_1624():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1623_1624.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1623_1624.py')
    spec = importlib.util.spec_from_file_location('shipped_1623_1624', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

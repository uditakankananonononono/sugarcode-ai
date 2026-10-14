import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import hydrogen_chain1645 as m45, circular_flows1646 as m46

def test_audpin_scope_1645():
    assert m45.SCOPE == 'caller staged conversion-factor chain only; no hydrogen performance or cost claims'
    assert "PARTIAL: caller staged conversion-factor chain only" in m45.__doc__

def test_audpin_scope_1646():
    assert m46.SCOPE == 'caller incoming-outgoing resource ledger only; no circularity or sustainability claims'
    assert "PARTIAL: caller incoming/outgoing resource ledger only" in m46.__doc__

def test_audpin_behavior_1645():
    r = m45.chain([('a',1,2),('b',3,4)], 16)
    assert r == {'stages': (('a',F(8),F(8)),('b',F(6),F(2))), 'final': F(6),
                 'total_losses': F(10), 'scope': m45.SCOPE}
    # empty chain: final = initial, no losses
    assert m45.chain([], 7)['final'] == 7 and m45.chain([], 7)['total_losses'] == 0
    # zero factor zeroes the chain
    assert m45.chain([('x',0,5)], 9)['final'] == 0
    try:
        m45.chain([('a',1,0)], 0); assert False
    except ValueError:
        pass

def test_audpin_behavior_1646():
    # repeated labels aggregate
    r = m46.flows([('b',3,5),('a',10,2),('b',1,0)])
    assert r == {'flows': (('a',10,2,8),('b',4,5,-1)), 'positive': ('a',),
                 'negative': ('b',), 'net_total': 7, 'scope': m46.SCOPE}
    # zero balance in neither list
    assert m46.flows([('x',5,5)])['positive'] == () and m46.flows([('x',5,5)])['negative'] == ()
    try:
        m46.flows([('x',-1,0)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1645_1646():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1645_1646.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1645_1646.py')
    spec = importlib.util.spec_from_file_location('shipped_1645_1646', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

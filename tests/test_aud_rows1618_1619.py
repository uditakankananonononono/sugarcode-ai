import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import network_rules1618 as m18, cyber_inventory1619 as m19

def test_audpin_scope_1618():
    assert m18.SCOPE == 'caller integer-port rule simulation only; no firewall enforcement or security claims'
    assert "PARTIAL: caller integer-port first-match rule simulation only" in m18.__doc__

def test_audpin_scope_1619():
    assert m19.SCOPE == 'caller integer version inventory comparison only; no vulnerability or security claims'
    assert "PARTIAL: caller patch-version inventory comparison only" in m19.__doc__

def test_audpin_behavior_1618():
    r = m18.evaluate([[80,90,'deny'],[0,65535,'allow']], [80,79,443], 'deny')
    assert r == {'decisions': ((80,'deny',0),(79,'allow',1),(443,'allow',1)), 'scope': m18.SCOPE}
    # no match -> default with None index
    assert m18.evaluate([], [1], 'allow')['decisions'] == ((1,'allow',None),)
    # first match wins over later overlapping rule
    r2 = m18.evaluate([(0,100,'deny'),(50,60,'allow')], [55], 'allow')
    assert r2['decisions'] == ((55,'deny',0),)
    try:
        m18.evaluate([], [1], 'ALLOW'); assert False
    except ValueError:
        pass

def test_audpin_behavior_1619():
    r = m19.inventory([('b',3,5),('a',10,2),('c',4,4)])
    assert r == {'inventory': (('a',-8,False),('b',2,True),('c',0,False)),
                 'below': ('b',), 'largest_gap': 2, 'scope': m19.SCOPE}
    # equality is not below
    assert m19.inventory([('x',5,5)])['below'] == ()
    # largest_gap never negative
    assert m19.inventory([('x',9,1)])['largest_gap'] == 0
    # printable unicode labels accepted, sorted by label
    r2 = m19.inventory([('Ω',0,1),('É',0,0)])
    assert [t[0] for t in r2['inventory']] == sorted(['Ω','É'])
    try:
        m19.inventory([('a',0,0),('a',1,1)]); assert False
    except ValueError as e:
        assert 'unique' in str(e)

def test_audpin_shipped_suite_1618_1619():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1618_1619.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1618_1619.py')
    spec = importlib.util.spec_from_file_location('shipped_1618_1619', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

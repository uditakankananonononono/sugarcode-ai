import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import waste_energy1651 as m51, landfill_capacity1652 as m52

def test_audpin_scope_1651():
    assert m51.SCOPE == 'caller mass-energy-factor arithmetic only; no waste-to-energy performance claims'
    assert "PARTIAL: caller mass/energy-factor multiplication only" in m51.__doc__

def test_audpin_scope_1652():
    assert m52.SCOPE == 'caller capacity-used-incoming ledger only; no landfill management advice'
    assert "PARTIAL: caller capacity/used/incoming ledger only" in m52.__doc__

def test_audpin_behavior_1651():
    r = m51.energy([('a',10,1,2),('b',0,5,1)])
    assert r == {'energy': (('a',F(5)),('b',F(0))), 'total': F(5),
                 'positive': ('a',), 'scope': m51.SCOPE}
    # zero numerator -> zero energy, not positive
    assert m51.energy([('x',9,0,7)])['positive'] == ()
    try:
        m51.energy([('x',1,1,0)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1652():
    # negative free-after NOT clamped; strict overflow only
    r = m52.capacity([('a',10,4,7),('b',5,5,0)])
    assert r == {'capacity': (('a',6,-1),('b',0,0)), 'overflow': ('a',),
                 'total_free_after': -1, 'scope': m52.SCOPE}
    # exact fit: free-after 0, no overflow
    assert m52.capacity([('x',5,2,3)])['overflow'] == ()
    try:
        m52.capacity([('x',3,4,0)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1651_1652():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1651_1652.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1651_1652.py')
    spec = importlib.util.spec_from_file_location('shipped_1651_1652', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import grid_slots1609 as m09, optical_loss1610 as m10

def test_audpin_scope_1609():
    assert m09.SCOPE == 'caller abstract resource-grid occupancy only; no 5G/6G radio or protocol claims'
    assert "PARTIAL: caller rectangular resource-grid occupancy only" in m09.__doc__

def test_audpin_scope_1610():
    assert m10.SCOPE == 'caller transmission-factor product only; no optical performance or rate claims'
    assert "PARTIAL: caller multiplicative transmission-factor arithmetic only" in m10.__doc__

def test_audpin_behavior_1609():
    r = m09.occupancy([[0,2,0,2],(1,3,1,3)], 3, 3)
    assert r == {'occupied': ((0,0),(0,1),(1,0),(1,1),(1,2),(2,1),(2,2)), 'free_count': 2,
                 'occupied_fraction': F(7,9), 'scope': m09.SCOPE}
    assert m09.occupancy([], 1, 1)['occupied_fraction'] == 0
    assert m09.occupancy([[0,32,0,32]], 32, 32)['occupied_fraction'] == 1
    # overlapping rectangles counted once
    assert m09.occupancy([(0,2,0,2),(0,2,0,2)], 2, 2)['free_count'] == 0
    try:
        m09.occupancy([(0,3,0,1)], 2, 2); assert False
    except ValueError:
        pass

def test_audpin_behavior_1610():
    r = m10.transmission([('a',1,2),('b',3,4)])
    assert r == {'stages': (('a',F(1,2)),('b',F(3,8))), 'transmission': F(3,8),
                 'loss': F(5,8), 'scope': m10.SCOPE}
    assert m10.transmission([])['transmission'] == 1
    assert m10.transmission([])['loss'] == 0
    # zero factor zeroes the whole chain
    assert m10.transmission([('x',1,2),('y',0,5)])['transmission'] == 0
    # printable unicode labels accepted
    assert m10.transmission([('Ω',1,1)])['stages'][0][0] == 'Ω'
    try:
        m10.transmission([('a',2,1)]); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1609_1610():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1609_1610.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1609_1610.py')
    spec = importlib.util.spec_from_file_location('shipped_1609_1610', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

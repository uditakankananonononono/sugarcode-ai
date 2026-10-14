import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import transport_load1643 as m43, ev_energy1644 as m44

def test_audpin_scope_1643():
    assert m43.SCOPE == 'caller trip passenger-distance totals only; no sustainability or routing claims'
    assert "PARTIAL: caller trip passenger/distance totals only" in m43.__doc__

def test_audpin_scope_1644():
    assert m44.SCOPE == 'caller battery-energy trip ledger only; no EV range or charging-control claims'
    assert "PARTIAL: caller battery-energy trip ledger only" in m44.__doc__

def test_audpin_behavior_1643():
    r = m43.trips([('a',10,3),('b',0,5)])
    assert r == {'passenger_distances': (('a',30),('b',0)), 'distance_total': 10,
                 'passenger_distance_total': 30, 'weighted_passengers': F(3), 'scope': m43.SCOPE}
    # all-zero distance -> weighted None
    assert m43.trips([('z',0,9)])['weighted_passengers'] is None
    try:
        m43.trips([('a',1,1001)]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1644():
    r = m44.ledger([(10,3),(20,7)], 15, 5)
    assert r == {'steps': ((0,12,0),(1,8,17)), 'final_charge': 8, 'use_total': 10,
                 'discarded_total': 17, 'scope': m44.SCOPE}
    # charge capped at capacity
    assert m44.ledger([(100,0)], 10, 0)['discarded_total'] == 90
    # use exceeding current refuses whole call even with later steps
    try:
        m44.ledger([(5,0),(0,6)], 10, 0); assert False
    except ValueError as e:
        assert 'exceed' in str(e)
    # overdraw refused even when charge was discarded earlier
    try:
        m44.ledger([(100,0),(0,11)], 10, 0); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1643_1644():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1643_1644.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1643_1644.py')
    spec = importlib.util.spec_from_file_location('shipped_1643_1644', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

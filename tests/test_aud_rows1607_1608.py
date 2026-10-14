import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import comm_frames1607 as m07
from sugarcode.extra_doc import wireless_shares1608 as m08


def test_audpin_scope_1607():
    assert m07.SCOPE == 'caller frame overhead arithmetic only; no communication performance claims'


def test_audpin_behavior_1607():
    r = m07.frames([0, 3, 5], 4, 2)
    assert r == {'frames': ((0, 0, 0), (3, 1, 5), (5, 2, 9)), 'payload_total': 8,
                 'wire_total': 14, 'frame_count': 3, 'useful_fraction': F(4, 7),
                 'scope': m07.SCOPE}
    # zero wire total -> useful_fraction None
    assert m07.frames([0], 4, 0)['useful_fraction'] is None
    # exact-fit payload: no extra frame
    assert m07.frames([8], 4, 1)['frames'] == ((8, 2, 10),)
    # ceiling: 9 needs 3 frames at capacity 4
    assert m07.frames([9], 4, 0)['frames'] == ((9, 3, 9),)
    # overhead 0: wire == payload
    assert m07.frames([5], 4, 0)['frames'] == ((5, 2, 5),)
    for bad in (-1, 1000001, True, 1.5, '3'):
        try:
            m07.frames([bad], 4, 2); assert False
        except ValueError:
            pass


def test_audpin_scope_1608():
    assert m08.SCOPE == 'caller weighted resource shares only; no wireless scheduling or rate claims'


def test_audpin_behavior_1608():
    r = m08.shares([('b', 1), ('a', 3)], 10)
    assert r == {'shares': (('a', F(3, 4), F(15, 2)), ('b', F(1, 4), F(5, 2))),
                 'capacity': 10, 'scope': m08.SCOPE}
    # capacity 0: allocations all zero, shares still exact
    assert m08.shares([('a', 2)], 0)['shares'] == (('a', F(1), F(0)),)
    # label-sorted output regardless of input order
    assert [t[0] for t in m08.shares([('z', 1), ('a', 1)], 4)['shares']] == ['a', 'z']
    # equal weights split evenly: capacity 7 over 3 equal weights -> 7/3 each
    r2 = m08.shares([('a', 5), ('b', 5), ('c', 5)], 7)
    assert all(t[2] == F(7, 3) for t in r2['shares'])
    try:
        m08.shares([('a', 1), ('a', 2)], 10); assert False
    except ValueError as e:
        assert 'unique' in str(e)
    for bad in (0, -1, True, 1.5, '2'):
        try:
            m08.shares([('a', bad)], 10); assert False
        except ValueError:
            pass


def test_audpin_shipped_suite_1607_1608():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1607_1608.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1607_1608.py')
    spec = importlib.util.spec_from_file_location('shipped_1607_1608', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

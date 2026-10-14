import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import information_collision1613 as m13, code_distance1614 as m14

def test_audpin_scope_1613():
    assert m13.SCOPE == 'caller discrete count collision arithmetic only; no source or coding performance claims'
    assert "PARTIAL: caller discrete count collision arithmetic only" in m13.__doc__

def test_audpin_scope_1614():
    assert m14.SCOPE == 'caller binary codebook distances only; no encoding decoding or channel reliability'
    assert "PARTIAL: caller binary codebook Hamming distances only" in m14.__doc__

def test_audpin_behavior_1613():
    r = m13.collision([2,1,1])
    assert r == {'collision': F(3,8), 'inverse_collision': F(8,3), 'positive_categories': 3,
                 'total': 4, 'scope': m13.SCOPE}
    # zero-count slots ignored in categories but kept in nothing else
    assert m13.collision([0,0,5,0])['positive_categories'] == 1
    assert m13.collision([0,0,5,0])['collision'] == 1
    try:
        m13.collision([0,0,0]); assert False
    except ValueError:
        pass

def test_audpin_behavior_1614():
    r = m14.distances(['01','10','11'])
    assert r == {'pairs': (('01','10',2),('01','11',1),('10','11',1)),
                 'minimum_distance': 1, 'disjoint_ball_radius': 0, 'scope': m14.SCOPE}
    # max distance pair, radius floor((d-1)/2)
    r2 = m14.distances(['000','111'])
    assert r2['minimum_distance'] == 3 and r2['disjoint_ball_radius'] == 1
    assert m14.distances(['0','1'])['pairs'] == (('0','1',1),)
    try:
        m14.distances(['01','1']); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1613_1614():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1613_1614.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1613_1614.py')
    spec = importlib.util.spec_from_file_location('shipped_1613_1614', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()


def test_audpin_gapwitness_1614_alphabet_x():
    # closing witness pin for shipped-test gap found by battery survivor strmut@19 ('01'->'01x'):
    # words containing 'x' must be refused (non-binary alphabet); shipped suite never exercises 'x'.
    for w in ('0x', 'x1', 'xx'):
        try:
            m14.distances([w, '10']); assert False, w
        except ValueError:
            pass

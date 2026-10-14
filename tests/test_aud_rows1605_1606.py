import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import microwave_reflect1605 as m05
from sugarcode.extra_doc import radar_delay1606 as m06


def test_audpin_scope_1605():
    assert m05.SCOPE == 'caller real-resistance reflection arithmetic only; no microwave hardware claims'


def test_audpin_behavior_1605():
    r = m05.reflection([3, 1, 3], 2)
    assert r == {'reflection': ((F(1, 5), F(1, 25), F(24, 25)),
                                (F(-1, 3), F(1, 9), F(8, 9)),
                                (F(1, 5), F(1, 25), F(24, 25))), 'scope': m05.SCOPE}
    # input order and repeats preserved
    assert [t[0] for t in m05.reflection([5, 1, 5], 3)['reflection']] == [F(1, 4), F(-1, 2), F(1, 4)]
    # matched load: gamma 0, all transmitted
    assert m05.reflection([7], 7)['reflection'] == ((F(0), F(0), F(1)),)
    # open-ish extreme: load max, reference 1
    assert m05.reflection([1000000], 1)['reflection'][0][0] == F(999999, 1000001)
    for bad in (0, -1, True, 1.5, '3'):
        try:
            m05.reflection([bad], 2); assert False
        except ValueError:
            pass
        try:
            m05.reflection([1], bad); assert False
        except ValueError:
            pass


def test_audpin_scope_1606():
    assert m06.SCOPE == 'caller round-trip delay distance arithmetic only; no radar detection or tracking'


def test_audpin_behavior_1606():
    r = m06.ranges([('b', 1, 2), ('a', 3, 4)], 10)
    assert r == {'ranges': (('a', F(15, 4)), ('b', F(5, 2))), 'minimum': F(5, 2),
                 'maximum': F(15, 4), 'scope': m06.SCOPE}
    # num 0 -> distance 0
    assert m06.ranges([('a', 0, 7)], 10)['ranges'] == (('a', F(0)),)
    # sorted by label
    assert [t[0] for t in m06.ranges([('z', 1, 1), ('a', 1, 1)], 2)['ranges']] == ['a', 'z']
    # denominator must be >= 1, numerator can be 0
    for bad in (0, -1, True, 1.5):
        try:
            m06.ranges([('a', 1, bad)], 10); assert False
        except ValueError:
            pass
    try:
        m06.ranges([('a', 1, 1), ('a', 2, 2)], 10); assert False
    except ValueError as e:
        assert 'unique' in str(e)


def test_audpin_shipped_suite_1605_1606():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1605_1606.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1605_1606.py')
    spec = importlib.util.spec_from_file_location('shipped_1605_1606', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

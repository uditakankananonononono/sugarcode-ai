import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import power_quality1601 as m01
from sugarcode.extra_doc import emc_margin1602 as m02


def test_audpin_scope_1601():
    assert m01.SCOPE == 'caller harmonic squared-ratio arithmetic only; no electrical compliance or safety'


def test_audpin_behavior_1601():
    r = m01.harmonics([2, 1, 0.5])
    assert r == {'fundamental_squared': F(4), 'harmonic_squared_sum': F(5, 4),
                 'thd_squared': F(5, 16), 'harmonic_energy_fraction': F(5, 21),
                 'scope': m01.SCOPE}
    # single fundamental: zero higher
    assert m01.harmonics([3])['thd_squared'] == 0
    # float spelling goes through decimal string: 0.1 -> 1/10 exactly
    assert m01.harmonics([0.1])['fundamental_squared'] == F(1, 100)
    # tuple input accepted
    assert m01.harmonics((2, 1))['harmonic_squared_sum'] == F(1)
    # fundamental zero refused
    try:
        m01.harmonics([0, 1]); assert False
    except ValueError as e:
        assert 'fundamental' in str(e)
    # bool and subclasses refused
    for bad in (True, float('nan'), float('inf'), 1000001, -1):
        try:
            m01.harmonics([1, bad]); assert False
        except ValueError:
            pass


def test_audpin_scope_1602():
    assert m02.SCOPE == 'caller numerical limit margins only; no EMC testing certification or safety'


def test_audpin_behavior_1602():
    r = m02.margins([['B', .3, .2], ('A', -.1, -.1)])
    assert r == {'margins': (('A', F(0), True), ('B', F(-1, 10), False)),
                 'minimum_margin': F(-1, 10), 'all_within': False, 'scope': m02.SCOPE}
    # inclusive pass at equality
    assert m02.margins([('x', 5, 5)])['all_within'] is True
    # printable unicode labels accepted and sorted by label
    r2 = m02.margins([('Ω', 1, 2), ('É', 0, 0)])
    assert [t[0] for t in r2['margins']] == sorted(['Ω', 'É'])
    # negative numbers accepted
    assert m02.margins([('a', -1000000, 1000000)])['minimum_margin'] == F(2000000)
    # duplicate labels refused
    try:
        m02.margins([('a', 0, 0), ('a', 1, 1)]); assert False
    except ValueError as e:
        assert 'unique' in str(e)


def test_audpin_shipped_suite_1601_1602():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1601_1602.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1601_1602.py')
    spec = importlib.util.spec_from_file_location('shipped_1601_1602', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

import unittest
from fractions import Fraction as F
from sugarcode.extra_doc import sea_contributions1625 as m25, extreme_counts1626 as m26

def test_audpin_scope_1625():
    assert m25.SCOPE == 'caller additive contribution arithmetic only; no sea-level or coastal projections'
    assert "PARTIAL: caller additive scenario contribution arithmetic only" in m25.__doc__

def test_audpin_scope_1626():
    assert m26.SCOPE == 'caller integer threshold counts only; no weather forecasts or hazard warnings'
    assert "PARTIAL: caller integer observation threshold count arithmetic only" in m26.__doc__

def test_audpin_behavior_1625():
    r = m25.contributions([('a',1,2),('b',-1,4),('c',0,5)], 10)
    assert r == {'contributions': (('a',F(1,2)),('b',F(-1,4)),('c',F(0))),
                 'positive': F(1,2), 'negative': F(-1,4), 'total': F(1,4),
                 'scenario': F(41,4), 'scope': m25.SCOPE}
    # empty rows: all sums zero, scenario = baseline
    assert m25.contributions([], -3)['scenario'] == -3
    assert m25.contributions([], -3)['total'] == 0
    # zero counts as neither positive nor negative
    r2 = m25.contributions([('z',0,7)], 0)
    assert r2['positive'] == 0 and r2['negative'] == 0
    try:
        m25.contributions([('a',0,0)], 0); assert False
    except ValueError:
        pass

def test_audpin_behavior_1626():
    r = m26.exceedance([5,1,9,9,2], 5)
    assert r == {'indices': (2,3), 'count': 2, 'fraction': F(2,5), 'excess_sum': 8,
                 'max_excess': 4, 'scope': m26.SCOPE}
    # equality not exceedance
    assert m26.exceedance([5], 5)['count'] == 0
    # none: excess defaults 0
    r2 = m26.exceedance([1,2], 100)
    assert r2['excess_sum'] == 0 and r2['max_excess'] == 0 and r2['fraction'] == 0
    # negative values allowed
    assert m26.exceedance([-5,-1], -3)['indices'] == (1,)
    try:
        m26.exceedance([], 0); assert False
    except ValueError:
        pass

def test_audpin_shipped_suite_1625_1626():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra_doc', 'test_quantum_rows1625_1626.py')
    if not os.path.exists(path):
        path = os.path.join('tests', 'extra_doc', 'test_quantum_rows1625_1626.py')
    spec = importlib.util.spec_from_file_location('shipped_1625_1626', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.TestLoader().loadTestsFromModule(mod)
    import io
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    assert res.wasSuccessful()

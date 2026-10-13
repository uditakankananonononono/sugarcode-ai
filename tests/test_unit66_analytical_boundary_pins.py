import math
import pytest
from sugarcode.modules.riboswitch.boundary_response import response_curve as response
from sugarcode.modules.riboswitch.finite_response import response_curve as finite

def test_hill_and_signal_closed_form_both_modes():
    for mode in ['on','off']:
        r=finite(2,mode=mode,hill=2,basal=.2,maximum=1,concentrations=[0,1,2,4])
        occupancy=[0,.2,.5,.8]
        assert [x['occupancy'] for x in r['curve']]==pytest.approx(occupancy)
        assert [x['signal'] for x in r['curve']]==pytest.approx([.2+.8*(o if mode=='on' else 1-o) for o in occupancy])
        assert r['dynamic_range']==5

def test_default_grid_and_hill_closed_form():
    r=finite(2)
    assert len(r['curve'])==61 and r['hill_coefficient']==1.5
    for i in [0,10,30,60]:
        concentration=2*10**(-3+i/10)
        odds=(concentration/2)**1.5
        assert r['curve'][i]['concentration_uM']==pytest.approx(concentration)
        assert r['curve'][i]['occupancy']==pytest.approx(odds/(1+odds))
    assert r['basal']==.05 and r['maximum']==1 and r['mode']=='on'

def test_kd_hill_basal_admission_exact_edges():
    assert response(1e-100,hill=100,basal=0,maximum=1,concentrations=[0,1e-100])['curve'][1]['occupancy']==.5
    for kw in [{'kd_uM':1e-101},{'kd_uM':1,'hill':0},{'kd_uM':1,'hill':100.001},{'kd_uM':1,'basal':1,'maximum':1}]:
        with pytest.raises(ValueError):response(**kw,concentrations=[0,1])

def test_point_cap_and_equal_concentrations():
    r=response(1,concentrations=[0]*10000)
    assert len(r['curve'])==10000 and all(x['occupancy']==0 for x in r['curve'])
    with pytest.raises(ValueError):response(1,concentrations=[1])

def test_base_boundary_default_hill_independent_of_finite_wrapper():
    r=response(2,concentrations=[1,2,4])
    assert r['hill_coefficient']==1.5
    odds=[(1/2)**1.5,1,2**1.5]
    assert [x['occupancy'] for x in r['curve']]==pytest.approx([x/(1+x) for x in odds])

def test_direct_default_signal_and_subunit_hill():
    r=response(2,concentrations=[0,2])
    assert r['basal']==.05 and r['maximum']==1
    assert r['curve'][0]['signal']==.05 and r['curve'][1]['signal']==pytest.approx(.525)
    r=response(4,hill=.5,basal=0,maximum=1,concentrations=[0,1,4,16])
    assert [x['occupancy'] for x in r['curve']]==pytest.approx([0,1/3,.5,2/3])

def test_near_kd_positive_logit_stays_positive_branch():
    # x/kd=exp(.2),hill1=>z.2; e=exp(-.2), occupancy1/(1+e).
    r=response(1,hill=1,concentrations=[1,math.exp(.2)])
    assert r['curve'][1]['occupancy']==pytest.approx(1/(1+math.exp(-.2)))

def test_finite_guard_recurses_through_curve_list(monkeypatch):
    from sugarcode.modules.riboswitch import finite_response as m
    monkeypatch.setattr(m,'_bounded',lambda *a,**k:{'curve':[{'signal':float('inf')}], 'dynamic_range':1})
    with pytest.raises(ValueError,match='UNREPRESENTABLE'):m.response_curve(1)

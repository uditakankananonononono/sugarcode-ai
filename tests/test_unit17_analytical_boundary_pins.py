import math
import pytest
from sugarcode.modules.deepsplice import hardened as m

@pytest.mark.parametrize('x,p',[(0,.5),(math.log(3),.75),(-math.log(3),.25),(1000,1),(-1000,0)])
def test_logistic_closed_form(x,p):assert m._stable_logistic(x)==pytest.approx(p)

def test_exon_inclusion_half_probability_interval_default():
    # r=a=0 and support=.25 => logit0, psi.5, radius1.96*.05=.098.
    r=m.safe_exon_inclusion(0,0,{'exon_definition_support':.25})
    assert r=={'psi':.5,'delta_site_strength':0,'interval95':[.402,.598],'calibration_n':100}
    r=m.safe_exon_inclusion(0,0,{'exon_definition_support':.25},calibration_n=400)
    assert r['interval95']==pytest.approx([.451,.549])

@pytest.mark.parametrize('ref,alt,support',[(10,10,100),(-10,-10,-100)])
def test_exon_numerical_admission_endpoints(ref,alt,support):
    assert 0<=m.safe_exon_inclusion(ref,alt,{'exon_definition_support':support},calibration_n=10**9)['psi']<=1

@pytest.mark.parametrize('ref,alt,support',[(10.001,0,0),(0,10.001,0),(-10.001,0,0),(0,-10.001,0),(0,0,100.001),(0,0,-100.001)])
def test_exon_numerical_admission_outside(ref,alt,support):
    with pytest.raises(ValueError,match='out of range'):m.safe_exon_inclusion(ref,alt,{'exon_definition_support':support})


def test_recursive_output_finiteness():
    assert m._ok({'x':[(1,2),[3]]})
    assert not m._ok({'x':[(1,float('nan'))]})
    assert not m._ok([{'x':float('inf')}])


def test_declared_numeric_and_sequence_caps():
    assert m._num('x',10**9,-10**9,10**9)==10**9
    with pytest.raises(ValueError,match='magnitude'):m._num('x',10**9+1,-10**9-1,10**9+1)
    seq='A'*1000000
    assert m._seq('s',seq)==seq
    with pytest.raises(ValueError):m._seq('s',seq+'A')


def test_branchpoint_and_variant_index_last_base(monkeypatch):
    monkeypatch.setattr(m.core,'branchpoint_variant_effect',lambda s,i,b:(i,b))
    assert m.safe_branchpoint_variant_effect('A'*60,59,'t')==(59,'T')
    monkeypatch.setattr(m.core,'variant_at',lambda s,i,b,*a:(i,b))
    assert m.safe_variant_at('AC',1,'g')==(1,'G')
    with pytest.raises(ValueError):m.safe_variant_at('AC',2,'g')


def test_list_caps_and_optional_numeric_defaults(monkeypatch):
    class Sized(list):
        def __len__(self):return 100000
    seen=[]
    monkeypatch.setattr(m.core,'active_learning',lambda c:seen.append(c) or c)
    monkeypatch.setattr(m.core,'intervention_simulation',lambda w,a,s:s)
    assert m.safe_active_learning(Sized([{'probability':.5}]))==[{'probability':.5}]
    assert m.safe_intervention_simulation(.5,.2,Sized([{}]))==[{}]
    seen.clear()
    assert m.safe_active_learning([{'probability':.5,'impact':1000000}])
    with pytest.raises(ValueError,match='out of range'):m.safe_active_learning([{'probability':.5,'impact':1000001}])

def test_optional_fields_checked_with_declared_defaults(monkeypatch):
    seen=[]
    num=m._num
    def observe(name,value,lo,hi):seen.append((name,value));return num(name,value,lo,hi)
    monkeypatch.setattr(m,'_num',observe)
    monkeypatch.setattr(m.core,'active_learning',lambda c:c)
    monkeypatch.setattr(m.core,'intervention_simulation',lambda w,a,s:s)
    m.safe_active_learning([{'probability':.5}])
    m.safe_intervention_simulation(.5,.2,[{}])
    assert ('impact',.5) in seen and ('psi_shift',0) in seen and ('offtarget_risk',.1) in seen

@pytest.mark.parametrize('value',[-1e-12,-1.0001e-12])
def test_isoform_negative_tolerance_exact(monkeypatch,value):
    monkeypatch.setattr(m.core,'isoform_distribution',lambda *a:{'isoforms':{'a':value,'b':1-value}})
    if value==-1e-12:assert m.safe_isoform_distribution(.5)['isoforms']['a']==value
    else:
        with pytest.raises(ValueError,match='probability'):m.safe_isoform_distribution(.5)


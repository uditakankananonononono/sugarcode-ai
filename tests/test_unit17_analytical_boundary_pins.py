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


@pytest.mark.parametrize('lo,hi',[(-10,10),(-100,100),(0,1),(0,1000000),(-1,1)])
def test_every_numeric_range_endpoints_and_near_outside(lo,hi):
    for x in [lo,hi]:assert m._num('x',x,lo,hi)==x
    for x in [lo-1e-9,hi+1e-9,lo-.001*max(1,abs(lo)),hi+.001*max(1,abs(hi))]:
        with pytest.raises(ValueError,match='out of range'):m._num('x',x,lo,hi)

@pytest.mark.parametrize('lo,hi',[(0,59),(0,1),(1,10**9)])
def test_integer_range_exact(lo,hi):
    assert m._int('x',lo,lo,hi)==lo and m._int('x',hi,lo,hi)==hi
    for x in [lo-1,hi+1]:
        with pytest.raises(ValueError):m._int('x',x,lo,hi)

def test_public_numeric_endpoints_delegate(monkeypatch):
    monkeypatch.setattr(m.core,'isoform_distribution',lambda p,f,c,i:{'isoforms':{'canonical':p,'other':1-p},'args':(p,f,c,i)})
    for p in [0,1]:
        for c in [0,1]:
            for i in [0,1]:assert m.safe_isoform_distribution(p,cryptic_strength=c,intron_retention=i)['args']==(p,True,c,i)
    for key in ['psi','cryptic_strength','intron_retention']:
        for x in [-1e-9,1+1e-9,-.001,1.001]:
            kw={'psi':.5,'cryptic_strength':.5,'intron_retention':.5};kw[key]=x
            with pytest.raises(ValueError):m.safe_isoform_distribution(**kw)
    monkeypatch.setattr(m.core,'active_learning',lambda c:c)
    for p in [0,1]:assert m.safe_active_learning([{'probability':p,'impact':0}])
    for x in [-1e-9,1+1e-9]:
        with pytest.raises(ValueError):m.safe_active_learning([{'probability':x}])
    monkeypatch.setattr(m.core,'intervention_simulation',lambda w,a,s:(w,a,s))
    assert m.safe_intervention_simulation(0,1,[{'psi_shift':-1,'offtarget_risk':0}])==(0,1,[{'psi_shift':-1,'offtarget_risk':0}])
    assert m.safe_intervention_simulation(1,0,[{'psi_shift':1,'offtarget_risk':1}])==(1,0,[{'psi_shift':1,'offtarget_risk':1}])
    for key in ['wild_psi','aberrant_psi','psi_shift','offtarget_risk']:
        lo=-1 if key=='psi_shift' else 0
        for x in [lo-1e-9,1+1e-9]:
            w,a=.5,.5;s={'psi_shift':0,'offtarget_risk':.5}
            if key=='wild_psi':w=x
            elif key=='aberrant_psi':a=x
            else:s[key]=x
            with pytest.raises(ValueError):m.safe_intervention_simulation(w,a,[s])

def test_zero_index_and_exon_calibration_caps(monkeypatch):
    monkeypatch.setattr(m.core,'variant_at',lambda s,i,b,*a:i)
    assert m.safe_variant_at('AC',0,'G')==0
    with pytest.raises(ValueError):m.safe_variant_at('AC',-1,'G')
    monkeypatch.setattr(m.core,'branchpoint_variant_effect',lambda s,i,b:i)
    assert m.safe_branchpoint_variant_effect('A'*60,0,'G')==0
    with pytest.raises(ValueError):m.safe_branchpoint_variant_effect('A'*60,-1,'G')
    for n in [1,10**9]:
        r=m.safe_exon_inclusion(0,0,{'exon_definition_support':.25},calibration_n=n)
        radius=1.96*.5/math.sqrt(n)
        assert r['interval95']==pytest.approx([max(0,.5-radius),min(1,.5+radius)])
    for n in [0,10**9+1]:
        with pytest.raises(ValueError):m.safe_exon_inclusion(0,0,{'exon_definition_support':.25},calibration_n=n)

def test_isoform_optional_defaults_forward(monkeypatch):
    monkeypatch.setattr(m.core,'isoform_distribution',lambda p,f,c,i:{'isoforms':{'a':1},'args':(p,f,c,i)})
    assert m.safe_isoform_distribution(.5)['args']==(.5,True,0,.05)

def test_probability_sum_tolerance_neighbors(monkeypatch):
    # Binary64 cannot represent1+1e-9 exactly. Adjacent sums bracket it.
    for total,accepted in [(math.nextafter(1+1e-9,1),True),(1+1e-9,False)]:
        monkeypatch.setattr(m.core,'isoform_distribution',lambda *a:{'isoforms':{'a':total}})
        if accepted:assert m.safe_isoform_distribution(.5)['isoforms']['a']==total
        else:
            with pytest.raises(ValueError):m.safe_isoform_distribution(.5)

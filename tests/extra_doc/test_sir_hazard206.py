import math
import pytest
from sugarcode.extra_doc.sir_hazard206 import simulate


def test_independent_two_step_hazard_reference_synchronous_old_state_and_units():
    r=simulate(80,15,5,.4,.2,.5,2)
    assert r['population']==100 and len(r['curve'])==3
    s,i,recovered=80,15,5
    for k in (1,2):
        infections=s*(1-math.exp(-.4*i/100*.5));recoveries=i*(1-math.exp(-.2*.5))
        s-=infections;i+=infections-recoveries;recovered+=recoveries
        row=r['curve'][k]
        assert row==pytest.approx(dict(time=k*.5,susceptible=s,infected=i,recovered=recovered,new_infections=infections,new_recoveries=recoveries))
    assert not r['real_epidemic_forecast_verified'] and not r['parameters_fitted'] and r['external_effects']==[]


def test_extreme_rates_positivity_mass_and_no_same_step_recovery_of_new_infected():
    r=simulate(99,1,0,1000,1000,10,1)['curve'][1]
    assert r['new_recoveries']==1 and r['new_infections']==99
    assert r['susceptible']==0 and r['infected']==99 and r['recovered']==1
    for row in simulate(900000,90000,10000,1000,999,10,1000)['curve']:
        assert min(row[k] for k in ('susceptible','infected','recovered'))>=0
        assert sum(row[k] for k in ('susceptible','infected','recovered'))==pytest.approx(1000000,abs=1e-7)


def test_zero_rates_infected_and_all_recovered_states():
    for compartments in ((80,15,5),(100,0,0),(0,0,100)):
        r=simulate(*compartments,0,0,1,2)
        for row in r['curve']:
            assert [row[k] for k in ('susceptible','infected','recovered')]==list(compartments)


@pytest.mark.parametrize('steps',[0,1,999,1000,1001,-1,True,1.0,'1'])
def test_step_boundaries(steps):
    if type(steps) is int and 0<=steps<=1000:assert len(simulate(1,0,0,1,1,1,steps)['curve'])==steps+1
    else:
        with pytest.raises(ValueError,match='^strict integer steps 0..1000$'):simulate(1,0,0,1,1,1,steps)


def test_all_numerical_caps_types_exact_refusals():
    base=[1,1,1,1,1,1,1]
    for index,field,low,high in ((0,'compartment',0,1000000),(1,'compartment',0,1000000),(2,'compartment',0,1000000),(3,'beta',0,1000),(4,'gamma',0,1000),(5,'dt',1e-6,10)):
        for edge in (low,high,float(high)):
            args=list(base);args[index]=edge
            if index<3 and edge==1000000:args[(index+1)%3]=0;args[(index+2)%3]=0
            simulate(*args)
        for bad in (True,'1',None,low-1e-7,high+1,float('nan'),float('inf')):
            args=list(base);args[index]=bad
            with pytest.raises(ValueError,match='^strict finite bounded '+field+'$'):simulate(*args)
    for compartments in ((0,0,0),(1000000,1,0)):
        with pytest.raises(ValueError,match='^positive total population at most 1000000$'):simulate(*compartments,1,1,1,1)


def test_350_independent_high_precision_decimal_two_step_oracles():
    from decimal import Decimal as D,localcontext
    from random import Random
    rng=Random(206)
    with localcontext() as c:
        c.prec=60
        for _ in range(350):
            s=D(rng.randrange(1,100));i=D(rng.randrange(1,50));r=D(rng.randrange(50));n=s+i+r;b=D(rng.randrange(1,10))/10;g=D(rng.randrange(1,10))/10;h=D(rng.randrange(1,10))/10
            result=simulate(float(s),float(i),float(r),float(b),float(g),float(h),2)
            for k in (1,2):
                infection=s*(1-(-b*i*h/n).exp());recovery=i*(1-(-g*h).exp())
                s=s-infection;i=i+infection-recovery;r=r+recovery;row=result['curve'][k]
                assert [row[t] for t in ('susceptible','infected','recovered','new_infections','new_recoveries')]==pytest.approx(list(map(float,(s,i,r,infection,recovery))),abs=1e-10)
                assert row['time']==pytest.approx(float(k*h))


def test_huge_integer_all_input_refusals_and_literal_assumptions_units():
    for index,field in ((0,'compartment'),(1,'compartment'),(2,'compartment'),(3,'beta'),(4,'gamma'),(5,'dt')):
        for bad in (10**400,-10**400):
            a=[1,1,1,1,1,1,1];a[index]=bad
            with pytest.raises(ValueError,match='^strict finite bounded '+field+'$'):simulate(*a)
    r=simulate(1,1,1,1,1,1,0)
    assert r['curve']==[dict(time=0.0,susceptible=1.0,infected=1.0,recovered=1.0,new_infections=0.0,new_recoveries=0.0)]
    assert r['units']=='compartment counts; beta/gamma inverse time; dt time units'
    assert r['method']=='synchronous exponential hazard flows, discrete approximation, not exact SIR ODE solution'
    assert r['assumptions']==['closed homogeneous population, no births/deaths/reinfection','supplied rates constant; mixing and parameter truth unverified']

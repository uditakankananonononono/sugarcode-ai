import copy
import pytest
from sugarcode.extra_doc.fcfs_exact209 import simulate


def fixture():return [dict(id=x,arrival=a,service=s) for x,a,s in [('c',1,2),('b',0,1),('a',0,4),('d',2,1)]]


def test_independent_two_server_fcfs_events_wait_units_and_no_mutation():
    rows=fixture();before=copy.deepcopy(rows);r=simulate(rows,2)
    assert r['jobs']==[
        dict(id='a',server=0,arrival_fraction='0',start_fraction='0',completion_fraction='4',wait_fraction='0',sojourn_fraction='4'),
        dict(id='b',server=1,arrival_fraction='0',start_fraction='0',completion_fraction='1',wait_fraction='0',sojourn_fraction='1'),
        dict(id='c',server=1,arrival_fraction='1',start_fraction='1',completion_fraction='3',wait_fraction='0',sojourn_fraction='2'),
        dict(id='d',server=1,arrival_fraction='2',start_fraction='3',completion_fraction='4',wait_fraction='1',sojourn_fraction='2')]
    assert r['final_clock_fraction']=='4' and r['mean_wait_fraction']=='1/4' and r['mean_sojourn_fraction']=='9/4'
    assert r['aggregate_server_utilization_fraction']=='1' and r['time_average_queue_length_fraction']=='1/4'
    assert rows==before and simulate(rows[::-1],2)==r and not r['real_queue_forecast_verified'] and r['external_effects']==[]


def test_single_server_idle_gaps_fractional_times_and_zero_duration():
    r=simulate([dict(id='a',arrival=.5,service=.2),dict(id='b',arrival=.6,service=.4)],1)
    assert r['jobs'][1]['start_fraction']=='7/10' and r['jobs'][1]['wait_fraction']=='1/10'
    assert r['aggregate_server_utilization_fraction']=='6/11' and r['time_average_queue_length_fraction']=='1/11'
    r=simulate([dict(id='a',arrival=0,service=0)],1)
    assert r['final_clock_fraction']=='0' and r['aggregate_server_utilization_fraction'] is None and r['time_average_queue_length_fraction'] is None


@pytest.mark.parametrize('n',[0,1,999,1000,1001])
def test_job_caps(n):
    rows=[dict(id=str(i),arrival=0,service=1) for i in range(n)]
    if 1<=n<=1000:assert len(simulate(rows,1)['jobs'])==n
    else:
        with pytest.raises(ValueError,match='^1..1000 queue jobs before scan$'):simulate(rows,1)
@pytest.mark.parametrize('n',[0,1,19,20,21,True,1.0,'1'])
def test_server_caps(n):
    if type(n) is int and 1<=n<=20:simulate(fixture(),n)
    else:
        with pytest.raises(ValueError,match='^strict integer servers 1..20$'):simulate(fixture(),n)
@pytest.mark.parametrize('v',[0,1000000,1000000.0])
def test_time_edges(v):simulate([dict(id='a',arrival=v,service=v)],1)
@pytest.mark.parametrize('n',[1,119,120,121])
def test_id_edges(n):
    rows=[dict(id='x'*n,arrival=0,service=1)]
    if n<=120:simulate(rows,1)
    else:
        with pytest.raises(ValueError,match='^bounded nonblank job id$'):simulate(rows,1)


def test_type_schema_duplicate_and_time_refusals():
    for bad in (True,'1',None,-1,1000001,float('nan'),float('inf')):
        for field in ('arrival','service'):
            row=dict(id='a',arrival=0,service=1);row[field]=bad
            with pytest.raises(ValueError,match='^strict finite arrival/service within 0..1000000$'):simulate([row],1)
    for bad in ('',' ','\t\n',True,None):
        with pytest.raises(ValueError,match='^bounded nonblank job id$'):simulate([dict(id=bad,arrival=0,service=1)],1)
    for bad in ((),None,True):
        with pytest.raises(ValueError,match='^1..1000 queue jobs before scan$'):simulate(bad,1)
    for bad in ({'id':'a','arrival':0,'wrong':1},[],None):
        with pytest.raises(ValueError,match='^exact id/arrival/service fields$'):simulate([bad],1)
    with pytest.raises(ValueError,match='^distinct job ids$'):simulate([dict(id='a',arrival=0,service=1)]*2,1)


def test_unequal_multi_server_finish_horizon_and_idle_capacity_reference():
    rows=[dict(id='a',arrival=0,service=4),dict(id='b',arrival=0,service=1)]
    r=simulate(rows,2)
    assert r['final_clock_fraction']=='4'
    assert r['aggregate_server_utilization_fraction']=='5/8'
    assert r['time_average_queue_length_fraction']=='0'
    assert r['mean_sojourn_fraction']=='5/2' and r['mean_wait_fraction']=='0'
    assert [row['completion_fraction'] for row in r['jobs']]==['4','1']


def test_500_independent_linear_server_scan_oracles():
    from fractions import Fraction as F
    from random import Random
    rng=Random(209)
    for _ in range(500):
        n=rng.randrange(1,20);servers=rng.randrange(1,5);rows=[dict(id=str(j),arrival=rng.randrange(15)/10,service=rng.randrange(10)/10) for j in range(n)];free=[F(0)]*servers;expected=[]
        for row in sorted(rows,key=lambda r:(F(str(r['arrival'])),r['id'])):
            arrival=F(str(row['arrival']));service=F(str(row['service']));server=free.index(min(free));start=max(arrival,free[server]);finish=start+service;free[server]=finish
            expected.append(dict(id=row['id'],server=server,arrival_fraction=str(arrival),start_fraction=str(start),completion_fraction=str(finish),wait_fraction=str(start-arrival),sojourn_fraction=str(finish-arrival)))
        r=simulate(rows,servers);assert r['jobs']==expected
        wait=sum(F(row['wait_fraction']) for row in expected);horizon=max(free);service=sum(F(str(row['service'])) for row in rows)
        assert F(r['total_wait_fraction'])==wait and F(r['mean_wait_fraction'])==wait/n and F(r['mean_sojourn_fraction'])==(wait+service)/n
        assert F(r['final_clock_fraction'])==horizon
        assert r['aggregate_server_utilization_fraction']==(str(service/(servers*horizon)) if horizon else None)
        assert r['time_average_queue_length_fraction']==(str(wait/horizon) if horizon else None)


def test_huge_time_refusals_and_literal_contracts():
    for field in ('arrival','service'):
        for value in (10**400,-10**400):
            row=dict(id='a',arrival=0,service=1);row[field]=value
            with pytest.raises(ValueError,match='^strict finite arrival/service within 0..1000000$'):simulate([row],1)
    r=simulate(fixture(),2)
    assert r['discipline']=='FCFS arrivals; equal arrival ties ascending id; equal available time ties lowest server index'
    assert r['observation_window']=='time zero through final completion, including idle gaps'
    assert r['units']=='arrival/service/wait/clock in supplied time units; utilization/queue length dimensionless'
    assert not r['stochastic_process_fitted']

import inspect
import os
import subprocess
import sys
import numpy as np
import pytest
from sugarcode.modules.prime_design import partition_seed_gate as module


def shape(fn):
    return [(p.name,p.kind,p.default) for p in inspect.signature(fn).parameters.values()]


def test_signature():
    assert shape(module.plan_pridict2_partition)==shape(module.assay_data.plan_pridict2_partition)


@pytest.mark.parametrize('mode',['positional','keyword'])
def test_all_values_forwarded(mode,monkeypatch):
    sig=inspect.signature(module.assay_data.plan_pridict2_partition)
    vals={'assay':object(),'cell':object(),'test_fold':object(),'validation_fraction':object(),'seed':np.int64(77)}
    calls=[]
    def capture(*a,**k):
        bound=sig.bind(*a,**k).arguments;calls.append(bound);return bound
    monkeypatch.setattr(module.assay_data,'plan_pridict2_partition',capture)
    if mode=='positional':result=module.plan_pridict2_partition(vals['assay'],vals['cell'],vals['test_fold'],validation_fraction=vals['validation_fraction'],seed=vals['seed'])
    else:result=module.plan_pridict2_partition(**vals)
    assert len(calls)==1
    for name in vals:
        if name=='seed':assert type(result[name]) is int and result[name]==77
        else: assert result[name] is vals[name]


def test_exact_invalid_seed_preflight(monkeypatch):
    def forbidden(*a,**k):raise AssertionError('partition implementation called')
    monkeypatch.setattr(module.assay_data,'plan_pridict2_partition',forbidden)
    for seed in (True,False,np.bool_(True),None,1.,'1',[],{}):
        with pytest.raises(TypeError,match='^seed must be an integer$'):module.plan_pridict2_partition(None,None,None,seed=seed)
    for seed in (-1,2**63,10**1000,np.uint64(2**63)):
        with pytest.raises(ValueError,match='^seed must be between 0 and 9223372036854775807$'):module.plan_pridict2_partition(None,None,None,seed=seed)


def test_edges_and_default_export_dispatch(monkeypatch):
    sig=inspect.signature(module.assay_data.plan_pridict2_partition)
    calls=[]
    def capture(*a,**k):
        bound=sig.bind(*a,**k);bound.apply_defaults();calls.append(bound.arguments);return bound.arguments
    monkeypatch.setattr(module.assay_data,'plan_pridict2_partition',capture)
    for seed in (0,2**63-1,np.int64(0),np.int64(2**63-1),np.uint64(2**63-1)):
        r=module.plan_pridict2_partition('fixture','HEK',0,seed=seed)
        assert type(r['seed']) is int and r['seed']==int(seed)
    assert module.plan_pridict2_partition('fixture','HEK',0)=={'assay':'fixture','cell':'HEK','test_fold':0,'validation_fraction':.1,'seed':42}


def test_deep_list_subprocess():
    code="""from sugarcode.modules.prime_design import partition_seed_gate as m
s=0
for _ in range(100000):s=[s]
def forbidden(*a,**k):raise AssertionError('implementation called')
m.assay_data.plan_pridict2_partition=forbidden
try:m.plan_pridict2_partition(None,None,None,seed=s)
except TypeError as e:assert str(e)=='seed must be an integer'
else:raise AssertionError('nested list accepted')
print('refused')
"""
    p=subprocess.run([sys.executable,'-B','-c',code],capture_output=True,text=True,timeout=15,env={**os.environ,'PYTHONPATH':'src'})
    assert p.returncode==0,(p.returncode,p.stderr[-1000:])
    assert p.stdout.strip()=='refused'


def fixture():
    return {'records':[{'seq_id':'r'+str(i),'grp_id':'g'+str(i),'outcomes':{'HEK':[1.,0.,0.]},'test_folds':{'HEK':i%5}} for i in range(12)]}


@pytest.mark.parametrize('seed',[0,42,2**63-1])
def test_actual_partition_unchanged(seed):
    import copy
    assay=fixture();before=copy.deepcopy(assay)
    expected=module.assay_data.plan_pridict2_partition(assay,'HEK',0,seed=seed)
    assert module.plan_pridict2_partition(assay,'HEK',0,seed=seed)==expected
    assert module.plan_pridict2_partition(assay,'HEK',0,seed=np.int64(seed))==expected
    assert assay==before


def test_actual_default_unchanged():
    assay=fixture()
    assert module.plan_pridict2_partition(assay,'HEK',0)==module.assay_data.plan_pridict2_partition(assay,'HEK',0)


def test_partition_independent_oracle():
    # Literal 12-row fixture: test groups are g0,g5,g10; nine others compete
    # for one validation group by salted digest. No implementation internals.
    import hashlib
    rows=fixture()
    for seed in (0,42,2**63-1):
        groups=['g'+str(i) for i in range(12) if i%5!=0]
        winner=min(groups,key=lambda g:(hashlib.sha256((str(seed)+':'+g).encode()).digest(),g))
        validation=int(winner[1:])
        r=module.plan_pridict2_partition(rows,'HEK',0,seed=seed)
        assert r['test']==[0,5,10]
        assert r['validation']==[validation]
        assert r['train']==[i for i in range(12) if i%5!=0 and i!=validation]
        assert r['non_test_group_count']==9 and r['validation_group_count']==1
        assert r['fitting_permitted'] is False
        assert r['reuse_status']=='DATA_REUSE_UNVERIFIED: fitting/redistribution gate CLOSED'

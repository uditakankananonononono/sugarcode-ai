import copy
import pytest
from sugarcode.extra_doc.streaming_sgd229 import train


def args():return [[[dict(features=[1,2],target=3),dict(features=[-2,1],target=-1)]],[0,0],.5,100]


def test_independent_asymmetric_hand_gradient_effective_rate_and_losses():
    a=args();before=copy.deepcopy(a);r=train(*a)
    assert r['weights']==pytest.approx([.25,.25])
    assert r['batch_history'][0]['gradient']==[-2.5,-2.5]
    assert r['batch_history'][0]['effective_rate']==.1
    assert r['batch_history'][0]['loss_before']==2.5 and r['batch_history'][0]['loss_after']==1.40625
    assert r['batches_used']==1 and r['samples_seen']==2 and r['stream_exhausted_observed'] and r['stream_fully_consumed_claimed']
    assert r['retained_sample_cap']==128 and not r['full_dataset_loss_computed'] and r['external_effects']==[] and a==before


def test_stream_budget_never_prefetches_and_batches_are_not_retained():
    def stream():
        yield [dict(features=[1],target=2)]
        raise AssertionError('must not read beyond configured budget')
    r=train(stream(),[0],1,1)
    assert r['weights']==[2] and r['batches_used']==1 and not r['stream_fully_consumed_claimed']
    assert r['method']=='streaming_minibatch_SGD_trace_normalized_rate'
    assert r['loss_definition']=='mean half squared prediction error per batch; no intercept unless feature supplied'


def test_300_independent_decimal_minibatch_sequences():
    from decimal import Decimal as D
    from random import Random
    rng=Random(229)
    for _ in range(300):
        w=[D(rng.randrange(-3,4)),D(rng.randrange(-3,4))];initial=list(map(float,w));rate=D('0.5');batches=[];expected=[]
        for k in range(rng.randrange(1,5)):
            batch=[dict(features=[rng.randrange(-3,4),rng.randrange(-3,4)],target=rng.randrange(-3,4)) for j in range(rng.randrange(1,6))];batches.append(batch)
            n=D(len(batch));res=[sum(z*D(f) for z,f in zip(w,s['features']))-D(s['target']) for s in batch]
            g=[sum(r*D(s['features'][j]) for r,s in zip(res,batch))/n for j in range(2)]
            bound=sum(sum(D(v)**2 for v in s['features']) for s in batch)/n;step=rate/max(D(1),bound)
            before=sum(r*r for r in res)/(2*n);w=[z-step*t for z,t in zip(w,g)]
            after=sum((sum(z*D(f) for z,f in zip(w,s['features']))-D(s['target']))**2 for s in batch)/(2*n)
            expected.append((g,step,before,after))
        r=train(iter(batches),initial,.5,100)
        assert r['weights']==pytest.approx(list(map(float,w)),abs=1e-12)
        for got,(g,step,before,after) in zip(r['batch_history'],expected):
            assert got['gradient']==pytest.approx(list(map(float,g)),abs=1e-12)
            assert got['effective_rate']==pytest.approx(float(step),rel=1e-12)
            assert got['loss_before']==pytest.approx(float(before),abs=1e-12) and got['loss_after']==pytest.approx(float(after),abs=1e-12)
            assert got['loss_after']<=got['loss_before']+1e-12


def test_all_caps_and_valid_numeric_boundaries_nonbool():
    for d in (1,7,8):
        for n in (1,127,128):
            batch=[dict(features=[0]*d,target=1000)]*n
            assert train([batch],[0]*d,1,1)['samples_seen']==n
    for v in (-1000,1000,-1000.0,1000.0):train([[dict(features=[v],target=v)]],[v],1,1)
    for limit in (1,99,100):
        r=train(([dict(features=[0],target=0)] for _ in range(limit)),[0],1,limit)
        assert r['batches_used']==limit and not r['stream_exhausted_observed']
    assert train([[dict(features=[0],target=0)]],[0],1e-15,1)['weights']==[0]


def test_strict_staged_refusals_and_mixed_nonbool_fixtures():
    for limit in (True,1.0,0,101,None):
        a=args();a[3]=limit
        with pytest.raises(ValueError,match='^strict max batches 1..100$'):train(*a)
    for rate in (True,'1',None,0,-.01,1.01,float('nan'),float('inf')):
        a=args();a[2]=rate
        with pytest.raises(ValueError,match=r'^strict finite learning rate \(0,1\]$'):train(*a)
    for init in (None,(),[],[0]*9,True):
        a=args();a[1]=init
        with pytest.raises(ValueError,match='^1..8 initial weights before scan$'):train(*a)
    for batch in (None,(),[],True,[dict(features=[0,0],target=0)]*129):
        a=args();a[0]=[batch]
        with pytest.raises(ValueError,match='^1..128 samples per batch before scan$'):train(*a)
    for s in ({},[],dict(features=[0,0],target=0,extra=1)):
        a=args();a[0][0][0]=s
        with pytest.raises(ValueError,match='^exact features/target sample fields$'):train(*a)
    for f in (None,(),[],[0],[0]*3):
        a=args();a[0][0][0]['features']=f
        with pytest.raises(ValueError,match='^one feature per weight$'):train(*a)
    for bad in (True,None,'1',-1000.01,1000.01,float('nan'),float('inf')):
        for j in (0,1):
            for index in (0,1):
                a=args()
                if index:a[1][j]=bad
                else:a[0][0][0]['features'][j]=bad
                with pytest.raises(ValueError,match='^strict finite regression value within -1000..1000$'):train(*a)
        a=args();a[0][0][0]['target']=bad
        with pytest.raises(ValueError,match='^strict finite regression value within -1000..1000$'):train(*a)
    for bad in (None,True,1):
        a=args();a[0]=bad
        with pytest.raises(ValueError,match='^iterable batch stream required$'):train(*a)
    with pytest.raises(ValueError,match='^at least one training batch required$'):train(iter([]),[0],1,1)


def test_one_nonfinite_iterate_fault_refused(monkeypatch):
    import sugarcode.extra_doc.streaming_sgd229 as m
    original=m.math.isfinite;count=[0]
    def finite(value):
        count[0]+=1
        return False if count[0]==10 else original(value)
    monkeypatch.setattr(m.math,'isfinite',finite)
    with pytest.raises(ValueError,match='^finite numerical weights required$'):train(*args())


@pytest.mark.parametrize('huge',[10**400,-10**400])
def test_huge_integer_refusals_before_float_conversion(huge):
    a=args();a[2]=huge
    with pytest.raises(ValueError,match=r'^strict finite learning rate \(0,1\]$'):train(*a)
    for j in (0,1):
        a=args();a[1][j]=huge
        with pytest.raises(ValueError,match='^strict finite regression value within -1000..1000$'):train(*a)
        a=args();a[0][0][0]['features'][j]=huge
        with pytest.raises(ValueError,match='^strict finite regression value within -1000..1000$'):train(*a)
    a=args();a[0][0][0]['target']=huge
    with pytest.raises(ValueError,match='^strict finite regression value within -1000..1000$'):train(*a)


@pytest.mark.parametrize('size',[1,3,7])
def test_batch_samples_different_from_feature_width_and_exact_index_key(size):
    batches=[[dict(features=[1,2],target=0)]*size,[dict(features=[2,1],target=1)]*(size+1)]
    r=train(batches,[0,0],.5,2)
    assert [h['samples'] for h in r['batch_history']]==[size,size+1]
    assert [h['batch_index'] for h in r['batch_history']]==[0,1]
    assert [set(h) for h in r['batch_history']]==[{'batch_index','samples','gradient','effective_rate','loss_before','loss_after'}]*2


def test_finite_weight_guard_every_coordinate_fault(monkeypatch):
    import sugarcode.extra_doc.streaming_sgd229 as m
    original=m.math.isfinite
    for fault_at in (10,11):
        counter=[0]
        def finite(v):
            counter[0]+=1
            return False if counter[0]==fault_at else original(v)
        with monkeypatch.context() as patch:
            patch.setattr(m.math,'isfinite',finite)
            with pytest.raises(ValueError,match='^finite numerical weights required$'):train(*args())

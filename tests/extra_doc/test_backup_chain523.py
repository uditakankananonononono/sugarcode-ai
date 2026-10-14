import random,copy
import pytest
from sugarcode.extra_doc.backup_chain523 import recover


def reference(bs,t):
    valid={};pending=set(range(len(bs)))
    while pending:
        done=[]
        for i in pending:
            ts,p,size,ok=bs[i]
            if p is not None and p not in valid:continue
            valid[i]=None if not ok or (p is not None and valid[p] is None) else (i,) if p is None else valid[p]+(i,)
            done.append(i)
        pending.difference_update(done)
    candidates=[]
    for i in range(len(bs)):
        if valid[i] is not None and bs[i][0]<=t:candidates.append((bs[i][0],sum(bs[j][2] for j in valid[i]),valid[i]))
    if candidates:
        latest=max(a[0] for a in candidates);ts,size,chain=min((a for a in candidates if a[0]==latest),key=lambda a:(a[1],a[2]));best=dict(timestamp=ts,chain=chain,bytes_to_read=size,data_loss_window=t-ts)
    else:best=None
    return dict(recoverable_chains=[valid[i] for i in range(len(bs))],best=best,data_protected_externally=False)


def test_reference():
    rng=random.Random(523)
    for _ in range(500):
        bs=[]
        for i in range(rng.randint(0,64)):
            ps=[j for j in range(i) if bs[j][0]<i];bs.append((i,rng.choice([None]+ps),rng.randint(0,1000),rng.choice([True,False])))
        t=rng.randint(0,70);b=copy.deepcopy(bs);assert recover(bs,t)==reference(bs,t);assert bs==b
    bs=[(0,None,5,True),(1,0,3,True),(1,None,2,True),(2,1,0,False)]
    assert recover(bs,1)['best']==dict(timestamp=1,chain=(2,),bytes_to_read=2,data_loss_window=0)
    assert recover([(1,None,0,True),(1,None,0,True)],1)['best']['chain']==(0,)
    assert recover([(1,1,0,True),(0,None,0,True)],1)==reference([(1,1,0,True),(0,None,0,True)],1)


def test_caps():
    for t in (0,10**9):
        for size in (0,10**12):
            bs=[(i,None if i==0 else i-1,size,True) for i in range(64)];assert recover(bs,t)==reference(bs,t)
    assert recover([],0)==reference([],0)
    assert recover([(10**9,None,0,True)],0)['best'] is None


@pytest.mark.parametrize('bad',[True,1.0,'0',None])
def test_slot_types(bad):
    for i in (0,2):
        row=[0,None,0,True];row[i]=bad
        with pytest.raises(ValueError):recover([tuple(row)],0)
    if bad is not None:
        with pytest.raises(ValueError):recover([(0,bad,0,True)],0)
    with pytest.raises(ValueError):recover([],bad)


@pytest.mark.parametrize('bad',[0,1,None,'True',1.0])
def test_availability_type(bad):
    with pytest.raises(ValueError):recover([(0,None,0,bad)],0)


@pytest.mark.parametrize('bs,t',[(None,0),([(0,None,0,True)]*65,0),([()],0),([(0,)],0),([(0,None,0)],0),([(0,None,0,True,0)],0),([[0,None,0,True]],0),([(-1,None,0,True)],0),([(10**9+1,None,0,True)],0),([(0,-1,0,True)],0),([(0,1,0,True)],0),([(0,None,-1,True)],0),([(0,None,10**12+1,True)],0),([], -1),([],10**9+1),([(0,0,0,True)],0),([(0,1,0,True),(0,0,0,True)],0),([(0,1,0,True),(1,None,0,True)],0)])
def test_refusals(bs,t):
    with pytest.raises(ValueError):recover(bs,t)


class ListSubclass523(list):
    pass


class TupleSubclass523(tuple):
    pass


class IntSubclass523(int):
    pass


@pytest.mark.parametrize('bad', [[1, 0, 0, True], TupleSubclass523((1, 0, 0, True))])
def test_row_container_exact_message_nonfirst(bad):
    with pytest.raises(ValueError, match='^backup timestamp parent bytes available quadruple$'):
        recover([(0, None, 0, True), bad], 1)


def test_negative_parent_exact_message_nonfirst():
    with pytest.raises(ValueError, match='^parent None or valid integer index$'):
        recover([(0, None, 0, True), (1, -1, 0, True)], 1)


@pytest.mark.parametrize('slot,message', [
    (0, '^timestamp integer0..1000000000$'),
    (1, '^parent None or valid integer index$'),
    (2, '^bytes integer0..1000000000000$'),
    (3, '^available must be bool$'),
])
def test_scalar_subclass_exact_messages_nonfirst(slot, message):
    row = [1, 0, 0, True]
    row[slot] = IntSubclass523(row[slot])
    with pytest.raises(ValueError, match=message):
        recover([(0, None, 0, True), tuple(row)], 1)


def test_outer_container_and_requested_subclasses_exact_messages():
    with pytest.raises(ValueError, match='^0..64 backups before scan$'):
        recover(ListSubclass523([(0, None, 0, True)]), 0)
    with pytest.raises(ValueError, match='^requested integer0..1000000000$'):
        recover([(0, None, 0, True)], IntSubclass523(0))


def test_triple_row_exact_message_nonfirst():
    with pytest.raises(ValueError, match='^backup timestamp parent bytes available quadruple$'):
        recover([(0, None, 0, True), (1, 0, 0)], 1)


@pytest.mark.parametrize('timestamp', [0, 1])
def test_parent_timestamp_exact_message_nonfirst(timestamp):
    with pytest.raises(ValueError, match='^parent timestamp must be strictly earlier$'):
        recover([(1, None, 0, True), (timestamp, 0, 0, True)], 1)

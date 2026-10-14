import copy
import pytest
from sugarcode.extra_doc.pareto_layers219 import identify


def test_literal_mixed_direction_layers_duplicate_vector_witness_and_no_mutation():
    rows=[dict(id=k,values=v) for k,v in [('a',[1,5]),('b',[2,6]),('c',[2,4]),('d',[3,3]),('e',[1,5])]];before=copy.deepcopy(rows);r=identify(rows,['min','max'])
    assert r['frontier_ids']==['a','b','e'] and r['layers']==[['a','b','e'],['c'],['d']]
    assert r['rank']==dict(a=0,b=0,c=1,d=2,e=0) and r['dominating_ids']==dict(a=[],b=[],c=['a','b','e'],d=['a','b','c','e'],e=[])
    assert r['directions']==['min','max'] and rows==before and not r['global_frontier_verified'] and r['external_effects']==[]
    assert r['definition']=='weakly no worse on every objective and strictly better on at least one; equal vectors do not dominate' and r['frontier_scope']=='only supplied feasible option menu'


def test_600_independent_pairwise_signed_difference_rank_oracles():
    from random import Random
    rng=Random(219)
    for _ in range(600):
        n=rng.randrange(1,12);d=rng.randrange(1,5);ways=[rng.choice(['min','max']) for j in range(d)];vs=[[rng.randrange(-5,6) for j in range(d)] for i in range(n)];rows=[dict(id=str(i),values=v) for i,v in enumerate(vs)];edges=[]
        for i in range(n):
            for j in range(n):
                diffs=[(vs[i][k]-vs[j][k])*(1 if ways[k]=='min' else -1) for k in range(d)]
                if max(diffs)<=0 and min(diffs)<0:edges.append((i,j))
        ranks={};todo=list(range(n));layers=[]
        while todo:
            current=[j for j in todo if all(i not in todo for i,k in edges if k==j)];layers.append(sorted(str(j) for j in current))
            for j in current:ranks[str(j)]=len(layers)-1;todo.remove(j)
        r=identify(rows,ways);assert r['layers']==layers and r['rank']==ranks
        assert r['dominating_ids']=={str(j):sorted(str(i) for i,k in edges if k==j) for j in range(n)}


def test_full_caps_numeric_edges_and_strict_all_refusals():
    for n in (1,99,100):
        for d in (1,7,8):assert len(identify([dict(id=str(i),values=[0]*d) for i in range(n)],['min']*d)['frontier_ids'])==n
    for v in (-1000000,1000000,-1000000.0,1000000.0):identify([dict(id='x'*120,values=[v])],['max'])
    for dirs in (None,(),[],[0]*9):
        with pytest.raises(ValueError,match='^1..8 Pareto directions before scan$'):identify([],dirs)
    for bad in (True,None,'bad'):
        for j in (0,1):
            dirs=['min','max'];dirs[j]=bad
            with pytest.raises(ValueError,match='^Pareto direction min or max$'):identify([],dirs)
    for rows in (None,(),[],[{}]*101):
        with pytest.raises(ValueError,match='^1..100 Pareto options before scan$'):identify(rows,['min'])
    for row in ({},None,[],dict(id='a',values=[0],extra=1)):
        with pytest.raises(ValueError,match='^exact Pareto id/values fields$'):identify([row],['min'])
    for name in (True,None,'',' ','x'*121):
        with pytest.raises(ValueError,match='^unique nonblank Pareto ids 1..120$'):identify([dict(id=name,values=[0])],['min'])
    with pytest.raises(ValueError,match='^unique nonblank Pareto ids 1..120$'):identify([dict(id='a',values=[0])]*2,['min'])
    for raw in (None,(),[],[0,0]):
        with pytest.raises(ValueError,match='^one Pareto value per direction$'):identify([dict(id='a',values=raw)],['min'])
    for value in (True,None,'1',-1000000.01,1000000.01,10**400,-10**400,float('nan'),float('inf')):
        for j in (0,1):
            raw=[0,0];raw[j]=value
            with pytest.raises(ValueError,match='^strict finite Pareto value within -1000000..1000000$'):identify([dict(id='a',values=raw)],['min','max'])

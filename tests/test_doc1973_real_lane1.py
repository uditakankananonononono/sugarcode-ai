"""Standalone recursive exact output types and input/order regression pins."""
import pytest

def exact(got,expected):
    assert type(got) is type(expected)
    if type(expected) is bool:
        assert got is expected
    elif type(expected) is dict:
        assert list(got)==list(expected)
        for key in expected:exact(key,next(k for k in got if k==key));exact(got[key],expected[key])
    elif type(expected) in (list,tuple):
        assert len(got)==len(expected)
        for a,b in zip(got,expected):exact(a,b)
    else:
        assert got==expected

import random
from sugarcode.extra_doc.tree_minimax1973_real import evaluate
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass

def test_independent_recursive_oracle():
    rng=random.Random(1973)
    for _ in range(100):
        parents=[None]+[rng.randrange(i) for i in range(1,20)];children={i:[j for j,p in enumerate(parents) if p==i] for i in range(20)};scores=[None if children[i] else rng.randrange(-5,6) for i in range(20)];rows=[(str(i),None if p is None else str(p),scores[i]) for i,p in enumerate(parents)];computed={}
        def solve(i,maximize):
            if not children[i]:out=(scores[i],[str(i)])
            else:
                candidates=[solve(j,not maximize) for j in children[i]];target=sorted(x[0] for x in candidates)[-1 if maximize else 0];v,path=next(x for x in candidates if x[0]==target);out=(v,[str(i)]+path)
            computed[i]=out[0];return out
        value,path=solve(0,True)
        exact(evaluate(rows),{'value':value,'principal_branch':path,'node_values':[(str(i),computed[i]) for i in range(20)],'language_reasoning_inferred':False})

@pytest.mark.parametrize('rows,message',[
 *[(x,'rows must be exact list1..100') for x in (None,L([('a',None,0)]),(),[],[('a',None,0)]*101)],
 *[([x],'node must be exact id parent score tuple') for x in (['a',None,0],T(('a',None,0)),('a',None),('a',None,0,1))],
 *[([(x,None,0)],'IDs must be unique valid labels') for x in ('',' ',False,S('a'),'x'*81,'\u00a0')],
 ([('a',None,None),('a','a',0)],'IDs must be unique valid labels'),
 *[([('a',x,0)],'root parent must be None') for x in (False,'a',0)],
 *[([('a',None,None),('b',x,0)],'parent must be prior valid ID') for x in (False,None,S('a'),'unknown')],
 *[([('a',None,x)],'score must be None or exact int-1000..1000') for x in (False,True,I(1),1.0,-1001,1001)],
 ([('a',None,None)],'branch score must be None and leaf score integer'),
 ([('a',None,0),('b','a',1)],'branch score must be None and leaf score integer'),
 ([('a',None,None),('',False,False)],'IDs must be unique valid labels'),
 ([('a',None,None),('b','unknown',False)],'parent must be prior valid ID'),
])
def test_first_bad(rows,message):
    with pytest.raises(ValueError) as exc:evaluate(rows)
    assert str(exc.value)==message

@pytest.mark.parametrize('score',[-1000,1000])
def test_leaf_endpoints(score):
    exact(evaluate([('a',None,score)]),{'value':score,'principal_branch':['a'],'node_values':[('a',score)],'language_reasoning_inferred':False})

def test_minimax_ties_cap_ownership():
    rows=[('r',None,None),('a','r',None),('b','r',3),('c','a',4),('d','a',-1)]
    exact(evaluate(rows),{'value':3,'principal_branch':['r','b'],'node_values':[('r',3),('a',-1),('b',3),('c',4),('d',-1)],'language_reasoning_inferred':False})
    assert evaluate([('r',None,None),('a','r',1),('b','r',1)])['principal_branch']==['r','a']
    rows=[('x'*80,None,None)]+[(str(i),'x'*80,i) for i in range(99)];out=evaluate(rows);assert out['value']==98;out['principal_branch'].clear();assert len(rows)==100

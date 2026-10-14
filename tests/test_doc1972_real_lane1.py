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
from sugarcode.extra_doc.chain_trace1972_real import execute
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass

def test_independent_expression_tree_oracle():
    rng=random.Random(1972)
    for _ in range(100):
        initial=[('a',rng.randrange(-5,6)),('b',rng.randrange(-5,6))];trees={n:v for n,v in initial};steps=[];trace=[]
        def solve(t):
            if type(t) is int:return t
            op,l,r=t;a,b=solve(l),solve(r)
            return {'add':lambda:a+b,'subtract':lambda:a-b,'multiply':lambda:a*b}[op]()
        for i in range(8):
            op=rng.choice(['add','subtract','multiply']);l=rng.choice(list(trees));r=rng.choice(list(trees));n=str(i);tree=(op,trees[l],trees[r]);a,b=solve(trees[l]),solve(trees[r]);trees[n]=tree;steps.append((n,op,l,r));trace.append((n,op,a,b,solve(tree)))
        exact(execute(initial,steps),{'environment':[(n,solve(t)) for n,t in trees.items()],'trace':trace,'language_reasoning_inferred':False})

@pytest.mark.parametrize('initial,steps,message',[
 *[(x,[],'initial must be exact list1..20') for x in (None,L([('a',0)]),(),[],[(str(i),0) for i in range(21)])],
 *[([x],[],'initial row must be exact name value tuple') for x in (['a',0],T(('a',0)),('a',),('a',0,1))],
 *[([(x,0)],[],'names must be unique valid labels') for x in ('',' ',False,S('a'),'x'*81,'\u00a0')],
 ([('a',0),('a',0)],[],'names must be unique valid labels'),
 *[([('a',x)],[],'initial value must be exact int-1000..1000') for x in (False,True,I(1),1.0,-1001,1001)],
 *[([('a',0)],x,'steps must be exact list0..20') for x in (None,L(),(),[('b','add','a','a')]*21)],
 *[([('a',0)],[x],'step must be exact name operation left right tuple') for x in (['b','add','a','a'],T(('b','add','a','a')),('b','add','a'),('b','add','a','a',1))],
 ([('a',0)],[('a','add','a','a')],'names must be unique valid labels'),
 *[([('a',0)],[('b',x,'a','a')],'operation must be exact add subtract multiply string') for x in (False,S('add'),'divide','')],
 *[([('a',0)],[('b','add',x,'a')],'left must be previously defined valid name') for x in (False,S('a'),'unknown')],
 *[([('a',0)],[('b','add','a',x)],'right must be previously defined valid name') for x in (False,S('a'),'unknown')],
 ([('z',0),('',False)],[],'names must be unique valid labels'),
 ([('a',0)],[('b','add','a','a'),('c','add','unknown',False)],'left must be previously defined valid name'),
])
def test_first_bad(initial,steps,message):
    with pytest.raises(ValueError) as exc:execute(initial,steps)
    assert str(exc.value)==message

def test_caps_dependency_order_zero_steps_ownership():
    initial=[('x'*80,-1000),('\u200b',1000)]+[(str(i),0) for i in range(18)];steps=[('s'+str(i),'add','x'*80,'\u200b') for i in range(20)];out=execute(initial,steps);assert len(out['trace'])==20;out['environment'].clear();assert len(initial)==20
    exact(execute([('a',2)],[('b','multiply','a','a'),('c','subtract','b','a')]),{'environment':[('a',2),('b',4),('c',2)],'trace':[('b','multiply',2,2,4),('c','subtract',4,2,2)],'language_reasoning_inferred':False})
    exact(execute([('a',0)],[]),{'environment':[('a',0)],'trace':[],'language_reasoning_inferred':False})

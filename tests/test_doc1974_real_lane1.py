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
from itertools import permutations
from sugarcode.extra_doc.graph_path1974_real import best_path
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass

def test_independent_permutation_path_oracle():
    rng=random.Random(1974)
    for _ in range(100):
        ns=list('zabc');es=[(a,b,rng.randrange(5)) for a in ns for b in ns if a!=b and rng.randrange(2)];weights={(a,b):c for a,b,c in es};candidates=[]
        for length in range(3):
            for middle in permutations(['a','b'],length):
                p=('z',)+middle+('c',)
                if all((a,b) in weights for a,b in zip(p,p[1:])):candidates.append((sum(weights[(a,b)] for a,b in zip(p,p[1:])),len(p)-1,tuple(ns.index(n) for n in p),list(p)))
        best=min(candidates) if candidates else None
        exact(best_path(ns,es,'z','c'),{'path':None if best is None else best[3],'cost':None if best is None else best[0],'reasoning_validated':False})

@pytest.mark.parametrize('nodes',[None,L(['a']),(),[],list(map(str,range(9))),['a','a'],['a',''],['a',False],['a',S('b')]])
def test_nodes(nodes):
    with pytest.raises(ValueError) as exc:best_path(nodes,[],'a','a')
    assert str(exc.value)=='nodes must be exact list1..8 unique valid labels'

@pytest.mark.parametrize('slot',['start','goal'])
@pytest.mark.parametrize('x',[False,S('a'),'unknown',''])
def test_endpoints(slot,x):
    args={'start':'a','goal':'b'};args[slot]=x
    with pytest.raises(ValueError) as exc:best_path(['a','b'],[],**args)
    assert str(exc.value)==slot+' must be known valid label'

@pytest.mark.parametrize('es,message',[
 *[(x,'edges must be exact list0..56') for x in (None,L(),(),[('a','b',0)]*57)],
 *[([x],'edge must be exact source target cost tuple') for x in (['a','b',0],T(('a','b',0)),('a','b'),('a','b',0,1))],
 *[([x],'endpoints must be distinct known valid labels') for x in ((S('a'),'b',0),('a',S('b'),0),('a',False,0),('a','unknown',0),('a','a',0))],
 ([('a','b',0),('a','b',1)],'ordered pairs must be unique'),
 *[([('a','b',x)],'cost must be exact int0..1000') for x in (False,I(1),1.0,-1,1001)],
 ([('a','b',False),('','b',0)],'cost must be exact int0..1000'),
])
def test_first_bad(es,message):
    with pytest.raises(ValueError) as exc:best_path(['a','b'],es,'a','b')
    assert str(exc.value)==message

def test_cost_length_input_ties_cycles_singleton_caps_ownership():
    exact(best_path(['z','b','a','g'],[('z','a',1),('a','g',1),('z','b',1),('b','g',1)],'z','g'),{'path':['z','b','g'],'cost':2,'reasoning_validated':False})
    assert best_path(['z','a','g'],[('z','a',0),('a','g',1),('z','g',1)],'z','g')['path']==['z','g']
    exact(best_path(['a'],[],'a','a'),{'path':['a'],'cost':0,'reasoning_validated':False})
    exact(best_path(['a','b'],[],'a','b'),{'path':None,'cost':None,'reasoning_validated':False})
    ns=['x'*80,'\u200b']+list(map(str,range(6)));es=[(a,b,1000) for a in ns for b in ns if a!=b];out=best_path(ns,es,ns[0],ns[1]);assert out['cost']==1000;out['path'].clear();assert len(es)==56

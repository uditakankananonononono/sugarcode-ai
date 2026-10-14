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

import random,itertools
from sugarcode.extra_doc.cnf_prove1985_real import prove
class L(list):pass
class T(tuple):pass
class S(str):pass

def test_independent_cartesian_assignment_oracle():
    rng=random.Random(1985)
    for _ in range(100):
        atoms=list('abcd');clauses=[[(rng.choice(atoms),bool(rng.randrange(2))) for j in range(rng.randrange(4))] for i in range(rng.randrange(6))];query=(rng.choice(atoms),bool(rng.randrange(2)));models=[]
        for reverse in itertools.product([False,True],repeat=4):
            assignment=dict(zip(atoms,reversed(reverse)))
            if all(set(assignment[a]==p for a,p in clause)&{True} for clause in clauses):models.append(assignment)
        bad=[m for m in models if m[query[0]]!=query[1]];counter=list(bad[0].items()) if bad else None
        exact(prove(atoms,clauses,query),{'models':len(models),'entailed':not bad,'countermodel':counter,'general_theorem_inferred':False})

@pytest.mark.parametrize('atoms,clauses,query,message',[
 *[(x,[],('a',True),'atoms must be exact list1..8') for x in (None,L(['a']),(),[],list(map(str,range(9))))],
 *[([x],[],('a',True),'atoms must be unique valid names') for x in ('',' ',False,S('a'),'x'*81,'\u00a0')],
 (['a','a'],[],('a',True),'atoms must be unique valid names'),
 *[(['a'],x,('a',True),'clauses must be exact list0..20') for x in (None,L(),(),[[]]*21)],
 *[(['a'],[x],('a',True),'clause must be exact list0..8') for x in (None,L(),(),[('a',True)]*9)],
 *[(['a'],[[x]],('a',True),'literal must be exact atom polarity tuple') for x in (['a',True],T(('a',True)),('a',),('a',True,1))],
 *[(['a'],[[(x,True)]],('a',True),'literal atom must be known valid name') for x in ('',' ',False,S('a'),'unknown')],
 *[(['a'],[[('a',x)]],('a',True),'literal polarity must be exact bool') for x in (0,1,None,'True')],
 *[(['a'],[],x,'literal must be exact atom polarity tuple') for x in (['a',True],T(('a',True)),('a',))],
 (['a'],[ [('a',True),(False,False)] ],('a',True),'literal atom must be known valid name'),
 (['a'],[[('unknown',1)]],('a',True),'literal atom must be known valid name'),
 (['a'],[],('a',1),'literal polarity must be exact bool'),
])
def test_first_bad(atoms,clauses,query,message):
    with pytest.raises(ValueError) as exc:prove(atoms,clauses,query)
    assert str(exc.value)==message

def test_empty_vacuous_tautology_order_ownership_caps():
    exact(prove(['a'],[],('a',True)),{'models':2,'entailed':False,'countermodel':[('a',False)],'general_theorem_inferred':False})
    exact(prove(['a'],[[]],('a',True)),{'models':0,'entailed':True,'countermodel':None,'general_theorem_inferred':False})
    assert prove(['a'],[[('a',True),('a',False)]],('a',False))['models']==2
    atoms=['x'*80,'\u200b']+list('abcdef');clauses=[[('a',True)]*8]*20;out=prove(atoms,clauses,('b',True));assert out['models']==128;out['countermodel'].clear();assert len(atoms)==8 and len(clauses)==20

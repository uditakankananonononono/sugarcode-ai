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
from sugarcode.extra_doc.horn_reason1984_real import infer
class L(list):pass
class T(tuple):pass
class S(str):pass

def test_independent_min_derivation_height_oracle():
    rng=random.Random(1984)
    for _ in range(100):
        atoms=list('abcdefg');facts=rng.sample(atoms,rng.randrange(4));rules=[(rng.sample(atoms,rng.randrange(4)),rng.choice(atoms)) for i in range(12)];height={x:0 for x in facts}
        changed=True
        while changed:
            changed=False
            for premises,c in rules:
                if all(x in height for x in premises):
                    candidate=1+max([height[x] for x in premises] or [0])
                    if c not in height or candidate<height[c]:height[c]=candidate;changed=True
        rounds=[]
        for level in range(1,max(height.values(),default=0)+1):
            layer=[]
            for premises,c in rules:
                if height.get(c)==level and c not in layer and all(x in height and height[x]<level for x in premises):layer.append(c)
            rounds.append(layer)
        closure=facts+[x for layer in rounds for x in layer];q=rng.choice(atoms)
        exact(infer(facts,rules,q),{'closure':closure,'rounds':rounds,'entailed':q in height,'general_truth_inferred':False})

@pytest.mark.parametrize('facts,rules,query,message',[
 *[(x,[],'a','facts must be exact list0..20') for x in (None,L(),(),list(map(str,range(21))))],
 *[([x],[],'a','facts must be unique valid atoms') for x in ('',' ',False,S('a'),'x'*81,'\u00a0')],
 (['a','a'],[],'a','facts must be unique valid atoms'),
 *[([],x,'a','rules must be exact list0..40') for x in (None,L(),(),[([], 'a')]*41)],
 *[([],[x],'a','rule must be exact premises conclusion tuple') for x in ([[],'a'],T(([],'a')),([],),([],'a',1))],
 *[([],[(x,'a')],'a','premises must be exact list0..10') for x in (None,L(),(),list(map(str,range(11))))],
 *[([],[([x],'a')],'a','premises must be unique valid atoms') for x in ('',' ',False,S('a'),'x'*81,'\u00a0')],
 ([],[(['a','a'],'b')],'a','premises must be unique valid atoms'),
 *[([],[( [],x)],'a','conclusion must be valid atom') for x in ('',' ',False,S('a'),'x'*81,'\u00a0')],
 *[([],[],x,'query must be valid atom') for x in ('',' ',False,S('a'),'x'*81,'\u00a0')],
 (['a',False],None,False,'facts must be unique valid atoms'),
 ([],[(['a',False],False)],False,'premises must be unique valid atoms'),
])
def test_first_bad(facts,rules,query,message):
    with pytest.raises(ValueError) as exc:infer(facts,rules,query)
    assert str(exc.value)==message

def test_layers_all_premises_cycles_duplicates_ownership():
    facts=['a'];rules=[(['b'],'c'),(['a'],'b'),(['a','z'],'bad'),(['a'],'b'),(['c'],'a')]
    exact(infer(facts,rules,'c'),{'closure':['a','b','c'],'rounds':[['b'],['c']],'entailed':True,'general_truth_inferred':False})
    exact(infer([], [(['b'],'a'),(['a'],'b')],'a'),{'closure':[],'rounds':[],'entailed':False,'general_truth_inferred':False})
    exact(infer([], [([], 'a')],'a'),{'closure':['a'],'rounds':[['a']],'entailed':True,'general_truth_inferred':False})
    out=infer(facts,rules,'z');out['closure'].clear();out['rounds'][0].clear();assert facts==['a'];assert rules[1]==(['a'],'b')

def test_accepted_caps():
    facts=['x'*80,'\u200b']+[str(i) for i in range(18)];rules=[([str(i) for i in range(10)],'n'+str(j)) for j in range(40)];out=infer(facts,rules,'x'*80);assert len(out['closure'])==60;assert out['entailed'] is True

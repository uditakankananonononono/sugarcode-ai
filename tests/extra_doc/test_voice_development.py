from fractions import Fraction as F
from itertools import product
import pytest
from sugarcode.extra_doc.voice_development import voice_development


def oracle(lexicon,rules,target):
    candidates=[]
    for rid,(order,tone,ending) in enumerate(rules):
        for indices in product(*(range(len(slot)) for slot in lexicon)):
            selected=[lexicon[i][j] for i,j in enumerate(indices)]
            profile=(sum(F(x[1]) for x in selected)/len(selected),F(tone))
            distance=sum(abs(a-b) for a,b in zip(profile,target))
            candidates.append((distance,rid,indices,profile,' '.join(selected[i][0] for i in order)+ending))
    return min(candidates)


def test_realized_voice_matches_exhaustive():
    lex=[[('I',0),('We',2)],[('move',1),('linger',4)],[('now',1),('quietly',5)]]
    rules=[([0,1,2],0,'.'),([2,0,1],3,'!')];target=[3,2]
    expected=oracle(lex,rules,target);r=voice_development(lex,rules,target)
    assert r=={'sentence':expected[4],'profile':list(expected[3]),'word_indices':list(expected[2]),'rule_index':expected[1],'certificate':{'distance':expected[0],'optimal':True,'target':target}}


def test_ties_rule_and_lexicon_order():
    r=voice_development([[('a',0),('b',0)]],[([0],0,'.'),([0],0,'!')],[0,0])
    assert r['sentence']=='a.' and r['rule_index']==0 and r['word_indices']==[0]


@pytest.mark.parametrize('target',[[0,0],[1,2],[3,-2],[-3,3]])
def test_small_oracle(target):
    lex=[[('a',-2),('b',1)],[('c',2),('d',-1)]];rules=[([0,1],-1,'.'),([1,0],2,'?')]
    expected=oracle(lex,rules,target);r=voice_development(lex,rules,target)
    assert r['sentence']==expected[-1] and r['certificate']['distance']==expected[0]


@pytest.mark.parametrize('lex',[None,(),[],[[]],[[('a',0)]]*4,[[('a',0)]*4],[[None]],[[('',0)]],[[('a'*21,0)]],[[('a b',0)]],[[('a',True)]],[[('a',1.)]],[[('a',11)]]])
def test_lex_refusal(lex):
    with pytest.raises((TypeError,ValueError)):voice_development(lex,[([0],0,'.')],[0,0])


@pytest.mark.parametrize('rules',[None,(),[],[([0],0,'.')]*5,[None],[([1],0,'.')],[([0,0],0,'.')],[([0],True,'.')],[([0],1.,'.')],[([0],11,'.')],[([0],0,'x')]])
def test_rule_refusal(rules):
    with pytest.raises((TypeError,ValueError)):voice_development([[('a',0)]],rules,[0,0])


@pytest.mark.parametrize('target',[None,(),[],[0],[0,0,0],[True,0],[1.,0],[11,0]])
def test_target_refusal(target):
    with pytest.raises((TypeError,ValueError)):voice_development([[('a',0)]],[([0],0,'.')],target)


def test_caps_and_preflight():
    class Rows(list):
        def __iter__(self):raise AssertionError('oversized scanned')
    with pytest.raises(ValueError):voice_development(Rows([None]*4),[],[0,0])
    r=voice_development([[('x'*20,-10),('b',0),('c',10)]]*3,[([0,1,2],10,'.')]*4,[10,10])
    assert r['sentence']=='c c c.' and r['certificate']['distance']==0

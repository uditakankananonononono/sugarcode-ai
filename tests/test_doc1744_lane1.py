import random
import pytest
from sugarcode.extra_doc.conversation1744 import audit_turns


def test_independent_adjacency_matrix_oracle():
    rng=random.Random(1744)
    for _ in range(100):
        turns=[(rng.choice('abc'),rng.randint(1,1000)) for i in range(50)]
        matrix={(a,b):sum(turns[i][0]==a and turns[i+1][0]==b for i in range(49)) for a in 'abc' for b in 'abc'}
        edges=[(a,b,n) for (a,b),n in sorted(matrix.items()) if n];same=sum(matrix[(a,a)] for a in 'abc')
        got=audit_turns(turns);assert got=={'edges':edges,'durations':[(a,sum(d for s,d in turns if s==a)) for a in 'abc'],'continuations':same,'switches':49-same,'claim':'PARTIAL','conversation_validated':False}

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('turns,message',[
 *[(x,'turns must be an exact list with 2..100 entries') for x in (None,L([('a',1),('b',1)]),(('a',1),('b',1)),[],[('a',1)],[('a',1)]*101)],
 *[([x,('b',1)],'turn must be a speaker duration tuple') for x in (['a',1],T(('a',1)),('a',),('a',1,2))],
 *[([(x,1),('b',1)],'speaker must be a nonblank exact string of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([('a',x),('b',1)],'duration must be an integer in 1..1000') for x in (None,True,I(1),1.5,0,1001)],
])
def test_invalid(turns,message):
    with pytest.raises(ValueError) as exc:audit_turns(turns)
    assert str(exc.value)==message


def test_caps_single_speaker_noncontiguous_order():
    got=audit_turns([('x'*80,1000)]*100);assert got['edges']==[('x'*80,'x'*80,99)] and got['durations']==[('x'*80,100000)] and got['switches']==0
    assert audit_turns([('\u200b',1),('a',1),('\u200b',1)])['edges']==[('a','\u200b',1),('\u200b','a',1)]

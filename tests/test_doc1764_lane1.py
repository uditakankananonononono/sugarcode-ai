import random
import pytest
from sugarcode.extra_doc.rational1764 import evaluate
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_pairwise_dominance_oracle():
    rng=random.Random(1764)
    for _ in range(100):
        rows=[(str(i),rng.randrange(1001),rng.randrange(1001)) for i in range(10)];net={n:b-c for n,b,c in rows}
        winners=[n for n,b,c in rows if all(net[n]>=net[m] for m in net)]
        assert evaluate(rows)=={'utilities':[(n,net[n]) for n,b,c in rows],'maximizers':winners,'regret':[(n,max(net[m]-net[n] for m in net)) for n,b,c in rows],'claim':'PARTIAL','behavior_validated':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'options must be an exact list with 2..20 entries') for x in (None,L([('a',0,0),('b',0,0)]),(('a',0,0),('b',0,0)),[],[('a',0,0)],[(str(i),0,0) for i in range(21)])],
 *[([x,('b',0,0)],'option must be an id benefit cost tuple') for x in (['a',0,0],T(('a',0,0)),('a',0),('a',0,0,1))],
 *[([(x,0,0),('b',0,0)],'option IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',0,0),('a',1,1)],'option IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x,0),('b',0,0)],'benefit must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
 *[([('a',0,x),('b',0,0)],'cost must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:evaluate(rows)
    assert str(exc.value)==message


def test_caps_minimum_count_and_ties():
    got=evaluate([(str(i),1000,1000) for i in range(20)]);assert got['maximizers']==list(map(str,range(20))) and got['regret']==[(str(i),0) for i in range(20)]
    got=evaluate([('x'*80,0,1000),('\u200b',1000,0)]);assert got['maximizers']==['\u200b'] and got['regret']==[('x'*80,2000),('\u200b',0)]

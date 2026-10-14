import random
import pytest
from sugarcode.extra_doc.postcolonial1757 import audit_transfers
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_signed_incidence_oracle():
    rng=random.Random(1757);actors=list('abcd')
    for _ in range(100):
        rng.shuffle(actors);transfers=[]
        for i in range(50):
            a,b=rng.sample(actors,2);transfers.append((a,b,rng.randint(1,1000)))
        balances=[]
        for n in actors:
            signed=[u*(int(b==n)-int(a==n)) for a,b,u in transfers]
            incoming=sum(x for x in signed if x>0);outgoing=-sum(x for x in signed if x<0);balances.append((n,incoming,outgoing,sum(signed)))
        assert audit_transfers(actors,transfers)=={'balances':balances,'total_transferred':sum(u for a,b,u in transfers),'claim':'PARTIAL','history_validated':False}

@pytest.mark.parametrize('actors',[None,L(['a','b']),('a','b'),[],['a'],list(map(str,range(21))),['a','a'],*[[x,'b'] for x in BAD]])
def test_actors_invalid(actors):
    with pytest.raises(ValueError) as exc:audit_transfers(actors,[])
    assert str(exc.value)=='actors must be an exact list of 2..20 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'transfers must be an exact list with 0..100 entries') for x in (None,L(),(),[('a','b',1)]*101)],
 *[([x],'transfer must be a source target units tuple') for x in (['a','b',1],T(('a','b',1)),('a','b'),('a','b',1,1))],
 *[([(x,'b',1)],'endpoints must be distinct known valid labels') for x in (*BAD,'unknown','b')],
 *[([('a',x,1)],'endpoints must be distinct known valid labels') for x in (*BAD,'unknown','a')],
 *[([('a','b',x)],'units must be an integer in 1..1000') for x in (None,True,I(1),1.5,0,1001)],
])
def test_transfers_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_transfers(['a','b'],rows)
    assert str(exc.value)==message


def test_caps_duplicates_and_zero_flow():
    actors=['x'*80,'\u200b']+list(map(str,range(18)));got=audit_transfers(actors,[('x'*80,'\u200b',1000)]*100)
    assert got['balances'][:2]==[('x'*80,0,100000,-100000),('\u200b',100000,0,100000)] and got['total_transferred']==100000
    assert audit_transfers(['a','b'],[])['balances']==[('a',0,0,0),('b',0,0,0)]

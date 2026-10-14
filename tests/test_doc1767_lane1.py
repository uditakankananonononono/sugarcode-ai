import random
import copy
import itertools
import pytest
from sugarcode.extra_doc.coalition1767 import enumerate_coalitions
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_powerset_deletion_oracle():
    rng=random.Random(1767)
    for _ in range(100):
        players=[(str(i),rng.randint(1,100)) for i in range(6)];quota=rng.randint(1,1000);coalitions=[]
        for k in range(1,7):
            for indices in itertools.combinations(range(6),k):
                total=sum(players[i][1] for i in indices)
                if total>=quota:coalitions.append((sum(2**i for i in indices),indices,total))
        coalitions.sort();winning=[([players[i][0] for i in inds],total) for mask,inds,total in coalitions]
        minimal=[([players[i][0] for i in inds],total) for mask,inds,total in coalitions if not any(sum(players[j][1] for j in inds if j!=i)>=quota for i in inds)]
        assert enumerate_coalitions(players,quota)=={'winning':winning,'minimal':minimal,'claim':'PARTIAL','coalitions_validated':False}

@pytest.mark.parametrize('players,message',[
 *[(x,'players must be an exact list with 2..10 entries') for x in (None,L([('a',1),('b',1)]),(('a',1),('b',1)),[],[('a',1)],[(str(i),1) for i in range(11)])],
 *[([x,('b',1)],'player must be an id weight tuple') for x in (['a',1],T(('a',1)),('a',),('a',1,1))],
 *[([(x,1),('b',1)],'player IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',1),('a',1)],'player IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x),('b',1)],'weight must be an integer in 1..100') for x in (None,True,I(1),1.5,0,101)],
])
def test_players_invalid(players,message):
    with pytest.raises(ValueError) as exc:enumerate_coalitions(players,1)
    assert str(exc.value)==message

@pytest.mark.parametrize('quota',(None,True,I(1),1.5,0,1001))
def test_quota_invalid(quota):
    with pytest.raises(ValueError) as exc:enumerate_coalitions([('a',1),('b',1)],quota)
    assert str(exc.value)=='quota must be an integer in 1..1000'


def test_caps_minimum_count_no_winner_and_ownership():
    got=enumerate_coalitions([(str(i),100) for i in range(10)],1000);assert got['minimal']==[(list(map(str,range(10))),1000)]
    rows=[('x'*80,1),('\u200b',1)];before=copy.deepcopy(rows);out=enumerate_coalitions(rows,1)
    assert out['minimal']==[(['x'*80],1),(['\u200b'],1)]
    out['minimal'][0][0].append('z');assert out['winning'][0][0]==['x'*80]
    out['winning'].clear();assert rows==before
    assert enumerate_coalitions(rows,1000)['winning']==[]

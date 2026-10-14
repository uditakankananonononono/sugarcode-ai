import random
import pytest
from sugarcode.extra_doc.public1763 import tally
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_approval_matrix_oracle():
    rng=random.Random(1763);policies=list('abcd')
    for _ in range(100):
        rng.shuffle(policies);ballots=[(str(i),rng.sample(policies,rng.randrange(5))) for i in range(20)];matrix=[[int(p in a) for p in policies] for n,a in ballots];counts=[(p,sum(r[j] for r in matrix)) for j,p in enumerate(policies)]
        assert tally(policies,ballots)=={'counts':counts,'leaders':[p for p,c in counts if all(c>=other for q,other in counts)],'claim':'PARTIAL','election_validated':False}

@pytest.mark.parametrize('policies',[None,L(['a','b']),('a','b'),[],['a'],list(map(str,range(21))),['a','a'],*[[x,'b'] for x in BAD]])
def test_policies_invalid(policies):
    with pytest.raises(ValueError) as exc:tally(policies,[('b',[])])
    assert str(exc.value)=='policies must be an exact list of 2..20 unique valid labels'

@pytest.mark.parametrize('ballots,message',[
 *[(x,'ballots must be an exact list with 1..100 entries') for x in (None,L([('a',[])]),(('a',[]),),[],[(str(i),[]) for i in range(101)])],
 *[([x],'ballot must be an id approvals tuple') for x in (['a',[]],T(('a',[])),('a',),('a',[],1))],
 *[([(x,[])],'ballot IDs must be unique valid labels') for x in BAD],
 ([('a',[]),('a',[])],'ballot IDs must be unique valid labels'),
 *[([('a',x)],'approvals must be an exact list of 0..20 unique known policy labels') for x in (None,L(),('a',),['a','a'],['unknown'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_ballots_invalid(ballots,message):
    with pytest.raises(ValueError) as exc:tally(['a','b'],ballots)
    assert str(exc.value)==message


def test_caps_single_ballot_empty_tie_labels():
    policies=['x'*80]+list(map(str,range(19)));got=tally(policies,[(str(i),policies[:]) for i in range(100)])
    assert got['leaders']==policies and got['counts']==[(p,100) for p in policies]
    assert tally(['a','\u200b'],[('x'*80,[])])['leaders']==['a','\u200b']

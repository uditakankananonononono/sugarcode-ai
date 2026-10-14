import random
import copy
import pytest
from sugarcode.extra_doc.voting1768 import tally as run
class L(list):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)

@pytest.mark.parametrize('candidates',[None,L(['a','b']),('a','b'),[],['a'],list(map(str,range(11))),['a','a'],*[[x,'b'] for x in BAD]])
def test_candidates_invalid(candidates):
    with pytest.raises(ValueError) as exc:run(candidates,[['a','b']])
    assert str(exc.value)=='candidates must be an exact list of 2..10 unique valid labels'

@pytest.mark.parametrize('ballots,message',[
 *[(x,'ballots must be an exact list with 1..100 entries') for x in (None,L([['a','b']]),(['a','b'],),[],[['a','b']]*101)],
 *[([x],'each ballot must be an exact candidate permutation list') for x in (None,L(['a','b']),('a','b'),[],['a'],['a','b','c'],['a','a'],['a','unknown'],*[[x,'b'] for x in BAD])],
])
def test_ballots_invalid(ballots,message):
    with pytest.raises(ValueError) as exc:run(['a','b'],ballots)
    assert str(exc.value)==message


def test_caps_minimum_singleton_and_ownership():
    candidates=['x'*80,'\u200b']+list(map(str,range(8)));ballots=[candidates[:] for i in range(100)];out=run(candidates,ballots)
    before=copy.deepcopy((candidates,ballots))
    for x in out.values():
        if type(x) is list:x.clear()
    assert (candidates,ballots)==before
    got=run(['a','b'],[['a','b']]);assert got['leaders']==['a']

def test_independent_rank_histogram_oracle():
    rng=random.Random(1768)
    for _ in range(100):
        candidates=list('abcde');rng.shuffle(candidates);ballots=[rng.sample(candidates,5) for i in range(20)]
        scores=[(c,sum((4-rank)*sum(b[rank]==c for b in ballots) for rank in range(5))) for c in candidates]
        assert run(candidates,ballots)=={'scores':scores,'leaders':[c for c,s in scores if all(s>=n for d,n in scores)],'claim':'PARTIAL','election_validated':False}

def test_ties():
    assert run(['a','b'],[['a','b'],['b','a']])['leaders']==['a','b']

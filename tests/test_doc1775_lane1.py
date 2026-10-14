import random
import copy
import pytest
from sugarcode.extra_doc.nationalism1775 import count_symbols
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_occurrence_histogram_oracle():
    rng=random.Random(1775);symbols=list('abcd')
    for _ in range(100):
        rng.shuffle(symbols);rows=[(str(i),rng.choices(symbols,k=rng.randrange(30))) for i in range(20)];hist=[]
        for n,tags in rows:
            h={}
            for t in tags:h[t]=h.get(t,0)+1
            hist.append(h)
        assert count_symbols(symbols,rows)=={'counts':[(s,sum(h.get(s,0) for h in hist),sum(h.get(s,0)>0 for h in hist)) for s in symbols],'claim':'PARTIAL','ideology_inferred':False}

@pytest.mark.parametrize('symbols',[None,L(['a']),('a',),[],list(map(str,range(21))),['a','a'],*[[x] for x in BAD]])
def test_symbols_invalid(symbols):
    with pytest.raises(ValueError) as exc:count_symbols(symbols,[('d',[])])
    assert str(exc.value)=='symbols must be an exact list of 1..20 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'documents must be an exact list with 1..100 entries') for x in (None,L([('a',[])]),(('a',[]),),[],[(str(i),[]) for i in range(101)])],
 *[([x],'document must be an id tags tuple') for x in (['a',[]],T(('a',[])),('a',),('a',[],1))],
 *[([(x,[])],'document IDs must be unique valid labels') for x in BAD],
 ([('a',[]),('a',[])],'document IDs must be unique valid labels'),
 *[([('a',x)],'tags must be an exact list of 0..100 known symbol labels') for x in (None,L(),('a',),['unknown'],['a']*101,*[[x] for x in BAD])],
])
def test_rows_invalid(rows,message):
    with pytest.raises(ValueError) as exc:count_symbols(['a','b'],rows)
    assert str(exc.value)==message


def test_caps_repetitions_singletons_and_ownership():
    symbols=['x'*80,'\u200b']+list(map(str,range(18)));rows=[(str(i),['x'*80]*100) for i in range(100)];before=copy.deepcopy(rows);out=count_symbols(symbols,rows);assert out['counts'][0]==('x'*80,10000,100)
    out['counts'].clear();assert rows==before
    assert count_symbols(['\u200b'],[('x'*80,[])])['counts']==[('\u200b',0,0)]

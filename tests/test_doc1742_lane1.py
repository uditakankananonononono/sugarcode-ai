import random
import pytest
from sugarcode.extra_doc.content1742 import count_codes


def test_independent_incidence_matrix_oracle():
    rng=random.Random(1742);cats=list('abcd')
    for _ in range(100):
        rng.shuffle(cats);units=[(str(i),rng.sample(cats,rng.randrange(5))) for i in range(30)]
        matrix=[[int(c in codes) for c in cats] for _,codes in units]
        counts=[(c,sum(row[j] for row in matrix)) for j,c in enumerate(cats)]
        pairs=[(a,b,sum(row[i]*row[j] for row in matrix)) for i,a in enumerate(cats) for j,b in enumerate(cats) if i<j]
        got=count_codes(cats,units);assert got=={'counts':counts,'cooccurrences':pairs,'claim':'PARTIAL','coding_validated':False}

class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,1.5,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)
@pytest.mark.parametrize('cats', [L(['a','b']),('a','b'),[],['a'],list(map(str,range(21))),['a','a'],*[[x,'b'] for x in BAD]])
def test_categories_invalid(cats):
    with pytest.raises(ValueError) as exc:count_codes(cats,[('u',[])])
    assert str(exc.value)=='categories must be an exact list of 2..20 unique valid labels'

@pytest.mark.parametrize('units,message',[
 *[(x,'units must be an exact list with 1..100 entries') for x in (None,L([('u',[])]),(('u',[]),),[],[(str(i),[]) for i in range(101)])],
 *[([x],'unit must be an id codes tuple') for x in (['u',[]],T(('u',[])),('u',),('u',[],1))],
 *[([(x,[])],'unit IDs must be unique valid labels') for x in BAD],
 ([('u',[]),('u',[])],'unit IDs must be unique valid labels'),
 *[([('u',x)],'codes must be an exact list of 0..20 unique category labels') for x in (None,L(),('a',),['a','a'],['z'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_units_invalid(units,message):
    with pytest.raises(ValueError) as exc:count_codes(['a','b'],units)
    assert str(exc.value)==message


def test_all_caps_and_zero_code():
    cats=['x'*80]+list(map(str,range(19)));units=[(str(i),cats[:]) for i in range(100)]
    got=count_codes(cats,units);assert got['counts']==[(c,100) for c in cats]
    assert all(n==100 for a,b,n in got['cooccurrences']) and len(got['cooccurrences'])==190
    assert count_codes(['a','\u200b'],[('u'*80,[])])['counts']==[('a',0),('\u200b',0)]

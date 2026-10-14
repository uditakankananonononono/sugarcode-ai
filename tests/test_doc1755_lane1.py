import random
import pytest
from sugarcode.extra_doc.queer1755 import audit_tags
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_tag_incidence_oracle():
    rng=random.Random(1755);cats=list('abcd')
    for _ in range(100):
        rng.shuffle(cats);rows=[(str(i),rng.sample(cats,rng.randrange(5))) for i in range(10)];matrix=[[int(c in ts) for c in cats] for n,ts in rows]
        assert audit_tags(cats,rows)=={'untagged':[n for (n,ts),r in zip(rows,matrix) if sum(r)==0],'single_tag':[n for (n,ts),r in zip(rows,matrix) if sum(r)==1],'multi_tag':[n for (n,ts),r in zip(rows,matrix) if sum(r)>1],'unused_categories':[c for j,c in enumerate(cats) if sum(r[j] for r in matrix)==0],'claim':'PARTIAL','identity_inferred':False,'theory_validated':False}

@pytest.mark.parametrize('cats',[None,L(['a','b']),('a','b'),[],['a'],list(map(str,range(21))),['a','a'],*[[x,'b'] for x in BAD]])
def test_categories_invalid(cats):
    with pytest.raises(ValueError) as exc:audit_tags(cats,[('r',[])])
    assert str(exc.value)=='categories must be an exact list of 2..20 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'records must be an exact list with 1..100 entries') for x in (None,L([('r',[])]),(('r',[]),),[],[(str(i),[]) for i in range(101)])],
 *[([x],'record must be an id tags tuple') for x in (['r',[]],T(('r',[])),('r',),('r',[],1))],
 *[([(x,[])],'record IDs must be unique valid labels') for x in BAD],
 ([('r',[]),('r',[])],'record IDs must be unique valid labels'),
 *[([('r',x)],'tags must be an exact list of 0..20 unique known category labels') for x in (None,L(),('a',),['a','a'],['unknown'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_rows_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_tags(['a','b'],rows)
    assert str(exc.value)==message


def test_caps_partitions_empty_single_and_zero_width():
    cats=['x'*80]+list(map(str,range(19)));got=audit_tags(cats,[(str(i),cats[:]) for i in range(100)])
    assert got['multi_tag']==list(map(str,range(100))) and got['unused_categories']==[]
    got=audit_tags(['\u200b','b'],[('x'*80,['\u200b']),('e',[])]);assert got['single_tag']==['x'*80] and got['untagged']==['e'] and got['unused_categories']==['b']

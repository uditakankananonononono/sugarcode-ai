import random
import pytest
from sugarcode.extra_doc.hermeneutics1749 import audit_links
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_incidence_join_oracle():
    rng=random.Random(1749);passages=list('abcdef')
    for _ in range(100):
        rng.shuffle(passages);rows=[(str(i),rng.sample(passages,rng.randint(1,6))) for i in range(8)]
        links=[(p,[n for n,rs in rows if rs.count(p)]) for p in passages]
        shared=[(a,b,sorted(p for p in passages if p in ar and p in br)) for i,(a,ar) in enumerate(rows) for b,br in rows[i+1:] if any(p in ar and p in br for p in passages)]
        assert audit_links(passages,rows)=={'links':links,'unreferenced':[p for p in passages if all(p not in rs for n,rs in rows)],'shared_evidence':shared,'claim':'PARTIAL','interpretations_validated':False}

@pytest.mark.parametrize('passages',[None,L(['a']),('a',),[],list(map(str,range(101))),['a','a'],*[[x] for x in BAD]])
def test_passages_invalid(passages):
    with pytest.raises(ValueError) as exc:audit_links(passages,[('i',['a'])])
    assert str(exc.value)=='passages must be an exact list of 1..100 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'interpretations must be an exact list with 1..20 entries') for x in (None,L([('a',['a'])]),(('a',['a']),),[],[(str(i),['a']) for i in range(21)])],
 *[([x],'interpretation must be an id passage_refs tuple') for x in (['a',['a']],T(('a',['a'])),('a',),('a',['a'],1))],
 *[([(x,['a'])],'interpretation IDs must be unique valid labels') for x in BAD],
 ([('a',['a']),('a',['a'])],'interpretation IDs must be unique valid labels'),
 *[([('a',x)],'refs must be an exact list of 1..100 unique known passage labels') for x in (None,L(['a']),('a',),[],['a','a'],['unknown'],list(map(str,range(101))),*[[x] for x in BAD])],
])
def test_rows_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_links(['a','b'],rows)
    assert str(exc.value)==message


def test_caps_labels_and_unreferenced():
    passages=['x'*80]+list(map(str,range(99)));got=audit_links(passages,[(str(i),passages[:]) for i in range(20)])
    assert len(got['shared_evidence'])==190 and got['unreferenced']==[] and len(got['links'])==100
    assert audit_links(['\u200b','b'],[('x'*80,['\u200b'])])['unreferenced']==['b']

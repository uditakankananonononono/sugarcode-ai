import random
import pytest
from sugarcode.extra_doc.critical1753 import audit_coverage
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_evidence_incidence_oracle():
    rng=random.Random(1753);evidence=list('abcdef')
    for _ in range(100):
        rng.shuffle(evidence);rows=[(str(i),rng.sample(evidence,rng.randrange(7))) for i in range(10)]
        matrix=[[int(e in rs) for e in evidence] for n,rs in rows];counts=[(e,sum(r[i] for r in matrix)) for i,e in enumerate(evidence)]
        assert audit_coverage(evidence,rows)=={'unsupported':[n for (n,rs),r in zip(rows,matrix) if sum(r)==0],'unused':[e for e,n in counts if n==0],'counts':counts,'claim':'PARTIAL','critique_validated':False}

@pytest.mark.parametrize('evidence',[None,L(['a']),('a',),[],list(map(str,range(101))),['a','a'],*[[x] for x in BAD]])
def test_evidence_invalid(evidence):
    with pytest.raises(ValueError) as exc:audit_coverage(evidence,[('c',[])])
    assert str(exc.value)=='evidence must be an exact list of 1..100 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'critiques must be an exact list with 1..20 entries') for x in (None,L([('a',[])]),(('a',[]),),[],[(str(i),[]) for i in range(21)])],
 *[([x],'critique must be an id refs tuple') for x in (['a',[]],T(('a',[])),('a',),('a',[],1))],
 *[([(x,[])],'critique IDs must be unique valid labels') for x in BAD],
 ([('a',[]),('a',[])],'critique IDs must be unique valid labels'),
 *[([('a',x)],'refs must be an exact list of 0..100 unique known evidence labels') for x in (None,L(),('a',),['a','a'],['unknown'],list(map(str,range(101))),*[[x] for x in BAD])],
])
def test_rows_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_coverage(['a','b'],rows)
    assert str(exc.value)==message


def test_caps_zero_refs_and_zero_width():
    evidence=['x'*80]+list(map(str,range(99)));got=audit_coverage(evidence,[(str(i),evidence[:]) for i in range(20)])
    assert got['counts']==[(e,20) for e in evidence] and got['unsupported']==[]
    assert audit_coverage(['\u200b'],[('x'*80,[])])['unused']==['\u200b']

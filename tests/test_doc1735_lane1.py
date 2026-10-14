import random
import pytest
from sugarcode.extra_doc.case_study1735 import audit


def test_independent_unique_source_join_oracle():
    rng=random.Random(1735)
    for _ in range(100):
        claims=['a','b','c'];rows=[(str(i),rng.choice('abcd'),rng.choice('xyz')) for i in range(20)];expected=[]
        for c in claims:
            sources=sorted(dict.fromkeys(s for n,claim,s in rows if claim==c));expected.append((c,len(sources),sources))
        got=audit(claims,rows);assert got['sources']==expected and got['under_triangulated']==[c for c,n,s in expected if n<2]
        assert got['unknown']==[n for n,c,s in rows if c not in claims]
        assert got['claim']=='PARTIAL' and got['truth_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
@pytest.mark.parametrize('claims,rows,message',[
 (L(['a']),[],'claims must be an exact list with 1..20 entries'),
 ([],[],'claims must be an exact list with 1..20 entries'),
 ([str(i) for i in range(21)],[],'claims must be an exact list with 1..20 entries'),
 *[([x],[],'claims must be unique valid labels') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 (['a'],L(),'evidence must be an exact list with 0..100 entries'),
 (['a'],[(str(i),'a','s') for i in range(101)],'evidence must be an exact list with 0..100 entries'),
 (['a'],[T(('a','a','s'))],'evidence must be valid id claim source tuples'),
 (['a'],[('a','a','s','s')],'evidence must be valid id claim source tuples'),
 *[(['a'],[tuple(x if i==pos else ['id','a','s'][i] for i in range(3))],'evidence must be valid id claim source tuples') for pos in range(3) for x in (S('a'),'\t')],
 (['a'],[('id','a','s')]*2,'evidence IDs must be unique'),
])
def test_invalid(claims,rows,message):
    with pytest.raises(ValueError) as exc:audit(claims,rows)
    assert str(exc.value)==message


def test_caps_source_dedup_and_labels():
    claims=list(map(str,range(20)));rows=[(str(i),str(i%20),'s') for i in range(100)]
    assert len(audit(claims,rows)['under_triangulated'])==20
    assert audit(['x'*80],[('\u200b','x'*80,'s'),('b','x'*80,'s')])['sources']==[('x'*80,1,['s'])]
    assert audit(['a'],[('1','a','x'),('2','a','y')])['under_triangulated']==[]

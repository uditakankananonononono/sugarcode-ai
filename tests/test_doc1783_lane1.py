import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc.poverty1783 import audit_gap
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_fraction_shortfall_oracle():
    rng=random.Random(1783)
    for _ in range(100):
        rows=[(str(i),rng.randrange(1001)) for i in range(20)];line=rng.randint(1,1000);shortfalls=[(n,line-u if u<line else 0) for n,u in rows];gap=sum((Fraction(g,20*line) for n,g in shortfalls))
        assert audit_gap(rows,line)=={'below':[n for n,u in rows if line>u],'shortfalls':shortfalls,'normalized_gap':(gap.numerator,gap.denominator),'claim':'PARTIAL','poverty_inferred':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'incomes must be an exact list with 1..100 entries') for x in (None,L([('a',0)]),(('a',0),),[],[(str(i),0) for i in range(101)])],
 *[([x],'income row must be an id income tuple') for x in (['a',0],T(('a',0)),('a',),('a',0,1))],
 *[([(x,0)],'IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',0),('a',1)],'IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x)],'income must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
])
def test_incomes_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_gap(rows,1)
    assert str(exc.value)==message

@pytest.mark.parametrize('line',(None,True,I(1),1.5,0,1001))
def test_line_invalid(line):
    with pytest.raises(ValueError) as exc:audit_gap([('a',0)],line)
    assert str(exc.value)=='line must be an integer in 1..1000'


def test_caps_single_boundary_and_ownership():
    assert audit_gap([(str(i),1000) for i in range(100)],1000)['normalized_gap']==(0,1)
    rows=[('x'*80,0)];out=audit_gap(rows,1);assert out['normalized_gap']==(1,1);out['shortfalls'].clear();out['below'].clear();assert rows==[('x'*80,0)]
    assert audit_gap([('\u200b',1)],1)['below']==[]

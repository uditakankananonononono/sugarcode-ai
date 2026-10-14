import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc.authoritarian1774 import concentration
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_pairwise_probability_oracle():
    rng=random.Random(1774)
    for _ in range(100):
        rows=[(str(i),rng.randint(1,1000)) for i in range(10)];total=sum(d for n,d in rows);h=Fraction(sum(d*d for n,d in rows),total*total)
        assert concentration(rows)=={'shares':[(n,(Fraction(d,total).numerator,Fraction(d,total).denominator)) for n,d in rows],'concentration':(h.numerator,h.denominator),'claim':'PARTIAL','regime_inferred':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'bodies must be an exact list with 2..20 entries') for x in (None,L([('a',1),('b',1)]),(('a',1),('b',1)),[],[('a',1)],[(str(i),1) for i in range(21)])],
 *[([x,('b',1)],'body must be an id decisions tuple') for x in (['a',1],T(('a',1)),('a',),('a',1,1))],
 *[([(x,1),('b',1)],'body IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',1),('a',1)],'body IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x),('b',1)],'decisions must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
 ([('a',0),('b',0)],'total decisions must be positive'),
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:concentration(rows)
    assert str(exc.value)==message


def test_caps_minimum_zero_share_ownership():
    assert concentration([(str(i),1000) for i in range(20)])['concentration']==(1,20)
    rows=[('x'*80,1000),('\u200b',0)];out=concentration(rows);assert out['shares']==[('x'*80,(1,1)),('\u200b',(0,1))] and out['concentration']==(1,1)
    out['shares'].clear();assert rows==[('x'*80,1000),('\u200b',0)]

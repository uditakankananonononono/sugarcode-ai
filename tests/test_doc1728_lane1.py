from fractions import Fraction
from functools import cmp_to_key
import random
import pytest
from sugarcode.extra_doc.response1728 import compare


def test_independent_cross_product_rate_oracle():
    rng=random.Random(1728)
    def cmp(a,b):
        diff=a[2]*b[1]-b[2]*a[1]
        return -(diff>0)+(diff<0) if diff else (a[0]>b[0])-(a[0]<b[0])
    for _ in range(100):
        rows=[]
        for i in range(20):
            invited=rng.randrange(1,10001);rows.append((str(i),invited,rng.randrange(invited+1)))
        expected=sorted(rows,key=cmp_to_key(cmp));got=compare(rows)
        assert got['ranking']==[(n,(Fraction(r,i).numerator,Fraction(r,i).denominator)) for n,i,r in expected]
        total=Fraction(sum(r for n,i,r in rows),sum(i for n,i,r in rows));assert got['aggregate_rate']==(total.numerator,total.denominator)
        assert got['claim']=='PARTIAL' and got['improvement_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('rows,message',[
 (L([('a',1,0)]),'rows must be an exact list with 1..50 entries'),
 ([], 'rows must be an exact list with 1..50 entries'),
 ([(str(i),1,0) for i in range(51)],'rows must be an exact list with 1..50 entries'),
 ([T(('a',1,0))],'row must be an id invited responded tuple'),
 ([('a',1,0,0)],'row must be an id invited responded tuple'),
 *[([(x,1,0)],'IDs must be unique nonblank exact strings of 1..80 characters') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([('a',x,0)],'invited must be an integer in 1..10000') for x in (True,I(1),0,10001,1.5)],
 *[([('a',1,x)],'responded must be an integer in 0..invited') for x in (True,I(0),-1,2,1.5)],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:compare(rows)
    assert str(exc.value)==message


def test_caps_full_zero_and_ties():
    assert compare([(str(i),10000,10000) for i in range(50)])['aggregate_rate']==(1,1)
    assert compare([('x'*80,1,0)])['aggregate_rate']==(0,1)
    assert compare([('b',1,1),('a',2,2)])['ranking'][0][0]=='a'
    assert compare([('\u200b',1,0)])['ranking'][0][0]=='\u200b'

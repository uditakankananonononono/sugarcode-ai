from fractions import Fraction
from functools import cmp_to_key
import random
import pytest
from sugarcode.extra_doc.natural_capital1719 import compare


def test_independent_cross_product_sort_oracle():
    rng=random.Random(1719)
    def comparator(a,b):
        delta=a[2]*b[1]-b[2]*a[1]
        return (delta>0)-(delta<0) if delta else (a[0]>b[0])-(a[0]<b[0])
    for _ in range(100):
        rows=[(str(i),rng.randrange(1,10001),rng.randrange(10001)) for i in range(15)]
        expected=sorted(rows,key=cmp_to_key(comparator));got=compare(rows)
        assert got['ranking']==[(n,(Fraction(r,o).numerator,Fraction(r,o).denominator)) for n,o,r in expected]
        total=Fraction(sum(r for n,o,r in rows),sum(o for n,o,r in rows));assert got['overall']==(total.numerator,total.denominator)
        assert got['claim']=='PARTIAL' and got['sustainability_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('rows,message',[
 (L([('a',1,0)]),'rows must be an exact list with 1..50 entries'),
 ([], 'rows must be an exact list with 1..50 entries'),
 ([(str(i),1,0) for i in range(51)],'rows must be an exact list with 1..50 entries'),
 ([T(('a',1,0))],'row must be an id output resource tuple'),
 ([('a',1,0,0)],'row must be an id output resource tuple'),
 *[([(x,1,0)],'IDs must be unique nonblank exact strings of 1..80 characters') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([('a',x,0)],'output must be an integer in 1..10000') for x in (True,I(1),0,10001,1.5)],
 *[([('a',1,x)],'resource must be an integer in 0..10000') for x in (True,I(0),-1,10001,1.5)],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:compare(rows)
    assert str(exc.value)==message


def test_maxima_ties_zero_resource():
    assert compare([(str(i),10000,10000) for i in range(50)])['overall']==(1,1)
    assert compare([('x'*80,1,0)])['overall']==(0,1)
    assert compare([('b',2,2),('a',1,1)])['ranking'][0][0]=='a'
    assert compare([('\u200b',1,0)])['ranking'][0][0]=='\u200b'

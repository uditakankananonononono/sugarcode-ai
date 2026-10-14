import itertools
from fractions import Fraction
import pytest
from sugarcode.extra_doc.hypothesis1021 import test as solve


def test_independent_coin_sequence_oracle():
    for n in range(1,11):
        counts=[0]*(n+1)
        for bits in itertools.product((0,1),repeat=n):counts[sum(bits)]+=1
        for s in range(n+1):
            p=Fraction(sum(v for v in counts if v<=counts[s]),2**n)
            got=solve(s,n,(1,2))
            assert got['p']==(p.numerator,p.denominator) and got['reject']==(p<=Fraction(1,2))
            assert got['claim']=='PARTIAL' and got['assumptions_validated'] is False

class I(int):pass
class T(tuple):pass

@pytest.mark.parametrize('s,n,a,message',[
 *[(0,x,(1,2),'trials must be an integer in 1..100') for x in (True,I(1),0,101)],
 *[(x,1,(1,2),'successes must be an integer in 0..trials') for x in (True,I(0),-1,2)],
 *[(0,1,x,'alpha must be an exact integer fraction tuple with 1<=num<den<=10000') for x in (T((1,2)),[1,2],(True,2),(I(1),2),(0,2),(2,2),(1,10001))],
])
def test_invalid(s,n,a,message):
    with pytest.raises(ValueError) as exc:solve(s,n,a)
    assert str(exc.value)==message


def test_exact_equality_symmetry_endpoints():
    assert solve(0,2,(1,2))['reject'] is True
    assert solve(100,100,(1,10000))['p']==solve(0,100,(1,10000))['p']
    assert solve(50,100,(1,10000))['p']==(1,1)

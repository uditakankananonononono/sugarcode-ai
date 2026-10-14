import itertools
import pytest
from sugarcode.extra_doc.zkp589 import check


def repeated(base, exponent):
    out=1
    for _ in range(exponent):out=(out*base)%23
    return out


def test_full_toy_equation_independent_multiplication_oracle():
    subgroup=[repeated(2,i) for i in range(1,11)]
    for y,t,c,s in itertools.product(subgroup,subgroup,range(11),range(11)):
        got=check(y,t,c,s)
        assert got['equation_valid']==(repeated(2,s)==(t*repeated(y,c))%23)
        assert got['security_validated'] is False and got['claim']=='PARTIAL'


def test_constructed_and_changed_transcripts():
    for secret,nonce,c in itertools.product(range(1,11),range(1,11),range(11)):
        y,t=repeated(2,secret),repeated(2,nonce)
        s=(nonce+c*secret)%11
        assert check(y,t,c,s)['equation_valid'] is True
        assert check(y,t,c,(s+1)%11)['equation_valid'] is False

class I(int):pass

@pytest.mark.parametrize('index,bad,message',[
 *[(i,x,'public and commitment must be nonidentity members of the toy subgroup') for i in (0,1) for x in (True,I(2),1,23,5,None)],
 *[(i,x,'challenge and response must be integers in 0..10') for i in (2,3) for x in (True,I(0),-1,11,None)],
])
def test_exact_input_messages(index,bad,message):
    args=[2,2,0,1];args[index]=bad
    with pytest.raises(ValueError) as exc:check(*args)
    assert str(exc.value)==message

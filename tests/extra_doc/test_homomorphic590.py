import math
import itertools
import pytest
from sugarcode.extra_doc.homomorphic590 import combine_ciphertexts as run


def test_small_paillier_addition_independent_decryption_oracle():
    # Insecure tiny fixture n=3*5, g=n+1. Production key generation is excluded.
    n=15;lam=4;mu=4
    def encrypt(m,r):return pow(n+1,m,n*n)*pow(r,n,n*n)%(n*n)
    def decrypt(c):return ((pow(c,lam,n*n)-1)//n*mu)%n
    for a,b,w1,w2 in itertools.product((0,1,7,14),(0,2,8),(0,1,3),(0,1,2)):
        assert decrypt(run(n,[(encrypt(a,2),w1),(encrypt(b,7),w2)]))==(a*w1+b*w2)%n


@pytest.mark.parametrize('bad',[None,True,1.0,'15',[],{}])
def test_modulus_type(bad):
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(bad,[(1,1)])


@pytest.mark.parametrize('bad',[2,2**4096+1,10**10000],ids=['low','upper','huge'])
def test_modulus_caps_before_rows(bad):
    with pytest.raises(ValueError,match='^integer outside declared range$'):run(bad,[None])


@pytest.mark.parametrize('bad',[None,(),{},True])
def test_outer_type(bad):
    with pytest.raises(TypeError,match='^exact list required$'):run(15,bad)


@pytest.mark.parametrize('n',[0,33])
def test_row_caps(n):
    with pytest.raises(ValueError,match='^row count must be 1..32$'):run(15,[None]*n)


@pytest.mark.parametrize('bad',[None,[],{},True,'x'])
def test_row_type(bad):
    with pytest.raises(TypeError,match='^exact tuple row required$'):run(15,[bad])


@pytest.mark.parametrize('n',[0,1,3])
def test_row_arity(n):
    with pytest.raises(ValueError,match='^row arity must be two$'):run(15,[(None,)*n])


@pytest.mark.parametrize('slot',range(2))
@pytest.mark.parametrize('bad',[None,True,1.0,'1',[],{}])
def test_slot_type(slot,bad):
    row=[2,1];row[slot]=bad
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(15,[tuple(row)])


@pytest.mark.parametrize('row',[(0,1),(225,1),(2,-1),(2,1025)])
def test_slot_caps(row):
    with pytest.raises(ValueError,match='^integer outside declared range$'):run(15,[row])


def test_units_endpoints_empty_weight_identity_and_order():
    with pytest.raises(ValueError,match='^ciphertext must be a unit modulo modulus$'):run(15,[(3,0)])
    assert run(3,[(1,0),(8,1024)])==1
    assert run(2**4096,[(1,1)])==1
    assert run(15,[(2,1)]*32)==pow(2,32,225)
    rows=[(2,3),(7,2)];assert run(15,rows)==run(15,list(reversed(rows)))
    assert run(15,rows)==pow(2,3,225)*pow(7,2,225)%225

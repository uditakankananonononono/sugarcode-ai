from fractions import Fraction as F
from math import comb
import pytest
from sugarcode.extra_doc.thompson_sampling import thompson_sampling


def cdf_oracle(a,b,x):
    # Integer Beta CDF equals binomial upper tail, independent of density integral.
    n=a+b-1
    return sum(F(comb(n,k))*x**k*(1-x)**(n-k) for k in range(a,n+1))


def test_beta_posterior_quantiles_independent():
    r=thompson_sampling([(2,1),(0,2)],[F(1,3),F(2,3)],prior=(1,1),bits=6)
    assert r['posterior']==[(3,2),(1,3)]
    for (a,b),q,(lo,hi) in zip(r['posterior'],[F(1,3),F(2,3)],r['draw_brackets']):
        assert cdf_oracle(a,b,lo)<=q<=cdf_oracle(a,b,hi)
        assert hi-lo==F(1,64)
    assert r['chosen_arm']==0


def test_uniform_ties_and_endpoints():
    r=thompson_sampling([(0,0),(0,0)],[F(1,2),F(1,2)],bits=4)
    assert r['draw_brackets']==[(F(1,2),F(1,2))]*2 and r['chosen_arm']==0
    r=thompson_sampling([(0,0),(0,0)],[F(0),F(1)],bits=1)
    assert r['draw_brackets']==[(0,0),(1,1)] and r['chosen_arm']==1


def test_overlapping_draws_unresolved():
    r=thompson_sampling([(0,0),(1,0)],[F(1,3),F(1,4)],bits=1)
    assert r['chosen_arm'] is None


@pytest.mark.parametrize('feedback',[[],[(0,0)]*5,None,(),[(True,0)],[(1.,0)],[(21,0)],[(0,-1)],[(1,)],[(1,2,3)]])
def test_feedback_refuse(feedback):
    with pytest.raises((TypeError,ValueError)):thompson_sampling(feedback,[F(1,2)])


@pytest.mark.parametrize('quantiles',[None,(),[],[True],[.5],[F(-1,2)],[F(3,2)],[F(1,10**101)]])
def test_quantile_refuse(quantiles):
    with pytest.raises((TypeError,ValueError)):thompson_sampling([(0,0)],quantiles)


@pytest.mark.parametrize('prior',[(0,1),(1,0),(11,1),(True,1),(1.,1),None,(1,),[1,1]])
def test_prior_refuse(prior):
    with pytest.raises((TypeError,ValueError)):thompson_sampling([(0,0)],[F(0)],prior=prior)


@pytest.mark.parametrize('bits',[0,17,True,1.,None])
def test_bits_refuse(bits):
    with pytest.raises((TypeError,ValueError)):thompson_sampling([(0,0)],[F(0)],bits=bits)


def test_end_caps_and_no_scan():
    class Rows(list):
        def __iter__(self):raise AssertionError('oversized scanned')
    with pytest.raises(ValueError):thompson_sampling(Rows([None]*5),[F(0)])
    r=thompson_sampling([(20,20)]*4,[F(1,2)]*4,prior=(10,10),bits=16)
    assert r['posterior']==[(30,30)]*4
    assert r['draw_brackets']==[(F(1,2),F(1,2))]*4


def test_grid_crosscheck():
    for success in range(3):
        for fail in range(3):
            for q in [F(1,5),F(2,5),F(4,5)]:
                r=thompson_sampling([(success,fail)],[q],bits=5)
                lo,hi=r['draw_brackets'][0]
                assert cdf_oracle(success+1,fail+1,lo)<=q<=cdf_oracle(success+1,fail+1,hi)

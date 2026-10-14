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


def test_literal_defaults_schema_messages_and_integer_quantiles():
    import inspect
    sig=inspect.signature(thompson_sampling)
    assert sig.parameters['bits'].default==8
    assert sig.parameters['prior'].default==(1,1)
    assert thompson_sampling([(0,0)],[F(1,3)])==thompson_sampling([(0,0)],[F(1,3)],bits=8,prior=(1,1))
    assert thompson_sampling([(0,0)],[0])['draw_brackets']==[(0,0)]
    assert thompson_sampling([(0,0)],[1])['draw_brackets']==[(1,1)]
    with pytest.raises(ValueError,match='integer budget'):thompson_sampling([(0,0)],[2])
    for rows in (None,(),[],[(0,0)]*5):
        with pytest.raises(ValueError,match='^arm budget 1..4 required$'):
            thompson_sampling(rows,[0])
    for row in (None,[0,0],(1,),(1,2,3)):
        with pytest.raises(ValueError,match='^success/failure pair required$'):
            thompson_sampling([row],[0])


def test_rational_size_exact_boundaries():
    assert thompson_sampling([(0,0)],[F(1,10**100)],bits=1)['draw_brackets']==[(0,F(1,2))]
    for q in (F(10**100+1),F(1,10**100+1),F(10**101),F(1,10**101)):
        with pytest.raises(ValueError,match='^rational size budget exceeded$'):
            thompson_sampling([(0,0)],[q])
    # Numerator exactly at cap passes size preflight and fails range, not size.
    with pytest.raises(ValueError,match='^quantile range 0..1 required$'):
        thompson_sampling([(0,0)],[F(10**100)])
    q=F(10**99+1,2*10**99+1)
    assert thompson_sampling([(0,0)],[q],bits=1)['draw_brackets']==[(F(1,2),1)]


def test_nonzero_lower_and_upper_initial_brackets():
    assert thompson_sampling([(0,0)],[F(1,3)],bits=1)['draw_brackets']==[(0,F(1,2))]
    assert thompson_sampling([(0,0)],[F(2,3)],bits=1)['draw_brackets']==[(F(1,2),1)]

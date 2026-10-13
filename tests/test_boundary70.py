from fractions import Fraction
from decimal import Decimal,localcontext
import pytest
from sugarcode.modules.bioplayground.boundary_diversity import diversity_metrics

@pytest.mark.parametrize('freq',[[1,0],[.5,.5],[.25,.75],[.25]*4])
def test_independent_oracle(freq):
    r=diversity_metrics(freq)
    assert r['heterozygosity']==float(1-sum(Fraction(str(x))**2 for x in freq))
    with localcontext() as ctx:
        ctx.prec=60
        e=-sum(Decimal(str(x))*Decimal(str(x)).ln() for x in freq if x)
        assert r['shannon_entropy']==pytest.approx(float(e))
        assert r['effective_alleles']==pytest.approx(float(e.exp()))

@pytest.mark.parametrize('freq',[[],[True,0],['.5',.5],[float('nan'),0],[float('inf'),0],[10**10000,0],[-1,2],[.2,.2],[0]*10001])
def test_invalid(freq):
    with pytest.raises(ValueError):diversity_metrics(freq)

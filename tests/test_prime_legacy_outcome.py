"""Legacy unfitted distribution arithmetic, not biological validation."""
import math
import pytest
from sugarcode.modules.prime_design.core import _outcome_distribution


@pytest.mark.parametrize('tm,length',[(35.985669961447094,10),(29.718521,17),(32.001,12)])
def test_legacy_distribution_has_exact_unit_mass(tm,length):
    r=_outcome_distribution({'pbs_tm_c':tm,'rtt_length':length})
    assert sum(r.values())==pytest.approx(1,abs=1e-12)
    assert all(math.isfinite(x) and 0<=x<=1 for x in r.values())


@pytest.mark.parametrize('peg',[
    {'pbs_tm_c':float('nan'),'rtt_length':14},
    {'pbs_tm_c':float('inf'),'rtt_length':14},
    {'pbs_tm_c':True,'rtt_length':14},
    {'pbs_tm_c':32,'rtt_length':True},
    {'pbs_tm_c':32,'rtt_length':14.5},
    {'pbs_tm_c':32,'rtt_length':1000}, {},
])
def test_legacy_bad_domains_rejected(peg):
    with pytest.raises(ValueError):_outcome_distribution(peg)

import numpy as np
from sugarcode.modules.cellfatenet.core import identify_attractors

def test_short_relaxation_endpoints_not_automatically_stable_attractors():
    r=identify_attractors(starts=2,hours=.001)
    assert r['attractors']==[]
    assert r['unresolved_endpoint_count']==2
    assert r['basin_scope']=='Fraction of supplied random starts, not global basin volume'

def test_claimed_attractors_have_checked_residual_and_jacobian():
    r=identify_attractors(starts=4,hours=150)
    assert r['attractors']
    for a in r['attractors']:
        assert a['fixed_point_residual_inf']<1e-5
        assert a['max_jacobian_real_eigenvalue']<0
        assert a['stability']=='locally asymptotically stable numerical fixed point'
        assert np.isfinite(a['max_jacobian_real_eigenvalue'])
    assert sum(x['basin_fraction'] for x in r['attractors'])<=1

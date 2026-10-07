import numpy as np
from sugarcode.modules.cellfatenet.core import optimal_reprogramming

def test_sparse_control_refits_returned_support_and_reports_improvement():
    result=optimal_reprogramming({}, {'TNNT2':2,'MYH6':2},hours=2,max_factors=1)
    assert result['sparse_refit_converged'] is True
    assert result['objective'] <= result['truncated_objective']+1e-8
    assert len(result['interventions'])<=1
    assert result['solver']=='L-BFGS-B dense support selection plus fixed-support sparse refit; not global sparse optimum'
    assert all(np.isfinite(x['control']) for x in result['interventions'])

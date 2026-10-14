import pytest
from sugarcode.extra_doc.co_design import consensus_design as solve


def test_maximin_surplus_then_total_and_first_index_oracle():
    r=solve([[5,1],[3,3],[3,4],[9,-1]],[1,0])
    #surpluses4/1min1;2/3min2;2/4min2total6;8/-1infeasible.
    assert r=={'candidate_index':2,'stakeholder_surpluses':[2,4],'minimum_surplus':2,
              'total_surplus':6,'feasible_indices':[0,1,2],'collaboration_performed':False}
    assert solve([[1],[1]],[1])['candidate_index']==0


def test_signed_boundaries_zero_surplus_caps_and_infeasible():
    r=solve([[1000]*8]*64,[-1000]*8)
    assert r['minimum_surplus']==2000 and r['total_surplus']==16000 and len(r['feasible_indices'])==64
    assert solve([[-1000]],[-1000])['minimum_surplus']==0
    with pytest.raises(ValueError,match='^no design meets every stakeholder minimum$'):
        solve([[-1]],[0])

@pytest.mark.parametrize('args,error,message',[
 ((None,[]),TypeError,'utilities and minimums must be lists or tuples'),
 (([],[0]),ValueError,'candidate count must be between 1 and 64'),
 (([None]*65,[0]),ValueError,'candidate count must be between 1 and 64'),
 (([[0]],[]),ValueError,'stakeholder count must be between 1 and 8'),
 (([[0]],[None]*9),ValueError,'stakeholder count must be between 1 and 8'),
 (([[]],[0]),ValueError,'utility rows must match stakeholders'),
 (([[True]],[0]),ValueError,'utilities must be nonbool integers between -1000 and 1000'),
 (([[-1001]],[0]),ValueError,'utilities must be nonbool integers between -1000 and 1000'),
 (([[1001]],[0]),ValueError,'utilities must be nonbool integers between -1000 and 1000'),
 (([[0]],[True]),ValueError,'minimums must be nonbool integers between -1000 and 1000'),
 (([[0]],[-1001]),ValueError,'minimums must be nonbool integers between -1000 and 1000'),
 (([[0]],[1001]),ValueError,'minimums must be nonbool integers between -1000 and 1000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

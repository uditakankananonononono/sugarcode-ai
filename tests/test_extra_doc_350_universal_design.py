import pytest
from sugarcode.extra_doc.universal_design import choose_universal_candidate as solve


def test_all_profile_feasibility_minimax_then_total_oracle():
    r=solve([[1,5],[3,3],[2,3],[0,0]],[[1,1],[1,1],[1,1],[1,0]],[3,5])
    assert r=={'candidate_index':2,'profile_efforts':[2,3],'worst_effort':3,
              'feasible_indices':[0,1,2],'universal_accessibility_validated':False}
    assert solve([[1],[1]],[[1],[1]],[1])['candidate_index']==0


def test_zero_effort_equal_limit_and_max_caps():
    assert solve([[0]],[[1]],[0])['worst_effort']==0
    r=solve([[1000000]*8]*64,[[1]*8]*64,[1000000]*8)
    assert len(r['feasible_indices'])==64 and r['candidate_index']==0
    with pytest.raises(ValueError,match='^no candidate satisfies every supplied profile$'):
        solve([[2]],[[1]],[1])
    with pytest.raises(ValueError,match='^no candidate satisfies every supplied profile$'):
        solve([[0]],[[0]],[0])

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[]),TypeError,'inputs must be lists or tuples'),
 (([],[],[0]),ValueError,'candidate count must be between 1 and 64'),
 (([None]*65,[],[0]),ValueError,'candidate count must be between 1 and 64'),
 (([[0]],[[1]],[]),ValueError,'profile count must be between 1 and 8'),
 (([[0]],[[1]],[None]*9),ValueError,'profile count must be between 1 and 8'),
 (([[0]],[],[0]),ValueError,'availability rows must match candidates'),
 (([[]],[[1]],[0]),ValueError,'rows must match profile count'),
 (([[True]],[[1]],[0]),ValueError,'efforts must be nonbool integers zero through 1000000'),
 (([[-1]],[[1]],[0]),ValueError,'efforts must be nonbool integers zero through 1000000'),
 (([[1000001]],[[1]],[0]),ValueError,'efforts must be nonbool integers zero through 1000000'),
 (([[0]],[[True]],[0]),ValueError,'availability must be nonbool binary integers'),
 (([[0]],[[2]],[0]),ValueError,'availability must be nonbool binary integers'),
 (([[0]],[[1]],[True]),ValueError,'maximum efforts must be nonbool integers zero through 1000000'),
 (([[0]],[[1]],[-1]),ValueError,'maximum efforts must be nonbool integers zero through 1000000'),
 (([[0]],[[1]],[1000001]),ValueError,'maximum efforts must be nonbool integers zero through 1000000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

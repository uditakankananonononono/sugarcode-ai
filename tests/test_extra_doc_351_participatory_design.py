import pytest
from sugarcode.extra_doc.participatory_design import participatory_vote as solve


def test_independent_rank_score_contributions_oracle():
    r=solve([[2,0,1],[1,2]],[2,1],3)
    assert r=={'scores':[4,5,8],'participant_contributions':[[4,2,6],[0,3,2]],
              'winner_indices':[2],'consultation_performed':False}


def test_empty_ballots_zero_weights_ties_and_caps():
    assert solve([[]],[1],2)['winner_indices']==[0,1]
    assert solve([[0]],[0],1)['scores']==[0]
    r=solve([list(range(8))]*32,[1000000]*32,8)
    assert r['scores']==[32000000*i for i in range(8,0,-1)]
    assert solve([[0,1],[1,0]],[1,1],2)['winner_indices']==[0,1]

@pytest.mark.parametrize('args,error,message',[
 ((None,[],1),TypeError,'ballots and weights must be lists or tuples'),
 (([],[],1),ValueError,'participant count must be between 1 and 32'),
 (([None]*33,[],1),ValueError,'participant count must be between 1 and 32'),
 (([[]],[1],True),ValueError,'candidate_count must be a nonbool integer between 1 and 8'),
 (([[]],[1],0),ValueError,'candidate_count must be a nonbool integer between 1 and 8'),
 (([[]],[1],9),ValueError,'candidate_count must be a nonbool integer between 1 and 8'),
 (([[]],[],1),ValueError,'weight count must match participants'),
 (([None],[1],1),ValueError,'ballots must be lists or tuples no longer than candidate count'),
 (([[0,1]],[1],1),ValueError,'ballots must be lists or tuples no longer than candidate count'),
 (([[True]],[1],1),ValueError,'ballot indices must be nonbool integers inside candidate range'),
 (([[-1]],[1],1),ValueError,'ballot indices must be nonbool integers inside candidate range'),
 (([[1]],[1],1),ValueError,'ballot indices must be nonbool integers inside candidate range'),
 (([[0,0]],[1],2),ValueError,'ballot candidates must be unique'),
 (([[]],[True],1),ValueError,'weights must be nonbool integers zero through 1000000'),
 (([[]],[-1],1),ValueError,'weights must be nonbool integers zero through 1000000'),
 (([[]],[1000001],1),ValueError,'weights must be nonbool integers zero through 1000000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

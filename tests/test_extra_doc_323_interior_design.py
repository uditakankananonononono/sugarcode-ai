import pytest
from sugarcode.extra_doc.interior_design import plan_interior as solve


def test_four_candidate_overlap_and_function_cost_oracle():
    a=[(0,0,2,2,5),(2,0,2,2,1)];b=[(2,0,2,2,2),(0,2,2,2,4)]
    # (0,0)cost7,(0,1)cost9,(1,0)overlap,(1,1)cost5.
    r=solve(4,4,[a,b])
    assert r=={'placement_indices':[1,1],'rectangles':[[2,0,2,2],[0,2,2,2]],
              'functional_cost':5,'candidate_count':4,'feasible_count':3,'building_compliance_validated':False}


def test_edge_contact_tie_and_max_shape():
    assert solve(2,1,[[(0,0,1,1,0)],[(1,0,1,1,0)]])['feasible_count']==1
    r=solve(1000,1000,[[(i,0,1,1,1000000)]*4 for i in range(6)])
    assert r['placement_indices']==[0]*6 and r['candidate_count']==4096 and r['functional_cost']==6000000
    with pytest.raises(ValueError,match='^no nonoverlapping interior plan exists$'):
        solve(1,1,[[(0,0,1,1,0)],[(0,0,1,1,0)]])

@pytest.mark.parametrize('args,error,message',[
 ((True,1,[]),ValueError,'room dimensions must be nonbool integers between 1 and 1000'),
 ((0,1,[]),ValueError,'room dimensions must be nonbool integers between 1 and 1000'),
 ((1,1001,[]),ValueError,'room dimensions must be nonbool integers between 1 and 1000'),
 ((1,1,None),TypeError,'placements must be a list or tuple'),
 ((1,1,[]),ValueError,'item count must be between 1 and 6'),
 ((1,1,[None]*7),ValueError,'item count must be between 1 and 6'),
 ((1,1,[[]]),ValueError,'each item must have between 1 and 4 placements'),
 ((1,1,[[None]*5]),ValueError,'each item must have between 1 and 4 placements'),
 ((1,1,[[None]]),ValueError,'placements must contain x y width height cost'),
 ((1,1,[[(True,0,1,1,0)]]),TypeError,'placement fields must be nonbool integers'),
 ((1,1,[[(0,0,0,1,0)]]),ValueError,'placement geometry must be inside room bounds'),
 ((2,2,[[(1,0,2,1,0)]]),ValueError,'placement geometry must be inside room bounds'),
 ((1,1,[[(0,0,1,1,-1)]]),ValueError,'costs must be between zero and 1000000'),
 ((1,1,[[(0,0,1,1,1000001)]]),ValueError,'costs must be between zero and 1000000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

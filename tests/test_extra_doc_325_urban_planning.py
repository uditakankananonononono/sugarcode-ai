import pytest
from sugarcode.extra_doc.urban_planning import select_facilities as solve


def test_three_facility_subset_oracle_weighted_nearest_assignment():
    # Residents0/10withweights1/3,candidates0/5/10;onefacilitycost30/20/10.
    r=solve([(0,0),(10,0)],[1,3],[(0,0),(5,0),(10,0)],1)
    assert r=={'facility_indices':[2],'resident_assignments':[2,2],'resident_distances':[10,0],
              'weighted_distance':10,'evaluated_subsets':3,'equity_validated':False}
    assert solve([(0,0),(10,0)],[1,3],[(0,0),(5,0),(10,0)],2)['facility_indices']==[0,2]


def test_manhattan_tie_and_caps():
    assert solve([(1,1)],[1],[(0,0),(2,2)],1)['facility_indices']==[0]
    assert solve([(1,1)],[1],[(0,0),(2,2)],2)['resident_assignments']==[0]
    r=solve([(-1000,-1000)]*32,[1000000]*32,[(1000,1000)]*12,6)
    assert r['evaluated_subsets']==924 and r['weighted_distance']==128000000000

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[],1),TypeError,'inputs must be lists or tuples'),
 (([],[],[(0,0)],1),ValueError,'resident count must be between 1 and 32'),
 (([None]*33,[],[(0,0)],1),ValueError,'resident count must be between 1 and 32'),
 (([(0,0)],[1],[],1),ValueError,'candidate count must be between 1 and 12'),
 (([(0,0)],[1],[None]*13,1),ValueError,'candidate count must be between 1 and 12'),
 (([(0,0)],[],[(0,0)],1),ValueError,'weights must match residents'),
 (([(0,0)],[1],[(0,0)],True),ValueError,'facility_count must be a nonbool integer inside candidate range'),
 (([(0,0)],[1],[(0,0)],0),ValueError,'facility_count must be a nonbool integer inside candidate range'),
 (([(0,0)],[1],[(0,0)],2),ValueError,'facility_count must be a nonbool integer inside candidate range'),
 (([None],[1],[(0,0)],1),ValueError,'points must have two coordinates'),
 (([(True,0)],[1],[(0,0)],1),ValueError,'coordinates must be nonbool integers between -1000 and 1000'),
 (([(-1001,0)],[1],[(0,0)],1),ValueError,'coordinates must be nonbool integers between -1000 and 1000'),
 (([(1001,0)],[1],[(0,0)],1),ValueError,'coordinates must be nonbool integers between -1000 and 1000'),
 (([(0,0)],[True],[(0,0)],1),ValueError,'weights must be nonbool integers zero through 1000000'),
 (([(0,0)],[-1],[(0,0)],1),ValueError,'weights must be nonbool integers zero through 1000000'),
 (([(0,0)],[1000001],[(0,0)],1),ValueError,'weights must be nonbool integers zero through 1000000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

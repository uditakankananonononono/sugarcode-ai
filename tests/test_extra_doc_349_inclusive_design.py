import pytest
from sugarcode.extra_doc.inclusive_design import inclusive_features as solve


def test_explicit_four_subset_coverage_cost_oracle():
    r=solve([[1,0],[1,1]],[1,3],[1,1])
    assert r=={'feature_indices':[1],'coverage_counts':[1,1],'cost':3,'feasible_count':2,'representation_validated':False}
    assert solve([[1,0],[1,1]],[1,3],[2,1])['feature_indices']==[0,1]


def test_zero_minimum_empty_tie_feature_count_then_index_and_caps():
    assert solve([[1]],[0],[0])['feature_indices']==[]
    assert solve([[1],[1]],[0,0],[1])['feature_indices']==[0]
    r=solve([[1]*8]*12,[1000000]*12,[12]*8)
    assert r['cost']==12000000 and r['coverage_counts']==[12]*8
    with pytest.raises(ValueError,match='^no feature selection covers supplied perspectives$'):
        solve([[0]],[1],[1])

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[]),TypeError,'inputs must be lists or tuples'),
 (([],[],[0]),ValueError,'feature count must be between 1 and 12'),
 (([None]*13,[],[0]),ValueError,'feature count must be between 1 and 12'),
 (([[0]],[0],[]),ValueError,'perspective count must be between 1 and 8'),
 (([[0]],[0],[None]*9),ValueError,'perspective count must be between 1 and 8'),
 (([[0]],[],[0]),ValueError,'cost count must match features'),
 (([[]],[0],[0]),ValueError,'coverage rows must match perspectives'),
 (([[True]],[0],[0]),ValueError,'coverage must be nonbool binary integers'),
 (([[2]],[0],[0]),ValueError,'coverage must be nonbool binary integers'),
 (([[0]],[True],[0]),ValueError,'costs must be nonbool integers zero through 1000000'),
 (([[0]],[-1],[0]),ValueError,'costs must be nonbool integers zero through 1000000'),
 (([[0]],[1000001],[0]),ValueError,'costs must be nonbool integers zero through 1000000'),
 (([[0]],[0],[True]),ValueError,'minimum counts must be nonbool integers inside feature range'),
 (([[0]],[0],[-1]),ValueError,'minimum counts must be nonbool integers inside feature range'),
 (([[0]],[0],[2]),ValueError,'minimum counts must be nonbool integers inside feature range'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

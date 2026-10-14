import pytest
from sugarcode.extra_doc.landscape_design import zone_landscape as solve


def test_complete_two_cell_zone_count_adjacency_oracle():
    # Four configs:00/11lackonezone;01cost2;10cost5.
    r=solve([[0,1],[0,1]],[[1,3],[2,1]],[1,1],[(0,1)],[])
    assert r=={'zones':[0,1],'zone_counts':[1,1],'cost':2,'feasible_count':2,'ecology_validated':False}
    with pytest.raises(ValueError,match='^no landscape satisfies zone constraints$'):
        solve([[0,1],[0,1]],[[1,3],[2,1]],[1,1],[(0,1)],[(1,0)])


def test_tie_supplied_order_and_max_caps():
    assert solve([[1,0]],[[0,0]],[0,0],[],[])['zones']==[1]
    r=solve([[0,1,2,3]]*6,[[1000000]*4]*6,[0]*4,[(0,1)]*15,[])
    assert r['feasible_count']==4096 and r['cost']==6000000
    assert solve([[0]],[[0]],[1],[],[])['zone_counts']==[1]

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[],[],[]),TypeError,'inputs must be lists or tuples'),
 (([],[],[0],[],[]),ValueError,'cell count must be between 1 and 6'),
 (([None]*7,[],[0],[],[]),ValueError,'cell count must be between 1 and 6'),
 (([[0]],[[0]],[],[],[]),ValueError,'zone count must be between 1 and 4'),
 (([[0]],[[0]],[None]*5,[],[]),ValueError,'zone count must be between 1 and 4'),
 (([[0]],[],[0],[],[]),ValueError,'cost rows must match cells'),
 (([[0]],[[0]],[0],[None]*16,[]),ValueError,'adjacency and forbidden caps are 15 and 16'),
 (([[]],[[0]],[0],[],[]),ValueError,'each cell must have between 1 and 4 options'),
 (([[0]],[[]],[0],[],[]),ValueError,'cost rows must match zone count'),
 (([[True]],[[0]],[0],[],[]),ValueError,'zone options must be nonbool indices inside zone range'),
 (([[0,0]],[[0]],[0],[],[]),ValueError,'cell options must be unique'),
 (([[0]],[[0]],[True],[],[]),ValueError,'minimum counts must be nonbool integers inside cell range'),
 (([[0]],[[1000001]],[0],[],[]),ValueError,'costs must be nonbool integers zero through 1000000'),
 (([[0]],[[0]],[0],[None],[]),ValueError,'pairs must contain two indices'),
 (([[0]],[[0]],[0],[],[(0,1)]),ValueError,'pair indices must be nonbool integers inside corresponding range'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

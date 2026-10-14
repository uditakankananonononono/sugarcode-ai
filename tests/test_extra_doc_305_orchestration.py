import pytest
from sugarcode.extra_doc.orchestration import assign_instruments as solve


def test_two_part_range_and_cost_oracle():
    r=solve([(40,60),(65,80)],[(30,70),(50,90),(0,127)],[[1,0,3],[0,2,1]])
    # legal(0,1)=3,(0,2)=2,(2,1)=5;part0 cannot instrument1,part1 cannot0.
    assert r=={'instrument_indices':[0,2],'compatibility_cost':2,
              'feasible_assignment_count':3,'timbral_quality_validated':False}


def test_tie_first_tuple_range_equality_and_max_shape():
    assert solve([(60,60)],[(60,60),(0,127)],[[0,0]])['instrument_indices']==[0]
    r=solve([(0,127)]*8,[(0,127)]*8,[[1000000]*8]*8)
    assert r['instrument_indices']==list(range(8)) and r['feasible_assignment_count']==40320
    assert r['compatibility_cost']==8000000
    with pytest.raises(ValueError,match='^no range-compatible distinct assignment exists$'):
        solve([(0,127)],[(1,126)],[[0]])

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[]),TypeError,'inputs must be lists or tuples'),
 (([],[],[]),ValueError,'counts must satisfy 1 <= parts <= instruments <= 8'),
 (([None]*9,[None]*9,[]),ValueError,'counts must satisfy 1 <= parts <= instruments <= 8'),
 (([(0,1)]*2,[(0,1)],[]),ValueError,'counts must satisfy 1 <= parts <= instruments <= 8'),
 (([None],[(0,1)],[[0]]),ValueError,'ranges must contain lower and upper MIDI pitches'),
 (([(0,1)],[(0,1)],[]),ValueError,'cost matrix must match parts and instruments'),
 (([(True,1)],[(0,1)],[[0]]),ValueError,'ranges must be ordered nonbool MIDI integers zero through 127'),
 (([(2,1)],[(0,1)],[[0]]),ValueError,'ranges must be ordered nonbool MIDI integers zero through 127'),
 (([(-1,1)],[(0,1)],[[0]]),ValueError,'ranges must be ordered nonbool MIDI integers zero through 127'),
 (([(0,128)],[(0,127)],[[0]]),ValueError,'ranges must be ordered nonbool MIDI integers zero through 127'),
 (([(0,1)],[(0,1)],[[True]]),ValueError,'costs must be nonbool integers between zero and 1000000'),
 (([(0,1)],[(0,1)],[[-1]]),ValueError,'costs must be nonbool integers between zero and 1000000'),
 (([(0,1)],[(0,1)],[[1000001]]),ValueError,'costs must be nonbool integers between zero and 1000000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message


def test_only_long_cost_row_refused():
    with pytest.raises(ValueError) as exc:solve([(0,1)],[(0,1)],[[0,1]])
    assert str(exc.value)=='cost matrix must match parts and instruments'

import pytest
from sugarcode.extra_doc.rhythm_programming import program_rhythm as solve


def test_explicit_floor_difference_pattern_rotation_and_accent():
    r=solve(8,3)
    assert r=={'pattern':[0,0,1,0,0,1,0,1],'velocities':[0,0,127,0,0,96,0,96],
              'hit_steps':[2,5,7],'cyclic_gaps':[3,2,3],'groove_validated':False}
    assert solve(8,3,2)['pattern']==[0,1,0,0,1,0,0,1]


def test_all_small_counts_independent_gap_and_count_invariants():
    for n in range(1,33):
        for k in range(n+1):
            r=solve(n,k)
            assert sum(r['pattern'])==k and len(r['pattern'])==n
            if k:
                assert sum(r['cyclic_gaps'])==n
                assert set(r['cyclic_gaps'])<={n//k,(n+k-1)//k}
            else:assert r['hit_steps']==[] and r['cyclic_gaps']==[]
    assert solve(128,128,127,1,1)['velocities']==[1]*128
    assert solve(1,1)['cyclic_gaps']==[1]

@pytest.mark.parametrize('args,message',[
 ((True,0),'steps must be a nonbool integer between 1 and 128'),
 ((0,0),'steps must be a nonbool integer between 1 and 128'),
 ((129,0),'steps must be a nonbool integer between 1 and 128'),
 ((4,True),'pulses must be a nonbool integer between zero and steps'),
 ((4,-1),'pulses must be a nonbool integer between zero and steps'),
 ((4,5),'pulses must be a nonbool integer between zero and steps'),
 ((4,1,True),'rotation must be a nonbool integer inside step range'),
 ((4,1,-1),'rotation must be a nonbool integer inside step range'),
 ((4,1,4),'rotation must be a nonbool integer inside step range'),
 ((4,1,0,True),'velocities must be nonbool integers between 1 and 127'),
 ((4,1,0,0),'velocities must be nonbool integers between 1 and 127'),
 ((4,1,0,96,128),'velocities must be nonbool integers between 1 and 127'),
])
def test_errors(args,message):
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)==message

from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.mixing import mix_tracks as solve


def test_exact_linear_mix_and_global_normalization_oracle():
    r=solve([[100,-100,20],[50,50,-20]],[2,1],100)
    # Raw250,-150,20;scale2/5 ->100,-60,8.
    assert r=={'samples':[100,-60,8],'raw_peak':250,'scale':F(2,5),'peak':100,
              'overload_indices':[0,1],'perceptual_balance_validated':False}
    assert solve([[100,-100,20],[50,50,-20]],[2,1],100,False)['samples']==[250,-150,20]


def test_cancellation_ceiling_equality_negative_extreme_and_caps():
    assert solve([[1,-1],[-1,1]],[1,1])['scale']==1
    assert solve([[100]],[1],100)['scale']==1
    assert solve([[-32768]],[1])['samples']==[-32767]
    assert len(solve([[0]*4096]*8,[0]*8)['samples'])==4096
    for value in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve([[1]],[value],32767,False)['raw_peak']==value

@pytest.mark.parametrize('args,error,message',[
 ((None,[]),TypeError,'tracks and gains must be lists or tuples'),
 (([],[]),ValueError,'track count must be between 1 and 8'),
 (([None]*9,[0]*9),ValueError,'track count must be between 1 and 8'),
 (([[0]],[]),ValueError,'gain count must match tracks'),
 (([[]],[1]),ValueError,'tracks must have between 1 and 4096 samples'),
 (([[None]*4097],[1]),ValueError,'tracks must have between 1 and 4096 samples'),
 (([[0],[0,0]],[1,1]),ValueError,'track lengths must agree'),
 (([[0]],[1],True),ValueError,'peak_ceiling must be a nonbool integer between 1 and 32767'),
 (([[0]],[1],0),ValueError,'peak_ceiling must be a nonbool integer between 1 and 32767'),
 (([[0]],[1],32768),ValueError,'peak_ceiling must be a nonbool integer between 1 and 32767'),
 (([[0]],[1],1,0),TypeError,'normalize must be bool'),
 (([[True]],[1]),ValueError,'samples must be nonbool signed 16-bit integers'),
 (([[-32769]],[1]),ValueError,'samples must be nonbool signed 16-bit integers'),
 (([[32768]],[1]),ValueError,'samples must be nonbool signed 16-bit integers'),
 (([[0]],[True]),TypeError,'gains must be nonbool int or Fraction'),
 (([[0]],[-1]),ValueError,'gains must be nonnegative'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('value',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(value):
    with pytest.raises(ValueError,match='^gains must fit 32 bits$'):solve([[0]],[value])


def test_positive_pcm_endpoint_and_overload_strict_equality():
    r=solve([[32767]],[1])
    assert r['samples']==[32767] and r['overload_indices']==[]
    assert solve([[1]],[1],1,False)['overload_indices']==[]

@pytest.mark.parametrize('gains',[{1,2},{0:1}])
def test_gain_container_nonsequence_refused(gains):
    with pytest.raises(TypeError) as exc:solve([[0]],gains)
    assert str(exc.value)=='tracks and gains must be lists or tuples'

@pytest.mark.parametrize('track',[range(3),b'ab'])
def test_track_nonsequence_container_refused(track):
    with pytest.raises(ValueError) as exc:solve([track],[1])
    assert str(exc.value)=='tracks must have between 1 and 4096 samples'

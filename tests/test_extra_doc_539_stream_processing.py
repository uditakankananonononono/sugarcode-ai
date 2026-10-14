import pytest
from sugarcode.extra_doc.stream_processing import window_stream as solve

def test_event_time_watermark_oracle():
    assert solve([[5,2],[10,3],[7,-1],[6,8],[15,4],[12,5]],5,3)=={
      'accepted_indices':[0,1,2,4,5],'late_indices':[3],
      'windows':[[5,10,2,1],[10,15,2,8],[15,20,1,4]],'live_processing_performed':False}
    assert solve([[0,1],[0,-1]],1,0)['windows']==[[0,1,2,0]]
    assert solve([],65536,65536)=={'accepted_indices':[],'late_indices':[],'windows':[],'live_processing_performed':False}
    assert solve([[4294967295,4294967295]]*128,1,0)['windows']==[[4294967295,4294967296,128,128*4294967295]]
    assert solve([[65536,1],[0,2]],65536,65536)['accepted_indices']==[0,1]

@pytest.mark.parametrize('e,error,message',[(None,TypeError,'events must be a list or tuple'),([None]*129,ValueError,'event cap is 128'),([None],ValueError,'events must contain timestamp and value'),([[0]],ValueError,'events must contain timestamp and value'),([[0,0,0]],ValueError,'events must contain timestamp and value')])
def test_shapes(e,error,message):
    with pytest.raises(error) as exc:solve(e,1,0)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,0,65537,None,1.0])
def test_width(bad):
    with pytest.raises(ValueError) as exc:solve([],bad,0)
    assert str(exc.value)=='width must be nonbool integer 1 through 65536'

@pytest.mark.parametrize('bad',[True,-1,65537,None,1.0])
def test_lateness(bad):
    with pytest.raises(ValueError) as exc:solve([],1,bad)
    assert str(exc.value)=='lateness must be nonbool integer 0 through 65536'

@pytest.mark.parametrize('e',[[True,0],[-1,0],[2**32,0],[1.0,0],[0,True],[0,2**32],[0,-(2**32)],[0,None],[0,1.0]])
def test_values(e):
    with pytest.raises(ValueError) as exc:solve([e],1,0)
    assert str(exc.value)=='timestamps must be nonnegative 32-bit and values signed 32-bit magnitude nonbool integers'

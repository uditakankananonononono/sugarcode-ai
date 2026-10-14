import copy
import pytest
from sugarcode.extra_doc.stream_processing import window_stream
class L(list): pass
class T(tuple): pass
class I(int): pass

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses(container):
    with pytest.raises(TypeError,match='^events must be a list or tuple$'):
        window_stream(container([(0,1)]),1,0)
    with pytest.raises(ValueError,match='^events must contain timestamp and value$'):
        window_stream([(0,1),container((1,2))],1,0)

@pytest.mark.parametrize('slot',[0,1])
def test_event_scalar_subclasses_nonfirst(slot):
    event=[1,2];event[slot]=I(event[slot])
    with pytest.raises(ValueError,match='^timestamps must be nonnegative 32-bit and values signed 32-bit magnitude nonbool integers$'):
        window_stream([(0,1),tuple(event)],1,0)

@pytest.mark.parametrize('which',['width','lateness'])
def test_parameter_subclasses(which):
    message='width must be nonbool integer 1 through 65536' if which=='width' else 'lateness must be nonbool integer 0 through 65536'
    with pytest.raises(ValueError,match='^'+message+'$'):
        window_stream([],I(1) if which=='width' else 1,I(0) if which=='lateness' else 0)

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_nonadjacent_max_seen_and_inclusive_watermark(outer,row):
    events=outer(row(e) for e in [(10,1),(7,2),(8,3),(6,4),(15,-1),(12,5),(11,6)])
    before=copy.deepcopy(events)
    assert window_stream(events,5,3)=={
        'accepted_indices':[0,1,2,4,5],'late_indices':[3,6],
        'windows':[[5,10,2,5],[10,15,2,6],[15,20,1,-1]],'live_processing_performed':False}
    assert events==before


def test_half_open_width_edges_signed_values_and_empty():
    bound=2**32-1
    assert window_stream([(4,-bound),(5,bound)],5,0)=={
        'accepted_indices':[0,1],'late_indices':[],
        'windows':[[0,5,1,-bound],[5,10,1,bound]],'live_processing_performed':False}
    assert window_stream([],1,0)=={'accepted_indices':[],'late_indices':[],
                                 'windows':[],'live_processing_performed':False}

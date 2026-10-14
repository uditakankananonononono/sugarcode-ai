import io,wave,struct
import pytest
from sugarcode.extra_doc.sound_design import synthesize_triangle as solve


def test_explicit_triangle_period_pcm_and_wav_roundtrip():
    r=solve(8,16,1000,8000)
    expected=[-1000,-500,0,500,1000,500,0,-500]*2
    assert r['samples']==expected and r['peak_amplitude']==1000 and r['playback_performed'] is False
    with wave.open(io.BytesIO(r['wav_bytes']),'rb') as wav:
        assert (wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes())==(1,2,8000,16)
        assert list(struct.unpack('<16h',wav.readframes(16)))==expected


def test_symmetric_rounding_zero_maximum_shapes_and_defaults():
    import inspect
    assert inspect.signature(solve).parameters['amplitude'].default==8192
    assert inspect.signature(solve).parameters['sample_rate'].default==8000
    r=solve(8,8,3)
    assert r['samples']==[-3,-1,0,1,3,1,0,-1]
    assert sum(r['samples'])==0
    assert solve(4,1,0)['samples']==[0]
    r=solve(1024,4096,32767,48000)
    assert len(r['samples'])==4096 and min(r['samples'])==-32767 and max(r['samples'])==32767

@pytest.mark.parametrize('args,message',[
 ((True,1),'period must be a nonbool multiple of four between 4 and 1024'),
 ((0,1),'period must be a nonbool multiple of four between 4 and 1024'),
 ((1028,1),'period must be a nonbool multiple of four between 4 and 1024'),
 ((5,1),'period must be a nonbool multiple of four between 4 and 1024'),
 ((4,True),'sample_count must be a nonbool integer between 1 and 4096'),
 ((4,0),'sample_count must be a nonbool integer between 1 and 4096'),
 ((4,4097),'sample_count must be a nonbool integer between 1 and 4096'),
 ((4,1,True),'amplitude must be a nonbool integer between zero and 32767'),
 ((4,1,-1),'amplitude must be a nonbool integer between zero and 32767'),
 ((4,1,32768),'amplitude must be a nonbool integer between zero and 32767'),
 ((4,1,1,True),'sample_rate must be a nonbool integer between 8000 and 48000'),
 ((4,1,1,7999),'sample_rate must be a nonbool integer between 8000 and 48000'),
 ((4,1,1,48001),'sample_rate must be a nonbool integer between 8000 and 48000'),
])
def test_errors(args,message):
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)==message

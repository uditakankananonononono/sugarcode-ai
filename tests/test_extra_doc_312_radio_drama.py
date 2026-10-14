import pytest
from sugarcode.extra_doc.radio_drama import compose_radio_drama as solve


def test_audio_cue_overlap_silence_and_timeline_oracle():
    r=solve([('speaker A',0,[10,20,30]),('door',2,[-5,7]),('speaker B',6,[40])])
    assert r=={'samples':[10,20,25,7,0,0,40],
              'timeline':[{'label':'speaker A','start_sample':0,'end_sample':3},
                          {'label':'door','start_sample':2,'end_sample':4},
                          {'label':'speaker B','start_sample':6,'end_sample':7}],
              'overload_indices':[],'sample_count':7,'story_quality_validated':False}


def test_overload_exact_pcm_boundaries_and_max_shape():
    r=solve([('a',0,[32767,-32768]),('b',0,[1,-1])])
    assert r['samples']==[32768,-32769] and r['overload_indices']==[0,1]
    assert solve([('x'*80,16383,[0])])['sample_count']==16384
    assert solve([('x',0,[0]*4096)]*32)['sample_count']==4096

@pytest.mark.parametrize('args,error,message',[
 ((None,),TypeError,'cues must be a list or tuple'),
 (([],),ValueError,'cue count must be between 1 and 32'),
 (([None]*33,),ValueError,'cue count must be between 1 and 32'),
 (([None],),ValueError,'cues must contain label offset and samples'),
 (([('x',True,[0])],),ValueError,'offsets must be nonbool integers zero through 16383'),
 (([('x',-1,[0])],),ValueError,'offsets must be nonbool integers zero through 16383'),
 (([('x',16384,[0])],),ValueError,'offsets must be nonbool integers zero through 16383'),
 (([('x',0,[])],),ValueError,'cue samples must have between 1 and 4096 entries'),
 (([('x',0,[None]*4097)],),ValueError,'cue samples must have between 1 and 4096 entries'),
 (([('x',16383,[None,None])],),ValueError,'drama timeline must not exceed 16384 samples'),
 (([(True,0,[0])],),TypeError,'cue labels must be strings'),
 (([('',0,[0])],),ValueError,'cue label length must be between 1 and 80'),
 (([('x'*81,0,[0])],),ValueError,'cue label length must be between 1 and 80'),
 (([(' ',0,[0])],),ValueError,'cue labels must not be blank'),
 (([('x',0,[True])],),ValueError,'samples must be nonbool signed 16-bit integers'),
 (([('x',0,[32768])],),ValueError,'samples must be nonbool signed 16-bit integers'),
 (([('x',0,[-32769])],),ValueError,'samples must be nonbool signed 16-bit integers'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message


def test_exact_pcm_endpoint_outputs_not_overloads():
    r=solve([('x',0,[32767,-32768,-1])])
    assert r['samples']==[32767,-32768,-1] and r['overload_indices']==[]

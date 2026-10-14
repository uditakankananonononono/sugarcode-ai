import pytest
from sugarcode.extra_doc.audiobook_narration import assemble_narration as solve


def test_explicit_audio_splice_and_half_open_cue_oracle():
    texts=['First sentence.','Second sentence.'];segments=[[1,-2,3],[4,-5]]
    r=solve(texts,segments,2)
    assert r=={'samples':[1,-2,3,0,0,4,-5],
              'cues':[{'text':texts[0],'start_sample':0,'end_sample':3},
                      {'text':texts[1],'start_sample':5,'end_sample':7}],
              'sample_count':7,'performance_validated':False}
    assert [r['samples'][c['start_sample']:c['end_sample']] for c in r['cues']]==segments
    r['samples'][0]=20;assert segments[0][0]==1


def test_caps_exact_admission_no_trailing_pause_and_pcm_edges():
    assert solve(['x'*256],[[32767,-32768]],1024)['samples']==[32767,-32768]
    assert solve(['x']*32,[[0]]*32)['sample_count']==32
    assert solve(['x']*4,[[0]*4096]*4)['sample_count']==16384
    with pytest.raises(ValueError,match='^narration must not exceed 16384 samples$'):
        solve(['x']*4,[[0]*4096]*4,1)

@pytest.mark.parametrize('args,error,message',[
 ((None,[]),TypeError,'texts and segments must be lists or tuples'),
 (([],[]),ValueError,'segment count must be between 1 and 32'),
 (([None]*33,[]),ValueError,'segment count must be between 1 and 32'),
 ((['x'],[]),ValueError,'text and audio segment counts must match'),
 ((['x'],[[0]],True),ValueError,'pause_samples must be a nonbool integer between zero and 1024'),
 ((['x'],[[0]],-1),ValueError,'pause_samples must be a nonbool integer between zero and 1024'),
 ((['x'],[[0]],1025),ValueError,'pause_samples must be a nonbool integer between zero and 1024'),
 (([True],[[0]]),TypeError,'text cues must be strings'),
 (([''],[[0]]),ValueError,'text cue length must be between 1 and 256'),
 ((['x'*257],[[0]]),ValueError,'text cue length must be between 1 and 256'),
 (([' '],[[0]]),ValueError,'text cues must not be blank'),
 ((['x'],[[]]),ValueError,'audio segments must have between 1 and 4096 samples'),
 ((['x'],[[None]*4097]),ValueError,'audio segments must have between 1 and 4096 samples'),
 ((['x'],[[True]]),ValueError,'samples must be nonbool signed 16-bit integers'),
 ((['x'],[[32768]]),ValueError,'samples must be nonbool signed 16-bit integers'),
 ((['x'],[[-32769]]),ValueError,'samples must be nonbool signed 16-bit integers'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message


def test_exact_next_total_sample_refusal_before_content_scan():
    with pytest.raises(ValueError) as exc:solve(['x']*5,[[None]*4096]*4+[[None]])
    assert str(exc.value)=='narration must not exceed 16384 samples'

@pytest.mark.parametrize('args',[('a',[[1]]),(['a'],{0:[1]}),(['a'],'x')])
def test_outer_container_declared_type_error(args):
    with pytest.raises(TypeError) as exc:solve(*args)
    assert str(exc.value)=='texts and segments must be lists or tuples'

@pytest.mark.parametrize('segment',[{1,2},'ab'])
def test_segment_container_declared_value_error(segment):
    with pytest.raises(ValueError) as exc:solve(['a'],[segment])
    assert str(exc.value)=='audio segments must have between 1 and 4096 samples'

import pytest
from sugarcode.extra_doc.music_composition import compose_melody as solve


def test_small_complete_path_oracle_and_pitch_tie():
    # Four paths to64:60/62/64motion4;60/65/64motion6;
    # 67/62/64motion7;67/65/64motion3.
    r=solve([[60,67],[62,65],[64]],64,7)
    assert r=={'pitches':[67,65,64],'quarter_note_durations':[1,1,1],
              'total_semitone_motion':3,'originality_validated':False}
    assert solve([[62,60],[61]],61)['pitches']==[60,61]
    assert solve([[60,67],[62,65],[64]],64,2)['pitches']==[67,65,64]


def test_boundary_shapes_defaults_single_note_and_infeasible():
    import inspect
    assert inspect.signature(solve).parameters['max_leap'].default==7
    assert solve([[0]],0,0)['pitches']==[0]
    assert solve([[0],[127]],127,127)['total_semitone_motion']==127
    r=solve([list(range(8))]*32,0,0)
    assert r['pitches']==[0]*32 and r['total_semitone_motion']==0
    with pytest.raises(ValueError,match='^no melody satisfies final pitch and leap cap$'):
        solve([[0],[127]],127,126)
    with pytest.raises(ValueError,match='^no melody satisfies final pitch and leap cap$'):
        solve([[60]],61)

@pytest.mark.parametrize('args,error,message',[
 ((None,0),TypeError,'pitch options must be a list or tuple'),
 (([],0),ValueError,'beat count must be between 1 and 32'),
 (([None]*33,0),ValueError,'beat count must be between 1 and 32'),
 (([[]],0),ValueError,'each beat must have between 1 and 8 pitches'),
 (([[None]*9],0),ValueError,'each beat must have between 1 and 8 pitches'),
 (([[0]],True),ValueError,'final_pitch must be a nonbool MIDI integer between zero and 127'),
 (([[0]],128),ValueError,'final_pitch must be a nonbool MIDI integer between zero and 127'),
 (([[0]],0,True),ValueError,'max_leap must be a nonbool integer between zero and 127'),
 (([[0]],0,-1),ValueError,'max_leap must be a nonbool integer between zero and 127'),
 (([[0]],0,128),ValueError,'max_leap must be a nonbool integer between zero and 127'),
 (([[True]],0),ValueError,'pitches must be nonbool MIDI integers between zero and 127'),
 (([[-1]],0),ValueError,'pitches must be nonbool MIDI integers between zero and 127'),
 (([[128]],0),ValueError,'pitches must be nonbool MIDI integers between zero and 127'),
 (([[0,0]],0),ValueError,'pitch options must be unique'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message


def test_negative_final_pitch_declared_refusal():
    with pytest.raises(ValueError) as exc:solve([[0]],-1)
    assert str(exc.value)=='final_pitch must be a nonbool MIDI integer between zero and 127'

import pytest
from sugarcode.extra_doc.harmony_arrangement import arrange_harmony as solve


def test_explicit_pair_interval_oracle_and_lex_ties():
    costs=list(range(12))
    #60/64/67:4+7+3=14;60/65/67:5+7+2=14;62/64/67:2+5+3=10;62/65/67:3+5+2=10.
    r=solve([[62,60],[65,64],[67]],costs)
    assert r=={'pitches':[62,64,67],'dissonance_cost':10,'candidate_count':4,
              'feasible_count':4,'pleasingness_validated':False}
    assert solve([[67,60],[64,72]],[0]*12)['pitches']==[60,64]
    assert solve([[0],[127]],costs)['dissonance_cost']==7


def test_single_voice_shape_and_cost_boundaries():
    assert solve([[127,0]],[1000000]*12)['pitches']==[0]
    r=solve([[4*i+j for j in range(4)] for i in range(6)],[0]*12)
    assert r['candidate_count']==4096 and r['feasible_count']==4096
    with pytest.raises(ValueError,match='^no strictly ascending voicing exists$'):solve([[64],[60]],[0]*12)

@pytest.mark.parametrize('args,error,message',[
 ((None,[0]*12),TypeError,'inputs must be lists or tuples'),
 (([],[0]*12),ValueError,'voice count must be between 1 and 6'),
 (([None]*7,[]),ValueError,'voice count must be between 1 and 6'),
 (([[]],[0]*12),ValueError,'each voice must have between 1 and 4 pitches'),
 (([[None]*5],[0]*12),ValueError,'each voice must have between 1 and 4 pitches'),
 (([[0]],[0]*11),ValueError,'interval costs must have twelve entries'),
 (([[0]],[True]*12),ValueError,'interval costs must be nonbool integers between zero and 1000000'),
 (([[0]],[-1]*12),ValueError,'interval costs must be nonbool integers between zero and 1000000'),
 (([[0]],[1000001]*12),ValueError,'interval costs must be nonbool integers between zero and 1000000'),
 (([[True]],[0]*12),ValueError,'pitches must be nonbool MIDI integers between zero and 127'),
 (([[-1]],[0]*12),ValueError,'pitches must be nonbool MIDI integers between zero and 127'),
 (([[128]],[0]*12),ValueError,'pitches must be nonbool MIDI integers between zero and 127'),
 (([[0,0]],[0]*12),ValueError,'pitch options must be unique'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message


def test_equal_voice_pitch_refused_and_unison_cost_not_added_to_self():
    with pytest.raises(ValueError,match='^no strictly ascending voicing exists$'):solve([[60],[60]],[0]*12)
    assert solve([[60],[64]],[9]+[0]*11)['dissonance_cost']==0

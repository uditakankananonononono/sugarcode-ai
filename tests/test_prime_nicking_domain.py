import pytest
from sugarcode.modules.prime_design import nicking_strategy

@pytest.mark.parametrize('candidate',[{'position':70.9,'strand':'-'},{'position':True,'strand':'-'},{'position':'70','strand':'-'},{'position':-1,'strand':'-'},{'position':70},{'position':70,'strand':'x'},{'position':70,'strand':'-','requires_edit_match':'no'},{}])
def test_bad_candidate_rejected(candidate):
    with pytest.raises(ValueError):nicking_strategy(0,[candidate])

@pytest.mark.parametrize('primary,strand',[(True,'+'),(1.5,'+'),(-1,'+'),(0,'x')])
def test_bad_primary_rejected(primary,strand):
    with pytest.raises(ValueError):nicking_strategy(primary,[],strand)

def test_coordinate_translation_invariant_and_input_unchanged():
    c=[{'position':70,'strand':'-','requires_edit_match':True}]
    a=nicking_strategy(0,c)[0];b=nicking_strategy(100,[dict(c[0],position=170)])[0]
    assert a['score']==b['score'] and a['distance']==70
    assert a['strategy']=='PE3b' and 'score' not in c[0]

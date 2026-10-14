from sugarcode.extra_doc.abstract_observer_predictions2022 import audit

NC = ('reflexivity','observer_theory','epistemic_validity')

def test_audpin_mixed_2022():
    assert audit((1,0,1),((1,1,1),(0,0,0),(1,0,1))) == {
        'abstract_observer_predictions_validated': False, 'not_claimed': NC,
        'error_positions': ((1,),(0,2),()), 'correct_counts': (2,1,3),
        'perfect_observers': (2,)}

def test_audpin_single_2022():
    assert audit((0,),((0,),(1,))) == {
        'abstract_observer_predictions_validated': False, 'not_claimed': NC,
        'error_positions': ((),(0,)), 'correct_counts': (1,0),
        'perfect_observers': (0,)}

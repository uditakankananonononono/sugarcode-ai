from sugarcode.extra_doc.abstract_feedback2021 import feedback

NC = ('physical_control','stability','convergence','safety')

def test_audpin_converge_2021():
    assert feedback(3,10,1,2) == {
        'abstract_feedback_validated': False, 'not_claimed': NC,
        'states': (3,10,10), 'pre_update_errors': (7,0),
        'final_error': 0, 'final_exact': True}

def test_audpin_overshoot_oscillation_2021():
    assert feedback(-5,5,2,3) == {
        'abstract_feedback_validated': False, 'not_claimed': NC,
        'states': (-5,15,-5,15), 'pre_update_errors': (10,-10,10),
        'final_error': -10, 'final_exact': False}

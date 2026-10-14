from sugarcode.extra_doc.abstract_calibration2023 import calibration

NC = ('metacognitive_validity','confidence_truth','learning_benefit')

def test_audpin_mixed_bins_2023():
    assert calibration(((5,1),(5,0),(0,1),(10,1))) == {
        'abstract_calibration_validated': False, 'not_claimed': NC,
        'bin_counts': (1,0,0,0,0,2,0,0,0,0,1),
        'bin_successes': (1,0,0,0,0,1,0,0,0,0,1),
        'signed_calibration_units': (10,0,0,0,0,0,0,0,0,0,0)}

def test_audpin_negative_gap_2023():
    assert calibration(((3,1),(3,1),(3,0),(7,0))) == {
        'abstract_calibration_validated': False, 'not_claimed': NC,
        'bin_counts': (0,0,0,3,0,0,0,1,0,0,0),
        'bin_successes': (0,0,0,2,0,0,0,0,0,0,0),
        'signed_calibration_units': (0,0,0,11,0,0,0,-7,0,0,0)}

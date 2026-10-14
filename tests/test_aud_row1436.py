from sugarcode.extra_doc.support_plan1436 import plan

def test_audpin_mixed_1436():
    assert plan(2,[0,3,5,2]) == {'support': [0,1,3,0], 'total': 4, 'peak': 3,
                                 'peak_step': 3, 'independent': False}

def test_audpin_all_met_1436():
    assert plan(5,[0,1,2]) == {'support': [0,0,0], 'total': 0, 'peak': 0,
                               'peak_step': None, 'independent': True}

def test_audpin_zero_learner_1436():
    assert plan(0,[1,1,1]) == {'support': [1,1,1], 'total': 3, 'peak': 1,
                               'peak_step': 1, 'independent': False}

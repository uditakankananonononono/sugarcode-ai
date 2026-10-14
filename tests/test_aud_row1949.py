from sugarcode.extra_doc.explainable_ai import track_tops

def test_audpin_tie_holds_first_1949():
    assert track_tops([('a','m',5),('b','m',3),('b','m',2)]) == {
        'total': 3, 'displacements': {}, 'tops': {'m':'a'}, 'leader': None}

def test_audpin_immediate_tie_1949():
    assert track_tops([('a','m',5),('b','m',5)]) == {
        'total': 2, 'displacements': {}, 'tops': {'m':'a'}, 'leader': None}

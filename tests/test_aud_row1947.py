from sugarcode.extra_doc.ai_safety import count_inversions

def test_audpin_two_inversions_1947():
    assert count_inversions([('h','g',9),('h','g',1),('h','g',5)]) == {
        'total': 3, 'inversions': {'g':2}, 'pairs': 2, 'leader': 'g'}

def test_audpin_cross_guard_1947():
    assert count_inversions([('h','a',3),('h','b',2),('h','a',2)]) == {
        'total': 3, 'inversions': {'a':1}, 'pairs': 1, 'leader': 'a'}

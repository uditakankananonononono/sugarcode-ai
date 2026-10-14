from sugarcode.extra_doc.ai_alignment import count_corrections

def test_audpin_single_correction_1946():
    assert count_corrections([('g','a',2),('g','a',1),('g','a',1)]) == {
        'total': 3, 'corrections': {'a':1}, 'pending': [], 'leader': 'a'}

def test_audpin_pending_sorted_1946():
    assert count_corrections([('g','a',2),('g','b',3),('g','a',1)]) == {
        'total': 3, 'corrections': {'a':1}, 'pending': ['b'], 'leader': 'a'}

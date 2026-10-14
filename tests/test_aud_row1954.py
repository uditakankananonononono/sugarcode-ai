from sugarcode.extra_doc.ai_governance import count_covers

def test_audpin_strict_cover_1954():
    assert count_covers([('a','r1',1),('a','r2',1),('b','r1',1)]) == {
        'total': 3, 'covers': {'a':1}, 'count': 1, 'independent': [], 'leader': 'a'}

def test_audpin_independent_1954():
    assert count_covers([('a','r1',1),('a','r2',1),('b','r2',1),('b','r3',1),('c','r1',1)]) == {
        'total': 5, 'covers': {'a':1}, 'count': 1, 'independent': ['b'], 'leader': 'a'}

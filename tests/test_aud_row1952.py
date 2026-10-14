from sugarcode.extra_doc.responsible_ai import track_debuts

def test_audpin_debuts_solo_1952():
    assert track_debuts([('a','x',1),('b','y',1),('a','z',1)]) == {
        'total': 3, 'debuts': {'a':2,'b':1}, 'favorite': 'a', 'solo': ['y']}

def test_audpin_favorite_tie_first_policy_1952():
    assert track_debuts([('b','x',1),('a','y',1),('b','z',1),('a','w',1)]) == {
        'total': 4, 'debuts': {'b':2,'a':2}, 'favorite': 'b', 'solo': []}

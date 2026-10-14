from sugarcode.extra_doc.agent_learning import catch_frontier

def test_audpin_tie_first_supplied_1943():
    assert catch_frontier([('e','a',5),('e','b',9),('e','a',9),('e','c',9)]) == {
        'total': 4, 'catches': {'a':1,'c':1}, 'frontier': 9, 'leader': 'a'}

def test_audpin_own_at_frontier_no_catch_1943():
    assert catch_frontier([('e','a',9),('e','a',9)]) == {
        'total': 2, 'catches': {}, 'frontier': 9, 'leader': None}

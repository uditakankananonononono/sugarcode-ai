from sugarcode.extra_doc.agent_negotiation import count_counters

def test_audpin_no_strict_between_1942():
    assert count_counters([('o','p',1),('o','p',9),('o','p',5)]) == {
        'total': 3, 'counters': {}, 'turns': 0, 'leader': None}

def test_audpin_one_counter_1942():
    assert count_counters([('o','x',5),('o','y',3),('o','x',4),('o','y',6),('o','x',2)]) == {
        'total': 5, 'counters': {'x':1}, 'turns': 1, 'leader': 'x'}

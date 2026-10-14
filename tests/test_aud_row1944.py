from sugarcode.extra_doc.reinforcement_learning_from_human_feedback import weight_feedback

def test_audpin_positions_1944():
    assert weight_feedback([('p','a',1),('p','a',2),('p','b',9)]) == {
        'total': 3, 'weighted': {'a':5,'b':9}, 'weight': 14, 'leader': 'b'}

def test_audpin_position_two_wins_1944():
    assert weight_feedback([('p','x',3),('p','y',9),('p','x',9)]) == {
        'total': 3, 'weighted': {'x':21,'y':9}, 'weight': 30, 'leader': 'x'}

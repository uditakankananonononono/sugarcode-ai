from sugarcode.extra_doc.race_relations1777 import count_contacts

def test_audpin_aggregate_order_1777():
    assert count_contacts(['a','b'],[('a','b',5),('b','a',5),('a','a',1),('b','b',2),('a','b',3)]) == {
        'pairs': [('a','a',1),('a','b',8),('b','a',5),('b','b',2)],
        'same': 3, 'different': 13, 'claim': 'PARTIAL', 'race_inferred': False}

def test_audpin_self_only_1777():
    assert count_contacts(['x','y'],[('x','x',7)]) == {
        'pairs': [('x','x',7)], 'same': 7, 'different': 0,
        'claim': 'PARTIAL', 'race_inferred': False}

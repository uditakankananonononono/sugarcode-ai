from sugarcode.extra_doc.interpretable_ai import count_slips

def test_audpin_plateau_then_drop_1950():
    assert count_slips([('r','m',5),('r','m',4),('r','m',4),('r','m',1)]) == {
        'total': 4, 'slips': {'r':2}, 'count': 2, 'leader': 'r'}

def test_audpin_two_rules_tie_1950():
    assert count_slips([('r','m',9),('s','m',8),('r','m',1),('s','m',1)]) == {
        'total': 4, 'slips': {'r':1,'s':1}, 'count': 2, 'leader': 'r'}

from sugarcode.extra_doc.abstract_stock_cycle2020 import cycle

NC = ('living_system','self_production','organizational_closure','sustainability')

def test_audpin_deficit_recovery_2020():
    assert cycle(10,((5,20),(30,5),(0,0))) == {
        'abstract_stock_cycle_validated': False, 'not_claimed': NC,
        'stocks': (10,-5,20,20), 'deficit_steps': (1,), 'net_change': 10}

def test_audpin_deep_deficit_2020():
    assert cycle(0,((0,100),(100,0))) == {
        'abstract_stock_cycle_validated': False, 'not_claimed': NC,
        'stocks': (0,-100,0), 'deficit_steps': (1,), 'net_change': 0}

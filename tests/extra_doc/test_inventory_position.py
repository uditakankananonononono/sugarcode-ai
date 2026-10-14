import itertools
import re
import pytest
from sugarcode.extra_doc.inventory_position import position
class Number(int): pass
NAMES = ('on_hand','incoming','reserved','reorder_point','target')

def oracle(hand, incoming, reserved, point, target):
    net = sum((hand,incoming,-reserved))
    if net >= point: reorder = False; top = 0
    else: reorder = True; top = target-net
    debt = abs(net) if net < 0 else 0
    return {'inventory_position_validated': False,
            'not_claimed': ('optimal_policy','lead_times','demand_model'),
            'position': net, 'reorder': reorder, 'top_up':top,'backlog':debt}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: position(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for args in itertools.product((0,1,2,10000),repeat=5):
        if args[4]>=args[3]: assert position(*args)==oracle(*args)

def test_bounds_and_types():
    for i,name in enumerate(NAMES):
        for bad in (-1,10001,False,True,Number(1),1.0,None,'é','ａ','Ж'):
            args = [1]*5; args[i] = bad
            refuse(args,f'{name}: whole number 0 to 10000 required')

def test_target_relation():
    for point in (1,2,10000):
        refuse((0,0,0,point,point-1),'target must be at least reorder_point')

def test_check_order():
    for i,name in enumerate(NAMES):
        args = [1]*5
        for j in range(i,5): args[j] = None
        refuse(args,f'{name}: whole number 0 to 10000 required')
    refuse((None,0,0,2,1),'on_hand: whole number 0 to 10000 required')

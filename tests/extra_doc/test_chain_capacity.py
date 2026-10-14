import itertools
import re
import pytest
from sugarcode.extra_doc.chain_capacity import capacity
class Number(int): pass
class Items(tuple): pass

def oracle(stages, required):
    lowest = stages[0]
    for value in stages:
        if value < lowest: lowest = value
    limiting = []; short = []
    for i,value in enumerate(stages):
        if value == lowest: limiting.append(i)
        if value < required: short.append(i)
    return {'chain_capacity_validated': False,
            'not_claimed': ('network_design','transport_plan','real_throughput'),
            'bottleneck':lowest, 'limiting_positions':tuple(limiting),
            'shortfall_positions':tuple(short), 'all_sufficient':len(short)==0,
            'margin':lowest-required}

def refuse(stages,required,message):
    with pytest.raises(ValueError) as exc: capacity(stages,required)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in (2,3,4):
        for stages in itertools.product((1,2,9,10000),repeat=n):
            for required in (1,2,3,9,10000):
                assert capacity(stages,required) == oracle(stages,required)

def test_caps_positions():
    for stages in ((1,)*12,(10000,)*12,(1,10000),(10000,1),tuple(range(1,13)),tuple(range(12,0,-1))):
        for required in (1,2,12,10000):
            assert capacity(stages,required) == oracle(stages,required)

def test_shape():
    for value in ((),(1,), (1,)*13, [1,2],Items((1,2)),None,'éЖ'):
        refuse(value,1,'stages: tuple of 2 to 12 capacities required')

def test_values():
    for pos in (0,1,11):
        for bad in (0,-1,10001,False,True,Number(1),1.0,None,'é','ａ','Ж'):
            values = [1]*12; values[pos] = bad
            refuse(tuple(values),1,f'stages[{pos}]: whole number 1 to 10000 required')

def test_required():
    for bad in (0,-1,10001,False,True,Number(1),1.0,None,'é','ａ','Ж'):
        refuse((1,10000),bad,'required: whole number 1 to 10000 required')

def test_order():
    refuse((None,)*13,None,'stages: tuple of 2 to 12 capacities required')
    refuse((None,0),None,'stages[0]: whole number 1 to 10000 required')
    refuse((1,0),None,'stages[1]: whole number 1 to 10000 required')

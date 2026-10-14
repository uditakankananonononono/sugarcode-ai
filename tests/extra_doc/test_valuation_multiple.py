import itertools
import re
import pytest
from sugarcode.extra_doc.valuation_multiple import values
class Number(int): pass
class Items(tuple): pass

def oracle(metric,multiples):
    scenarios=[]
    for multiple in multiples: scenarios.append(metric*multiple)
    low=high=scenarios[0]
    for scenario in scenarios:
        if scenario<low: low=scenario
        if scenario>high: high=scenario
    return {'valuation_multiple_validated':False,
            'not_claimed':('fair_value','market_evidence','investment_advice'),
            'scenarios':tuple(scenarios),'low':low,'high':high,'spread':high-low}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: values(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in (1,2,3,4):
        for multiples in itertools.product((1,2,100),repeat=n):
            for metric in (0,1,1000000): assert values(metric,multiples)==oracle(metric,multiples)

def test_caps_positions():
    for multiples in ((1,)*12,(100,)*12,(100,)+(1,)*11,(1,)*11+(100,)):
        for metric in (0,1,1000000): assert values(metric,multiples)==oracle(metric,multiples)

def test_shape_and_metric_order():
    for bad in ((),(None,)*13,[1],Items((1,)),None,'é'):
        refuse((None,bad),'multiples: tuple of 1 to 12 entries required')
    for bad in (-1,1000001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse((bad,(None,)),'metric: whole number 0 to 1000000 required')

def test_multiple_types_bounds():
    for pos in (0,1,11):
        for bad in (0,-1,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            multiples=[1]*12;multiples[pos]=bad
            refuse((0,tuple(multiples)),f'multiples[{pos}]: whole number 1 to 100 required')

import itertools
import re
from fractions import Fraction
import pytest
from sugarcode.extra_doc.flow_waste import waste
class Number(int): pass
class Items(tuple): pass

def oracle(stages,limit):
    work=0;wait=0;positions=[]
    for i,(a,b) in enumerate(stages):
        work+=a;wait+=b
        if b: positions.append(i)
    share=Fraction(wait,work+wait)*100
    return {'flow_waste_validated':False,
            'not_claimed':('waste_elimination','production_model','lean_advice'),
            'work_total':work,'wait_total':wait,'elapsed_total':work+wait,
            'wait_pct':int(share),'within_limit':share<=limit,
            'waiting_positions':tuple(positions)}

def refuse(stages,limit,message):
    with pytest.raises(ValueError) as exc: waste(stages,limit)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_fraction_oracle():
    choices=((1,0),(1,1),(2,1),(1,2),(3,0))
    for n in (1,2,3):
        for stages in itertools.product(choices,repeat=n):
            for limit in (0,1,33,34,50,66,67,99,100):
                assert waste(stages,limit)==oracle(stages,limit)

def test_caps_and_first_last():
    for stages in (((1000,1000),)*20,((1,0),)*20,((1,1),)+( (1,0),)*19,((1,0),)*19+((1,1),)):
        for limit in (0,1,50,100): assert waste(stages,limit)==oracle(stages,limit)

def test_container():
    for bad in ((),(None,)*21,[(1,0)],Items(((1,0),)),None,'é'):
        refuse(bad,None,'stages: tuple of 1 to 20 pairs required')

def test_nested_shapes_types_and_bounds():
    for pos in (0,1,19):
        for bad in (None,(),(1,), (1,0,1),[1,0],Items((1,0)),'Ж'):
            rows=[(1,0)]*20; rows[pos]=bad
            refuse(tuple(rows),None,f'stages[{pos}]: pair (work, wait) required')
        for bad in (0,-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            rows=[(1,0)]*20;rows[pos]=(bad,None)
            refuse(tuple(rows),None,f'stages[{pos}].work: whole number 1 to 1000 required')
        for bad in (-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            rows=[(1,0)]*20;rows[pos]=(1,bad)
            refuse(tuple(rows),None,f'stages[{pos}].wait: whole number 0 to 1000 required')

def test_limit():
    for bad in (-1,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((1,0),),bad,'wait_limit: whole number 0 to 100 required')

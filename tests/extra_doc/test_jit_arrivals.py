import itertools
import re
import pytest
from sugarcode.extra_doc.jit_arrivals import arrivals
class Number(int): pass
class Items(tuple): pass

def oracle(rows):
    early=[];late=[];on_time=0;storage=0;delay=0
    for i,(arrival,consumption) in enumerate(rows):
        diff=arrival-consumption
        if diff<0: early.append(i);storage+=abs(diff)
        elif diff>0: late.append(i);delay+=diff
        else: on_time+=1
    return {'jit_arrivals_validated':False,
            'not_claimed':('inventory_optimization','real_schedule','delivery_reliability'),
            'early_positions':tuple(early),'late_positions':tuple(late),
            'on_time_count':on_time,'storage_slots':storage,'delay_slots':delay}

def refuse(rows,message):
    with pytest.raises(ValueError) as exc: arrivals(rows)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    pairs=tuple(itertools.product((0,1,1000),repeat=2))
    for n in (1,2,3):
        for rows in itertools.product(pairs,repeat=n): assert arrivals(rows)==oracle(rows)

def test_caps():
    for rows in (((0,1000),)*20,((1000,0),)*20,((1000,1000),)*20,((0,1),)+((0,0),)*18+((1,0),)):
        assert arrivals(rows)==oracle(rows)

def test_outer():
    for bad in ((),(None,)*21,[(0,0)],Items(((0,0),)),None,'é'):
        refuse(bad,'rows: tuple of 1 to 20 pairs required')

def test_nested_shapes_and_values():
    for pos in (0,1,19):
        for bad in (None,(),(0,), (0,0,0),[0,0],Items((0,0)),'Ж'):
            rows=[(0,0)]*20;rows[pos]=bad
            refuse(tuple(rows),f'rows[{pos}]: pair (arrival, consumption) required')
        for j,name in enumerate(('arrival','consumption')):
            for bad in (-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                row=[0,0];row[j]=bad
                rows=[(0,0)]*20;rows[pos]=tuple(row)
                refuse(tuple(rows),f'rows[{pos}].{name}: whole number 0 to 1000 required')

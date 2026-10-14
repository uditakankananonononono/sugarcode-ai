import itertools,re,pytest
from sugarcode.extra_doc.abstract_bend_deltas import bends
class Number(int):pass
class Items(tuple):pass

def oracle(values):
    deltas=[];rev=[];variation=0
    for a,b in zip(values,values[1:]):
        delta=b-a;deltas.append(delta)
        variation+=(b-a) if b>=a else (a-b)
    for i in range(1,len(deltas)):
        if (deltas[i]<0<deltas[i-1]) or (deltas[i-1]<0<deltas[i]):rev.append(i)
    return {'abstract_bend_deltas_validated':False,'not_claimed':('robot_control','material_behavior','physical_safety'),'deltas':tuple(deltas),'reversal_positions':tuple(rev),'variation':variation}

def refuse(values,message):
    with pytest.raises(ValueError) as e:bends(values)
    assert re.fullmatch(re.escape(message),str(e.value))

def test_oracle():
    for n in (2,3,4):
        for values in itertools.product((-2,-1,0,1,2),repeat=n):assert bends(values)==oracle(values)

def test_caps():
    for values in ((-100,)*30,(100,)*30,(-100,100)*15,(0,)*29+(100,)):
        assert bends(values)==oracle(values)

def test_bad():
    for bad in ((),(0,),(None,)*31,[],Items((0,1)),None,'é'):
        refuse(bad,'values: tuple of 2 to 30 integers required')
    for pos in (0,1,29):
        for bad in (-101,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            values=[0]*30;values[pos]=bad
            refuse(tuple(values),f'values[{pos}]: whole number -100 to 100 required')

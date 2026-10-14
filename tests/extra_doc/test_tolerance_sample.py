import itertools
import re
import pytest
from sugarcode.extra_doc.tolerance_sample import inspect
class Number(int): pass
class Items(tuple): pass

def oracle(values,lower,upper):
    low=[]; high=[]; accepted=0
    for i,v in enumerate(values):
        if v < lower: low.append(i)
        elif v > upper: high.append(i)
        else: accepted+=1
    return {'tolerance_sample_validated':False,
            'not_claimed':('certification','sampling_assurance','calibration'),
            'below_positions':tuple(low),'above_positions':tuple(high),
            'accepted_count':accepted,'all_in_bounds':not low and not high}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: inspect(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in (1,2,3):
        for values in itertools.product((-1000,-1,0,1,1000),repeat=n):
            for low,high in itertools.product((-1000,-1,0,1,1000),repeat=2):
                if low<=high: assert inspect(values,low,high)==oracle(values,low,high)

def test_caps():
    for values in ((0,)*30,(-1000,)*30,(1000,)*30,(-1000,)+(0,)*28+(1000,)):
        for lo,hi in ((-1000,1000),(0,0),(-1,1)):
            assert inspect(values,lo,hi)==oracle(values,lo,hi)

def test_container():
    for bad in ((),(None,)*31,[1],Items((1,)),None,'é'):
        refuse((bad,None,None),'values: tuple of 1 to 30 measurements required')

def test_values():
    for pos in (0,1,29):
        for bad in (-1001,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            values=[0]*30;values[pos]=bad
            refuse((tuple(values),None,None),f'values[{pos}]: whole number -1000 to 1000 required')

def test_bounds():
    for pos,name in ((1,'lower'),(2,'upper')):
        for bad in (-1001,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            args=[(0,),0,0]; args[pos]=bad
            refuse(args,f'{name}: whole number -1000 to 1000 required')
    refuse(((0,),1,0),'lower must not exceed upper')
    refuse(((0,),None,None),'lower: whole number -1000 to 1000 required')

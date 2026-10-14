import itertools
import re
import pytest
from sugarcode.extra_doc.adoption_checkpoints import checkpoints
class Number(int): pass
class Items(tuple): pass

def oracle(adopters,population,target):
    first=None;previous=adopters[0];gains=[]
    for i,value in enumerate(adopters):
        if first is None and value>=target: first=i
        if i: gains.append(value-previous)
        previous=value
    remaining=target-adopters[-1]
    if remaining<0: remaining=0
    return {'adoption_checkpoints_validated':False,
            'not_claimed':('transition_management','adoption_prediction','readiness'),
            'first_reached':first,'gains':tuple(gains),'remaining':remaining,'reached':first is not None}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: checkpoints(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in (1,2,3,4):
        for seq in itertools.combinations_with_replacement((0,1,2,10000),n):
            for target in (0,1,2,3,9999,10000): assert checkpoints(seq,10000,target)==oracle(seq,10000,target)

def test_caps_first_last():
    for seq in ((0,)*20,(10000,)*20,tuple(range(20)),(0,)*19+(10000,)):
        for target in (0,1,19,10000): assert checkpoints(seq,10000,target)==oracle(seq,10000,target)
    assert checkpoints((0,1),1,1)==oracle((0,1),1,1)

def test_shape():
    for bad in ((),(None,)*21,[0],Items((0,)),None,'é'):
        refuse((bad,None,None),'adopters: tuple of 1 to 20 counts required')

def test_scalar_types_bounds_and_order():
    for bad in (0,-1,10001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((None,),bad,None),'population: whole number 1 to 10000 required')
    for bad in (-1,2,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((None,),1,bad),'target: whole number 0 to population required')

def test_adopter_bounds_types():
    for pos in (0,1,19):
        for bad in (-1,10001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            seq=[0]*20;seq[pos]=bad
            refuse((tuple(seq),10000,0),f'adopters[{pos}]: whole number 0 to population required')
    refuse(((0,2),1,0),'adopters[1]: whole number 0 to population required')

def test_decrease_and_validation_precedes_trend():
    for pos in (1,19):
        seq=[1]*20;seq[pos]=0
        refuse((tuple(seq),1,1),f'adopters[{pos}]: count must not decrease')
    refuse(((1,0,None),1,1),'adopters[2]: whole number 0 to population required')

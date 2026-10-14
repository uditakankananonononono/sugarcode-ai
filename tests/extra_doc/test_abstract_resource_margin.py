import itertools,re,pytest
from sugarcode.extra_doc.abstract_resource_margin import margins
class Number(int):pass
class Items(tuple):pass

def oracle(demands,stock):
    remaining=[];left=stock;short=[]
    for i,value in enumerate(demands):
        left-=value;remaining.append(left)
        if left<0:short.append(i)
    return {'abstract_resource_margin_validated':False,'not_claimed':('outbreak_planning','safety_assessment','medical_decisions'),'remaining':tuple(remaining),'shortfall_positions':tuple(short),'total_demand':stock-left}

def refuse(args,message):
    with pytest.raises(ValueError) as e:margins(*args)
    assert re.fullmatch(re.escape(message),str(e.value))

def test_oracle():
    for n in (1,2,3):
        for demands in itertools.product((0,1,2,1000),repeat=n):
            for stock in (0,1,2,1000,20000):assert margins(demands,stock)==oracle(demands,stock)

def test_caps():
    for demands in ((0,)*20,(1000,)*20,(1000,)+(0,)*18+(1,)):
        for stock in (0,1,19999,20000):assert margins(demands,stock)==oracle(demands,stock)

def test_bad():
    for bad in ((),(None,)*21,[0],Items((0,)),None,'é'):
        refuse((bad,None),'demands: tuple of 1 to 20 counts required')
    for pos in (0,1,19):
        for bad in (-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            values=[0]*20;values[pos]=bad
            refuse((tuple(values),None),f'demands[{pos}]: whole number 0 to 1000 required')
    for bad in (-1,20001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((0,),bad),'stock: whole number 0 to 20000 required')

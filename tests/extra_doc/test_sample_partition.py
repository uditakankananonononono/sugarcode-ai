import itertools,re,pytest
from sugarcode.extra_doc.sample_partition import split
class Number(int):pass
class Items(tuple):pass

def oracle(values,period):
    hold=set(range(0,len(values),period));hpos=[];tpos=[];hval=[];tval=[]
    for i,value in enumerate(values):
        if i in hold:hpos.append(i);hval.append(value)
        else:tpos.append(i);tval.append(value)
    return {'sample_partition_validated':False,
            'not_claimed':('honest_estimation','randomization','generalization'),
            'holdout_positions':tuple(hpos),'training_positions':tuple(tpos),
            'holdout_values':tuple(hval),'training_values':tuple(tval)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:split(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in (2,3,4,5):
        for values in itertools.product((-1000,0,1000),repeat=n):
            for period in (2,3,9,10):assert split(values,period)==oracle(values,period)

def test_caps():
    for values in (tuple(range(30)),(0,)*30,(1000,)+(0,)*29,(0,)*29+(-1000,)):
        for period in range(2,11):assert split(values,period)==oracle(values,period)

def test_types_bounds_order():
    for bad in ((),(0,),(None,)*31,[0,1],Items((0,1)),None,'é'):
        refuse((bad,None),'values: tuple of 2 to 30 entries required')
    for pos in (0,1,29):
        for bad in (-1001,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            values=[0]*30;values[pos]=bad
            refuse((tuple(values),None),f'values[{pos}]: whole number -1000 to 1000 required')
    for bad in (0,1,11,True,False,None,Number(2),2.0,'é','ａ','Ж'):
        refuse(((0,1),bad),'period: whole number 2 to 10 required')

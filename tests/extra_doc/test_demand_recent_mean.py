import itertools
import re
import pytest
from sugarcode.extra_doc.demand_recent_mean import recent_mean
class Number(int): pass
class Items(tuple): pass

def oracle(counts,window):
    total = 0
    for i in range(len(counts)-window,len(counts)): total+=counts[i]
    mean = total//window
    previous=None
    if window<=len(counts)//2:
        old=0
        for i in range(len(counts)-2*window,len(counts)-window): old+=counts[i]
        previous=old//window
    return {'demand_recent_mean_validated':False,
            'not_claimed':('predictive_accuracy','statistical_model','seasonality'),
            'mean':mean,'remainder':total-mean*window,'window_total':total,
            'previous_mean':previous,'change':mean-previous if previous is not None else None}

def refuse(counts,window,message):
    with pytest.raises(ValueError) as exc: recent_mean(counts,window)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in (2,3,4,5):
        for counts in itertools.product((0,1,3),repeat=n):
            for w in range(1,n+1): assert recent_mean(counts,w)==oracle(counts,w)

def test_caps():
    for counts in ((0,)*24,(10000,)*24,tuple(range(24)),tuple(range(23,-1,-1))):
        for w in range(1,25): assert recent_mean(counts,w)==oracle(counts,w)

def test_shape():
    for counts in ((),(0,),(None,)*25,[1,2],Items((1,2)),None,'éЖ'):
        refuse(counts,None,'counts: tuple of 2 to 24 observations required')

def test_values():
    for pos in (0,1,23):
        for bad in (-1,10001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            counts=[0]*24; counts[pos]=bad
            refuse(tuple(counts),None,f'counts[{pos}]: whole number 0 to 10000 required')

def test_window():
    for bad in (0,-1,3,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse((0,1),bad,'window: whole number 1 to observation count required')

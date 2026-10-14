import itertools,re,pytest
from sugarcode.extra_doc.abstract_interval_occupancy import occupancy
class Number(int):pass
class Items(tuple):pass

def oracle(intervals,point):
    active=[]
    for i,(start,end) in enumerate(intervals):
        if point in range(start,end+1):active.append(i)
    return {'abstract_interval_occupancy_validated':False,'not_claimed':('confinement_decisions','exposure_assessment','medical_advice'),'active_positions':tuple(active),'active_count':len(active),'unoccupied':len(active)==0}

def refuse(args,message):
    with pytest.raises(ValueError) as e:occupancy(*args)
    assert re.fullmatch(re.escape(message),str(e.value))

def test_oracle():
    choices=tuple(itertools.combinations_with_replacement((0,1,2,1000),2))
    for n in (0,1,2,3):
        for intervals in itertools.product(choices,repeat=n):
            for point in (0,1,2,3,999,1000):assert occupancy(intervals,point)==oracle(intervals,point)

def test_caps():
    for intervals in (((0,1000),)*20,((0,0),)*20,((1000,1000),)*20,((0,1),)*19+((2,1000),)):
        for point in (0,1,2,999,1000):assert occupancy(intervals,point)==oracle(intervals,point)

def test_bad():
    for bad in ((None,)*21,[],Items(()),None,'é'):
        refuse((bad,None),'intervals: tuple of 0 to 20 pairs required')
    for pos in (0,1,19):
        for bad in (None,(),(0,), (0,1,2),[0,1],Items((0,1)),'Ж'):
            rows=[(0,1)]*20;rows[pos]=bad
            refuse((tuple(rows),None),f'intervals[{pos}]: pair (start, end) required')
        for col in (0,1):
            for bad in (-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                rows=[(0,1)]*20;edge=[0,1];edge[col]=bad;rows[pos]=tuple(edge)
                refuse((tuple(rows),None),f'intervals[{pos}][{col}]: whole number 0 to 1000 required')
        rows=[(0,1)]*20;rows[pos]=(1,0)
        refuse((tuple(rows),None),f'intervals[{pos}]: start must not exceed end')
    for bad in (-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((),bad),'point: whole number 0 to 1000 required')

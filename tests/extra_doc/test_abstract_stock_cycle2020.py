import itertools,pytest
from sugarcode.extra_doc.abstract_stock_cycle2020 import cycle
class Number(int):pass
class Items(tuple):pass

def oracle(initial,rows):
    stocks=tuple(initial+sum(p for p,_ in rows[:i])-sum(l for _,l in rows[:i]) for i in range(len(rows)+1))
    return {'abstract_stock_cycle_validated':False,'not_claimed':('living_system','self_production','organizational_closure','sustainability'),'stocks':stocks,'deficit_steps':tuple(i for i,v in enumerate(stocks) if i and v<0),'net_change':sum(p for p,_ in rows)-sum(l for _,l in rows)}

@pytest.mark.parametrize('initial',[0,1,100])
@pytest.mark.parametrize('pair',[(0,0),(0,1),(1,0),(100,0),(0,100),(100,100)])
@pytest.mark.parametrize('count',[1,20])
def test_caps(initial,pair,count):
    rows=(pair,)*count;result=cycle(initial,rows)
    assert result==oracle(initial,rows)
    assert result['stocks'] is not rows

def test_oracle():
    for n in (1,2,3):
        for rows in itertools.product(((0,0),(0,1),(1,0),(100,100)),repeat=n):
            for initial in (0,1,100):assert cycle(initial,rows)==oracle(initial,rows)

def refuse(args,message):
    with pytest.raises(ValueError) as e:cycle(*args)
    assert str(e.value)==message

def test_refusals():
    for bad in (-1,101,True,False,Number(1),1.0,None,'é',{},[0]):refuse((bad,None),'initial: integer 0 to 100 required')
    for bad in ((),((0,0),)*21,[],[(0,0)]*21,{}, {'extra':0},Items(((0,0),)),None):refuse((0,bad),'rows: tuple of 1 to 20 production-loss pairs required')
    for i in (0,1,19):
        for bad in ((),(0,), (0,0,0),[0,0],{'production':0,'loss':0,'extra':0},Items((0,0)),None):
            rows=[(0,0)]*20;rows[i]=bad
            refuse((0,tuple(rows)),f'rows[{i}]: pair (production, loss) required')
        for j in (0,1):
            for bad in (-1,101,True,False,Number(1),1.0,None,'é','Ж','ａ'):
                rows=[(0,0)]*20;row=[0,0];row[j]=bad;rows[i]=tuple(row)
                refuse((0,tuple(rows)),f'rows[{i}][{j}]: integer 0 to 100 required')

def test_singleton():
    assert cycle(0,((0,1),))=={'abstract_stock_cycle_validated':False,'not_claimed':('living_system','self_production','organizational_closure','sustainability'),'stocks':(0,-1),'deficit_steps':(1,),'net_change':-1}

def test_fresh():
    r=cycle(0,((0,0),));r['stocks']=('caller',)
    assert cycle(0,((0,0),))==oracle(0,((0,0),))

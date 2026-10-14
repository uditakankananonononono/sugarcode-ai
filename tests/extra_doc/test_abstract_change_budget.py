import itertools,re,pytest
from sugarcode.extra_doc.abstract_change_budget import changes
class Number(int):pass
class Items(tuple):pass

def oracle(rows,budget):
    costs=[]
    for before,after in rows:
        low,high=(before,after) if before<=after else (after,before)
        costs.append(high-low)
    total=0
    for cost in costs:total+=cost
    return {'abstract_change_budget_validated':False,'not_claimed':('lifestyle_effectiveness','health_outcome_assessment','medical_advice'),'change_costs':tuple(costs),'total_cost':total,'within_budget':budget-total>=0,'remaining_budget':budget-total}

def refuse(args,message):
    with pytest.raises(ValueError) as e:changes(*args)
    assert re.fullmatch(re.escape(message),str(e.value))

def test_oracle():
    choices=tuple(itertools.product((0,1,1000),repeat=2))
    for n in (1,2,3):
        for rows in itertools.product(choices,repeat=n):
            for budget in (0,1,2,999,1000,20000):assert changes(rows,budget)==oracle(rows,budget)

def test_caps():
    for rows in (((0,1000),)*20,((1000,0),)*20,((0,0),)*20,((0,1),)*19+((1,0),)):
        for budget in (0,19,20,19999,20000):assert changes(rows,budget)==oracle(rows,budget)

def test_bad():
    for bad in ((),(None,)*21,[],Items(((0,1),)),None,'é'):
        refuse((bad,None),'rows: tuple of 1 to 20 value pairs required')
    for pos in (0,1,19):
        for bad in (None,(),(0,), (0,1,2),[0,1],Items((0,1)),'Ж'):
            rows=[(0,1)]*20;rows[pos]=bad
            refuse((tuple(rows),None),f'rows[{pos}]: pair (before, after) required')
        for col in (0,1):
            for bad in (-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                rows=[(0,1)]*20;edge=[0,1];edge[col]=bad;rows[pos]=tuple(edge)
                refuse((tuple(rows),None),f'rows[{pos}][{col}]: whole number 0 to 1000 required')
    for bad in (-1,20001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse((((0,1),),bad),'budget: whole number 0 to 20000 required')

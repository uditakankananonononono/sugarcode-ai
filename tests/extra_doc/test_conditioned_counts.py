import itertools,re,pytest
from sugarcode.extra_doc.conditioned_counts import condition
class Number(int):pass
class Items(tuple):pass

def oracle(rows,group):
    positions=[];total=0
    for i,(g,count) in enumerate(rows):
        if g==group:positions.append(i);total+=count
    return {'conditioned_counts_validated':False,
            'not_claimed':('conditional_inference','selection_adjustment','statistical_validity'),
            'positions':tuple(positions),'count_total':total,'selected_count':len(positions)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:condition(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    pairs=tuple(itertools.product((0,1,10),(0,1,1000)))
    for n in (1,2,3):
        for rows in itertools.product(pairs,repeat=n):
            for group in (0,1,2,10):assert condition(rows,group)==oracle(rows,group)

def test_caps():
    for rows in (((10,1000),)*30,((0,0),)*30,((10,1),)+((0,0),)*29,((0,0),)*29+((10,1),)):
        for group in (0,1,10):assert condition(rows,group)==oracle(rows,group)

def test_types_bounds_order():
    for bad in ((),(None,)*31,[(0,0)],Items(((0,0),)),None,'é'):
        refuse((bad,None),'rows: tuple of 1 to 30 pairs required')
    for pos in (0,1,29):
        for bad in (None,(),(0,), (0,0,0),[0,0],Items((0,0)),'Ж'):
            rows=[(0,0)]*30;rows[pos]=bad
            refuse((tuple(rows),None),f'rows[{pos}]: pair (group, count) required')
        for j,(name,cap) in enumerate((('group',10),('count',1000))):
            for bad in (-1,cap+1,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                row=[0,0];row[j]=bad;rows=[(0,0)]*30;rows[pos]=tuple(row)
                refuse((tuple(rows),None),f'rows[{pos}].{name}: whole number 0 to {cap} required')
    for bad in (-1,11,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse((((0,0),),bad),'group: whole number 0 to 10 required')

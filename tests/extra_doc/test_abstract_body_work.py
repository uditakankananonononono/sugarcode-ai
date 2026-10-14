import itertools,re,pytest
from sugarcode.extra_doc.abstract_body_work import work
class Number(int):pass
class Items(tuple):pass

def oracle(rows):
    signed=[];neg=[]
    for i,(force,distance) in enumerate(rows):
        product=sum(force for _ in range(abs(distance)))
        if distance<0:product=-product
        signed.append(product)
        if (force<0 and distance>0) or (force>0 and distance<0):neg.append(i)
    return {'abstract_body_work_validated':False,'not_claimed':('embodied_computation','physical_work_accuracy','robotics_validity'),'signed_work':tuple(signed),'total_work':sum(signed),'negative_positions':tuple(neg)}

def refuse(rows,message):
    with pytest.raises(ValueError) as e:work(rows)
    assert re.fullmatch(re.escape(message),str(e.value))

def test_oracle():
    choices=tuple(itertools.product((-2,-1,0,1,2),repeat=2))
    for n in (1,2):
        for rows in itertools.product(choices,repeat=n):assert work(rows)==oracle(rows)

def test_caps():
    for rows in (((-100,100),)*20,((100,-100),)*20,((100,100),)*20,((0,0),)*19+((-100,-100),)):
        assert work(rows)==oracle(rows)

def test_bad():
    for bad in ((),(None,)*21,[],Items(((0,1),)),None,'é'):
        refuse(bad,'rows: tuple of 1 to 20 integer pairs required')
    for pos in (0,1,19):
        for bad in (None,(),(0,), (0,1,2),[0,1],Items((0,1)),'Ж'):
            rows=[(0,1)]*20;rows[pos]=bad
            refuse(tuple(rows),f'rows[{pos}]: pair (force, displacement) required')
        for col in (0,1):
            for bad in (-101,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                rows=[(0,1)]*20;pair=[0,1];pair[col]=bad;rows[pos]=tuple(pair)
                refuse(tuple(rows),f'rows[{pos}][{col}]: whole number -100 to 100 required')

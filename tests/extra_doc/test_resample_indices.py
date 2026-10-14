import itertools,re,pytest
from sugarcode.extra_doc.resample_indices import resample
class Number(int):pass
class Items(tuple):pass

def oracle(values,indices):
    sampled=[];usage=[0]*len(values)
    for index in indices:sampled.append(values[index]);usage[index]+=1
    return {'resample_indices_validated':False,
            'not_claimed':('randomness','bootstrap_inference','uncertainty'),
            'sampled':tuple(sampled),'total':sum(sampled),'usage':tuple(usage),
            'unused_positions':tuple(i for i,count in enumerate(usage) if not count)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:resample(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in (1,2,3):
        for values in itertools.product((-1000,0,1000),repeat=n):
            for m in (1,2,3,4):
                for indices in itertools.product(range(n),repeat=m):assert resample(values,indices)==oracle(values,indices)

def test_caps_positions():
    values=tuple(range(20))
    for indices in ((0,)*30,(19,)*30,tuple(i%20 for i in range(30)),(0,)*29+(19,)):
        assert resample(values,indices)==oracle(values,indices)

def test_types_bounds_order():
    for j,(name,cap,msg) in enumerate((('values',20,'entries'),('indices',30,'positions'))):
        for bad in ((),(None,)*(cap+1),[0],Items((0,)),None,'é'):
            args=[(0,),(0,)];args[j]=bad
            refuse(args,f'{name}: tuple of 1 to {cap} {msg} required')
    refuse(((None,),None),'indices: tuple of 1 to 30 positions required')
    for pos in (0,1,19):
        for bad in (-1001,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            values=[0]*20;values[pos]=bad
            refuse((tuple(values),(0,)),f'values[{pos}]: whole number -1000 to 1000 required')
    for pos in (0,1,29):
        for bad in (-1,20,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            indices=[0]*30;indices[pos]=bad
            refuse(((0,)*20,tuple(indices)),f'indices[{pos}]: position 0 to values length minus 1 required')

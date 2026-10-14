import itertools,re,pytest
from sugarcode.extra_doc.abstract_polarity import polarity
class Number(int):pass
class Items(tuple):pass

def oracle(values):
    signs=[];changes=[];net=0
    for value in values:
        net+=value
        if value:
            sign=-1 if value<0 else 1
            if signs and signs[-1]!=sign:changes.append(len(signs))
            signs.append(sign)
    return {'abstract_polarity_validated':False,
            'not_claimed':('electrical_safety','brain_stimulation','treatment_efficacy'),
            'nonzero_signs':tuple(signs),'sign_change_positions':tuple(changes),'sign_change_count':len(changes),'net':net}

def refuse(values,message):
    with pytest.raises(ValueError) as exc:polarity(values)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in range(1,7):
        for seq in itertools.product((-100,0,100),repeat=n):assert polarity(seq)==oracle(seq)

def test_caps():
    for seq in ((0,)*30,(-100,)*30,(100,)*30,tuple((-1)**i for i in range(30)),(1,)+(0,)*28+(-1,)):
        assert polarity(seq)==oracle(seq)

def test_types_bounds_order():
    for bad in ((),(None,)*31,[0],Items((0,)),None,'é'):
        refuse(bad,'values: tuple of 1 to 30 abstract values required')
    for pos in (0,1,29):
        for bad in (-101,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            seq=[0]*30;seq[pos]=bad
            refuse(tuple(seq),f'values[{pos}]: whole number -100 to 100 required')

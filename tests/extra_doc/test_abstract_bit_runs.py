import itertools,re,pytest
from sugarcode.extra_doc.abstract_bit_runs import runs
class Number(int):pass
class Items(tuple):pass

def oracle(bits):
    longest=0
    for start in range(len(bits)):
        for end in range(start+1,len(bits)+1):
            if all(v==1 for v in bits[start:end]):longest=max(longest,end-start)
    transitions=tuple(i for i in range(1,len(bits)) if bits[i]!=bits[i-1] and bits[i]>bits[i-1])
    return {'abstract_bit_runs_validated':False,'not_claimed':('behavior_effectiveness','psychological_assessment','care_advice'),'longest_one_run':longest,'start_positions':transitions,'one_count':len([v for v in bits if v==1])}

def refuse(bits,message):
    with pytest.raises(ValueError) as e:runs(bits)
    assert re.fullmatch(re.escape(message),str(e.value))

def test_oracle():
    for n in range(1,9):
        for bits in itertools.product((0,1),repeat=n):assert runs(bits)==oracle(bits)

def test_caps():
    for bits in ((0,)*40,(1,)*40,(0,1)*20,(1,)+(0,)*38+(1,),(0,)+(1,)*39):assert runs(bits)==oracle(bits)

def test_bad():
    for bad in ((),(None,)*41,[0],Items((0,)),None,'é'):
        refuse(bad,'bits: tuple of 1 to 40 integer bits required')
    for pos in (0,1,39):
        for bad in (-1,2,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            values=[0]*40;values[pos]=bad
            refuse(tuple(values),f'bits[{pos}]: integer zero or one required')

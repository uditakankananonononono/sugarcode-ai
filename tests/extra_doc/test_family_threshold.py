import itertools,re,pytest
from fractions import Fraction
from sugarcode.extra_doc.family_threshold import threshold
class Number(int):pass
class Items(tuple):pass

def oracle(values,cutoff):
    limit=Fraction(cutoff,len(values));flags=[]
    for i,value in enumerate(values):
        if value<=limit:flags.append(i)
    floor=int(limit)
    return {'family_threshold_validated':False,
            'not_claimed':('pvalue_generation','family_error_guarantee','inference_validity'),
            'flagged_positions':tuple(flags),'flagged_count':len(flags),'cutoff_floor':floor,'cutoff_remainder':cutoff-floor*len(values)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:threshold(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_fraction_oracle():
    for n in (1,2,3,4):
        for seq in itertools.product((0,1,2,1000000),repeat=n):
            for cutoff in (0,1,2,3,4,5,1000000):assert threshold(seq,cutoff)==oracle(seq,cutoff)

def test_caps():
    for seq in ((0,)*30,(1000000,)*30,(0,)+(1000000,)*29,(1000000,)*29+(0,)):
        for cutoff in (0,1,30,1000000):assert threshold(seq,cutoff)==oracle(seq,cutoff)

def test_types_bounds_order():
    for bad in ((),(None,)*31,[0],Items((0,)),None,'é'):
        refuse((bad,None),'pvalues: tuple of 1 to 30 scaled values required')
    for pos in (0,1,29):
        for bad in (-1,1000001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            seq=[0]*30;seq[pos]=bad
            refuse((tuple(seq),None),f'pvalues[{pos}]: whole number 0 to 1000000 required')
    for bad in (-1,1000001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((0,),bad),'family_cutoff: whole number 0 to 1000000 required')

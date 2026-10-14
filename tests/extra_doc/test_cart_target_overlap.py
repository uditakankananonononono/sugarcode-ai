import itertools
import re
import pytest
from sugarcode.extra_doc.cart_target_overlap import overlap
class Number(int): pass
class Items(tuple): pass

def oracle(targets,observed):
    distinct_targets=[];distinct_observed=[]
    for t in targets:
        if t not in distinct_targets:distinct_targets.append(t)
    for t in observed:
        if t not in distinct_observed:distinct_observed.append(t)
    shared=sum(t in distinct_observed for t in distinct_targets)
    missing=len(distinct_targets)-shared
    extra=sum(t not in distinct_targets for t in distinct_observed)
    return {'cart_target_overlap_validated':False,
            'not_claimed':('cart_design','antigen_specificity','clinical_interpretation'),
            'shared_count':shared,'missing_count':missing,'extra_count':extra,'all_targets_present':missing==0}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:overlap(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    options=[t for n in (1,2,3) for t in itertools.product((0,1,100),repeat=n)]
    for a,b in itertools.product(options,repeat=2):assert overlap(a,b)==oracle(a,b)

def test_caps():
    options=((0,)*20,(100,)*20,tuple(range(20)),(100,)+(0,)*19,(0,)*19+(100,))
    for a,b in itertools.product(options,repeat=2):assert overlap(a,b)==oracle(a,b)

def test_types_bounds_order():
    for j,name in enumerate(('targets','observed')):
        for bad in ((),(None,)*21,[0],Items((0,)),None,'é'):
            args=[(0,),(0,)];args[j]=bad
            refuse(args,f'{name}: tuple of 1 to 20 indices required')
        for pos in (0,1,19):
            for bad in (-1,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                seq=[0]*20;seq[pos]=bad;args=[(0,),(0,)];args[j]=tuple(seq)
                refuse(args,f'{name}[{pos}]: whole number 0 to 100 required')
    refuse(((None,),None),'targets[0]: whole number 0 to 100 required')

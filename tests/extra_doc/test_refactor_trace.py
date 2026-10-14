import itertools
import re
import pytest
from sugarcode.extra_doc.refactor_trace import compare
class Number(int): pass
class Items(tuple): pass

def oracle(before,after):
    pairs=list(itertools.zip_longest(before,after,fillvalue=None))
    differences=[]
    for i,(a,b) in enumerate(pairs):
        if a!=b: differences.append(i)
    return {'refactor_trace_validated':False,
            'not_claimed':('behavior_equivalence','code_transformation','quality_improvement'),
            'difference_positions':tuple(differences),
            'first_difference':differences[0] if differences else None,
            'same_trace':len(differences)==0,'length_change':len(after)-len(before)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: compare(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    options=[t for n in (0,1,2,3) for t in itertools.product((-1000,0,1000),repeat=n)]
    for before,after in itertools.product(options,repeat=2): assert compare(before,after)==oracle(before,after)

def test_caps_first_last():
    options=((0,)*30,(1000,)+(0,)*29,(0,)*29+(-1000,),(0,)*29,())
    for before,after in itertools.product(options,repeat=2): assert compare(before,after)==oracle(before,after)

def test_shapes_and_values_and_order():
    for j,name in enumerate(('before','after')):
        for bad in ((None,)*31,[0],Items((0,)),None,'é'):
            args=[(),()];args[j]=bad
            refuse(args,f'{name}: tuple of 0 to 30 entries required')
        for pos in (0,1,29):
            for bad in (-1001,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                seq=[0]*30;seq[pos]=bad;args=[(),()];args[j]=tuple(seq)
                refuse(args,f'{name}[{pos}]: whole number -1000 to 1000 required')
    refuse((None,None),'before: tuple of 0 to 30 entries required')
    refuse(((None,),None),'before[0]: whole number -1000 to 1000 required')

import itertools
import re
import pytest
from sugarcode.extra_doc.handoff_redesign import handoffs
class Number(int): pass
class Items(tuple): pass

def oracle(before,after):
    found=[]
    for sequence in (before,after):
        positions=[]; previous=sequence[0]
        for i,value in enumerate(sequence[1:],start=1):
            if value!=previous: positions.append(i)
            previous=value
        found.append(tuple(positions))
    old,new=found
    return {'handoff_redesign_validated':False,
            'not_claimed':('process_redesign','organization_outcome','execution'),
            'before_handoffs':old,'after_handoffs':new,'handoffs_saved':len(old)-len(new),
            'steps_saved':len(before)-len(after),'fewer_handoffs':len(old)>len(new)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: handoffs(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    options=[t for n in (1,2,3) for t in itertools.product((0,1,100),repeat=n)]
    for before,after in itertools.product(options,repeat=2): assert handoffs(before,after)==oracle(before,after)

def test_caps_positions():
    options=((0,)*30,tuple(i%2 for i in range(30)),(100,)+(0,)*29,(0,)*29+(100,),(0,))
    for before,after in itertools.product(options,repeat=2): assert handoffs(before,after)==oracle(before,after)

def test_shapes_types_and_order():
    for j,name in enumerate(('before','after')):
        for bad in ((),(None,)*31,[0],Items((0,)),None,'é'):
            args=[(0,),(0,)];args[j]=bad
            refuse(args,f'{name}: tuple of 1 to 30 department indices required')
        for pos in (0,1,29):
            for bad in (-1,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                seq=[0]*30;seq[pos]=bad
                args=[(0,),(0,)];args[j]=tuple(seq)
                refuse(args,f'{name}[{pos}]: whole number 0 to 100 required')
    refuse(((),()),'before: tuple of 1 to 30 department indices required')
    refuse(((None,),()),'before[0]: whole number 0 to 100 required')

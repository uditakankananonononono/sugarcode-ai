import itertools,re,pytest
from sugarcode.extra_doc.abstract_slot_spacing import spacing
class Number(int):pass
class Items(tuple):pass

def oracle(slots,minimum):
    gaps=[];short=[]
    for i,(left,right) in enumerate(zip(slots,slots[1:])):
        gap=right-left;gaps.append(gap)
        if not gap>=minimum:short.append(i)
    return {'abstract_slot_spacing_validated':False,
            'not_claimed':('device_protocol','magnetic_stimulation','treatment'),
            'gaps':tuple(gaps),'short_gap_positions':tuple(short),'all_spaced':len(short)==0,'span':sum(gaps)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:spacing(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in (2,3,4,5):
        for seq in itertools.combinations((0,1,2,3,9,1000),n):
            for minimum in (1,2,3,9,999,1000):assert spacing(seq,minimum)==oracle(seq,minimum)

def test_caps():
    for seq in (tuple(range(30)),tuple(range(29))+(1000,),(0,1000),(0,1)):
        for minimum in (1,2,1000):assert spacing(seq,minimum)==oracle(seq,minimum)

def test_types_bounds_order():
    for bad in ((),(0,),(None,)*31,[0,1],Items((0,1)),None,'é'):
        refuse((bad,None),'slots: tuple of 2 to 30 abstract slots required')
    for pos in (0,1,29):
        for bad in (-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            seq=list(range(30));seq[pos]=bad
            refuse((tuple(seq),None),f'slots[{pos}]: whole number 0 to 1000 required')
    for bad in (0,-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((1,0),bad),'minimum_gap: whole number 1 to 1000 required')
    for seq,pos in (((0,0),1),((1,0),1),(tuple(range(29))+(28,),29)):
        refuse((seq,1),f'slots[{pos}]: slots must strictly increase')

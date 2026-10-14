import itertools
import re
import pytest
from sugarcode.extra_doc.fishbone_groups import groups
class Number(int): pass
class Items(tuple): pass

def oracle(assignments,categories):
    positions=[[] for _ in range(categories)]
    for i,category in enumerate(assignments): positions[category].append(i)
    counts=[];empty=[]
    for i,p in enumerate(positions):
        counts.append(len(p))
        if not p: empty.append(i)
    return {'fishbone_groups_validated':False,
            'not_claimed':('diagram_rendering','causality','assignment_correctness'),
            'positions':tuple(tuple(p) for p in positions),'counts':tuple(counts),
            'empty_categories':tuple(empty),'covered_count':sum(bool(p) for p in positions)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: groups(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for c in range(1,5):
        for n in (1,2,3,4):
            for assignments in itertools.product(range(c),repeat=n):
                assert groups(assignments,c)==oracle(assignments,c)

def test_caps_and_positions():
    for assignments in ((0,)*30,(7,)*30,tuple(i%8 for i in range(30)),(7,)+(0,)*28+(6,)):
        assert groups(assignments,8)==oracle(assignments,8)

def test_shape():
    for bad in ((),(None,)*31,[0],Items((0,)),None,'é'):
        refuse((bad,None),'assignments: tuple of 1 to 30 indices required')

def test_categories():
    for bad in (0,-1,9,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((None,),bad),'categories: whole number 1 to 8 required')

def test_assignment_types_and_bounds():
    for pos in (0,1,29):
        for bad in (-1,8,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            values=[0]*30;values[pos]=bad
            refuse((tuple(values),8),f'assignments[{pos}]: whole number 0 to categories minus 1 required')
    refuse(((1,),1),'assignments[0]: whole number 0 to categories minus 1 required')

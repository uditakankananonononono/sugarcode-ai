import itertools
import re
import pytest
from sugarcode.extra_doc.repetition_runs import runs
class Number(int): pass
class Items(tuple): pass

def oracle(tasks):
    starts=[];lengths=[];previous=None
    for i,value in enumerate(tasks):
        if i==0 or value!=previous: starts.append(i);lengths.append(1)
        else: lengths[-1]+=1
        previous=value
    repeated=[]
    for start,length in zip(starts,lengths):
        if length>=2: repeated.append(start)
    return {'repetition_runs_validated':False,
            'not_claimed':('robotic_execution','automation_suitability','external_effects'),
            'starts':tuple(starts),'lengths':tuple(lengths),'repeated_starts':tuple(repeated),
            'saved_if_collapsed':sum(length-1 for length in lengths)}

def refuse(tasks,message):
    with pytest.raises(ValueError) as exc: runs(tasks)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in range(1,7):
        for tasks in itertools.product((0,1,100),repeat=n): assert runs(tasks)==oracle(tasks)

def test_caps_positions():
    for tasks in ((0,)*30,(100,)*30,tuple(i%2 for i in range(30)),(0,0)+tuple(range(2,30)),tuple(range(28))+(100,100)):
        assert runs(tasks)==oracle(tasks)

def test_shape():
    for bad in ((),(None,)*31,[0],Items((0,)),None,'é'):
        refuse(bad,'tasks: tuple of 1 to 30 indices required')

def test_values():
    for pos in (0,1,29):
        for bad in (-1,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            tasks=[0]*30;tasks[pos]=bad
            refuse(tuple(tasks),f'tasks[{pos}]: whole number 0 to 100 required')

import itertools
import re
import pytest
from sugarcode.extra_doc.workflow_savings import savings
class Number(int): pass
class Items(tuple): pass

def oracle(rows):
    before=0;after=0;improved=[];regressed=[]
    for i,(a,b) in enumerate(rows):
        before+=a;after+=b
        if a>b: improved.append(i)
        if a<b: regressed.append(i)
    return {'workflow_savings_validated':False,
            'not_claimed':('actual_automation','workflow_integration','feasibility'),
            'before_total':before,'after_total':after,'saved':before-after,
            'improved_positions':tuple(improved),'regressed_positions':tuple(regressed)}

def refuse(rows,message):
    with pytest.raises(ValueError) as exc: savings(rows)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    pairs=tuple(itertools.product((0,1,1000),repeat=2))
    for n in (1,2,3):
        for rows in itertools.product(pairs,repeat=n): assert savings(rows)==oracle(rows)

def test_caps():
    for rows in (((0,1000),)*20,((1000,0),)*20,((1000,1000),)*20,((0,1),)+((0,0),)*18+((1,0),)):
        assert savings(rows)==oracle(rows)

def test_outer():
    for bad in ((),(None,)*21,[(0,0)],Items(((0,0),)),None,'é'):
        refuse(bad,'steps: tuple of 1 to 20 pairs required')

def test_nested_shapes_and_values():
    for pos in (0,1,19):
        for bad in (None,(),(0,), (0,0,0),[0,0],Items((0,0)),'Ж'):
            rows=[(0,0)]*20;rows[pos]=bad
            refuse(tuple(rows),f'steps[{pos}]: pair (before, after) required')
        for j,name in enumerate(('before','after')):
            for bad in (-1,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                row=[0,0];row[j]=bad
                rows=[(0,0)]*20;rows[pos]=tuple(row)
                refuse(tuple(rows),f'steps[{pos}].{name}: whole number 0 to 1000 required')

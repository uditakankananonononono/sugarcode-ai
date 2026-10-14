import itertools
import re
import pytest
from sugarcode.extra_doc.checkpoint_score_delta import deltas
class Number(int): pass
class Items(tuple): pass

def oracle(pairs):
    changes=[];positive=[];total=0
    for i,(before,after) in enumerate(pairs):
        change=after-before;changes.append(change);total+=change
        if after>before:positive.append(i)
    return {'checkpoint_score_delta_validated':False,
            'not_claimed':('immune_response','drug_efficacy','clinical_interpretation'),
            'changes':tuple(changes),'positive_positions':tuple(positive),'total_change':total,'positive_count':len(positive)}

def refuse(pairs,message):
    with pytest.raises(ValueError) as exc:deltas(pairs)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    pairs=tuple(itertools.product((0,1,100),repeat=2))
    for n in (1,2,3):
        for rows in itertools.product(pairs,repeat=n):assert deltas(rows)==oracle(rows)

def test_caps_first_last():
    for rows in (((0,100),)*20,((100,0),)*20,((0,0),)*20,((0,1),)+((0,0),)*19,((0,0),)*19+((0,1),)):
        assert deltas(rows)==oracle(rows)

def test_types_bounds_order():
    for bad in ((),(None,)*21,[(0,0)],Items(((0,0),)),None,'é'):
        refuse(bad,'pairs: tuple of 1 to 20 score pairs required')
    for pos in (0,1,19):
        for bad in (None,(),(0,), (0,0,0),[0,0],Items((0,0)),'Ж'):
            rows=[(0,0)]*20;rows[pos]=bad
            refuse(tuple(rows),f'pairs[{pos}]: pair (before, after) required')
        for j,name in enumerate(('before','after')):
            for bad in (-1,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                row=[0,0];row[j]=bad;rows=[(0,0)]*20;rows[pos]=tuple(row)
                refuse(tuple(rows),f'pairs[{pos}].{name}: whole number 0 to 100 required')

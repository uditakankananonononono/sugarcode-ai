import itertools,re,pytest
from sugarcode.extra_doc.abstract_cloak_mask import evaluate
class Number(int):pass
class Items(tuple):pass

def oracle(rows):
    visible=[];hidden=[]
    for i,(value,mask) in enumerate(rows):
        if mask:visible.append(value)
        else:visible.append(0);hidden.append(i)
    return {'abstract_cloak_mask_validated':False,'not_claimed':('physical_invisibility','physical_validity','production_readiness'),'visible_values':tuple(visible),'hidden_positions':tuple(hidden),'visible_total':sum(visible)}

def refuse(rows,message):
    with pytest.raises(ValueError) as e:evaluate(rows)
    assert re.fullmatch(re.escape(message),str(e.value))

def test_oracle():
    for n in (1,2,3):
        for rows in itertools.product([(0, 0), (0, 1), (1, 0), (1, 1), (100, 0), (100, 1)],repeat=n):assert evaluate(rows)==oracle(rows)

def test_caps():
    for pair in [(0, 0), (0, 1), (1, 0), (1, 1), (100, 0), (100, 1)]:
        rows=(pair,)*20
        assert evaluate(rows)==oracle(rows)
    for pair in [(0, 0), (0, 1), (1, 0), (1, 1), (100, 0), (100, 1)]:
        rows=((0, 0),)*19+(pair,)
        assert evaluate(rows)==oracle(rows)

def test_bad():
    for bad in ((),(None,)*21,[],Items(((0, 0),)),None,'é'):
        refuse(bad,'rows: tuple of 1 to 20 integer pairs required')
    for pos in (0,1,19):
        for bad in (None,(),(0,), (0,1,2),[0,1],Items((0,1)),'Ж'):
            rows=[(0, 0)]*20;rows[pos]=bad
            refuse(tuple(rows),f'rows[{pos}]: pair (value, mask) required')
        for bad in [-1, 101]+[True,False,None,Number(1),1.0,'é','ａ','Ж']:
            rows=[(0, 0)]*20;rows[pos]=(bad,None)
            refuse(tuple(rows),f'rows[{pos}].value: whole number 0 to 100 required')
        for bad in [-1, 2]+[True,False,None,Number(1),1.0,'é','ａ','Ж']:
            rows=[(0, 0)]*20;rows[pos]=(0,bad)
            refuse(tuple(rows),f'rows[{pos}].mask: integer zero or one required')

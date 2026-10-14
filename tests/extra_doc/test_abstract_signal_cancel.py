import itertools,re,pytest
from sugarcode.extra_doc.abstract_signal_cancel import evaluate
class Number(int):pass
class Items(tuple):pass

def oracle(rows):
    residuals=[];cancelled=[];total=0
    for i,(left,right) in enumerate(rows):
        residual=left-(-right);residuals.append(residual)
        if left==-right:cancelled.append(i)
        total+=residual if residual>=0 else -residual
    return {'abstract_signal_cancel_validated':False,'not_claimed':('physical_sound_manipulation','physical_validity','production_readiness'),'residuals':tuple(residuals),'cancelled_positions':tuple(cancelled),'magnitude_total':total}

def refuse(rows,message):
    with pytest.raises(ValueError) as e:evaluate(rows)
    assert re.fullmatch(re.escape(message),str(e.value))

def test_oracle():
    for n in (1,2,3):
        for rows in itertools.product([(-100, 100), (100, -100), (-1, 1), (0, 0), (1, 1), (-100, -100), (100, 100)],repeat=n):assert evaluate(rows)==oracle(rows)

def test_caps():
    for pair in [(-100, 100), (100, -100), (-1, 1), (0, 0), (1, 1), (-100, -100), (100, 100)]:
        rows=(pair,)*20
        assert evaluate(rows)==oracle(rows)
    for pair in [(-100, 100), (100, -100), (-1, 1), (0, 0), (1, 1), (-100, -100), (100, 100)]:
        rows=((-100, 100),)*19+(pair,)
        assert evaluate(rows)==oracle(rows)

def test_bad():
    for bad in ((),(None,)*21,[],Items(((-100, 100),)),None,'é'):
        refuse(bad,'rows: tuple of 1 to 20 integer pairs required')
    for pos in (0,1,19):
        for bad in (None,(),(0,), (0,1,2),[0,1],Items((0,1)),'Ж'):
            rows=[(-100, 100)]*20;rows[pos]=bad
            refuse(tuple(rows),f'rows[{pos}]: pair (left, right) required')
        for bad in [-101, 101]+[True,False,None,Number(1),1.0,'é','ａ','Ж']:
            rows=[(-100, 100)]*20;rows[pos]=(bad,None)
            refuse(tuple(rows),f'rows[{pos}].left: whole number -100 to 100 required')
        for bad in [-101, 101]+[True,False,None,Number(1),1.0,'é','ａ','Ж']:
            rows=[(-100, 100)]*20;rows[pos]=(0,bad)
            refuse(tuple(rows),f'rows[{pos}].right: whole number -100 to 100 required')

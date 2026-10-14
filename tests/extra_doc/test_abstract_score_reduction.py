import itertools,re,pytest
from sugarcode.extra_doc.abstract_score_reduction import reductions as call
class Number(int):pass
class Items(tuple):pass
NC=('pain_assessment', 'treatment_advice', 'efficacy')
def oracle(rows,scalar):
    changes=[];positions=[];total=0
    for i,(before,after) in enumerate(rows):
        change=before-after;changes.append(change);total+=change
        if before>=after+scalar:positions.append(i)
    return {'abstract_score_reduction_validated':False,'not_claimed':NC,
            'reductions':tuple(changes),'meeting_positions':tuple(positions),
            'meeting_count':len(positions),'total_reduction':total}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:call(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))
def test_oracle():
    choices=tuple(itertools.product((0,1,100),repeat=2))
    for n in (1,2,3):
        for rows in itertools.product(choices,repeat=n):
            for scalar in (0,1,100):assert call(rows,scalar)==oracle(rows,scalar)
def test_caps_and_positions():
    for rows in (((100,100),)*20,((0,0),)*20,((100,1),)+((1,1),)*19,((1,1),)*19+((100,1),)):
        for scalar in (0,1,100):assert call(rows,scalar)==oracle(rows,scalar)
def test_types_bounds_order():
    for bad in ((),(None,)*21,[(1,1)],Items(((1,1),)),None,'é'):
        refuse((bad,None),'pairs: tuple of 1 to 20 pairs required')
    for pos in (0,1,19):
        for bad in (None,(),(1,), (1,1,1),[1,1],Items((1,1)),'Ж'):
            rows=[(1,1)]*20;rows[pos]=bad
            refuse((tuple(rows),None),f'pairs[{pos}]: pair (before, after) required')
        for j,name in enumerate(('before', 'after')):
            for bad in (-1,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                row=[1,1];row[j]=bad;rows=[(1,1)]*20;rows[pos]=tuple(row)
                refuse((tuple(rows),None),f'pairs[{pos}].{name}: whole number 0 to 100 required')
    for bad in (-1,101,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse((((1,1),),bad),'minimum: whole number 0 to 100 required')

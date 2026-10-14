import itertools,pytest
from sugarcode.extra_doc.abstract_self_contingency import contingency
class Number(int):pass
class Items(tuple):pass

def oracle(rows):
    cells=[0,0,0,0];mismatch=[];agree=0
    for i,(a,b) in enumerate(rows):
        cells[2*a+b]+=1
        if a==b:agree+=1
        else:mismatch.append(i)
    return {'abstract_self_contingency_validated':False,'not_claimed':('assessment_truth','metacognitive_validity','learner_evaluation'),'cells_00_01_10_11':tuple(cells),'disagreement_positions':tuple(mismatch),'agreement_count':agree}

def refuse(rows,message):
    with pytest.raises(ValueError) as exc:contingency(rows)
    assert str(exc.value)==message

def test_oracle():
    for n in (1,2,3,4):
        for rows in itertools.product(((0,0),(0,1),(1,0),(1,1)),repeat=n):assert contingency(rows)==oracle(rows)

@pytest.mark.parametrize('rows',[(p,)*n for p in ((0,0),(0,1),(1,0),(1,1)) for n in (1,20)])
def test_accept(rows):
    result=contingency(rows);assert result==oracle(rows)
    assert result['cells_00_01_10_11'] is not rows

@pytest.mark.parametrize('bad',[(),((0,0),)*21,[],[(0,0)]*21,{}, {0:(0,0),'extra':0},Items(((0,0),)),None])
def test_shape(bad):refuse(bad,'rows: tuple of 1 to 20 bit pairs required')

def test_refusals():
    for pos in (0,1,19):
        for bad in ((),(0,), (0,0,0),[0,0],{'self_bit':0,'observed_bit':0,'extra':0},Items((0,0)),None):
            rows=[(0,0)]*20;rows[pos]=bad
            refuse(tuple(rows),f'rows[{pos}]: pair (self_bit, observed_bit) required')
        for col in (0,1):
            for bad in (-1,2,True,False,Number(1),1.0,None,'é','Ж','ａ'):
                rows=[(0,0)]*20;pair=[0,0];pair[col]=bad;rows[pos]=tuple(pair)
                refuse(tuple(rows),f'rows[{pos}][{col}]: integer zero or one required')

def test_singleton_full():
    assert contingency(((1,0),))=={'abstract_self_contingency_validated':False,'not_claimed':('assessment_truth','metacognitive_validity','learner_evaluation'),'cells_00_01_10_11':(0,0,1,0),'disagreement_positions':(0,),'agreement_count':0}

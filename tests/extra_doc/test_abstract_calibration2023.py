import itertools,pytest
from sugarcode.extra_doc.abstract_calibration2023 import calibration
class Number(int):pass
class Items(tuple):pass

def oracle(rows):
    counts=[0]*11;success=[0]*11;gaps=[0]*11
    for confidence,correct in rows:
        counts[confidence]+=1;success[confidence]+=correct
        gaps[confidence]+=10*correct-confidence
    return {'abstract_calibration_validated':False,'not_claimed':('metacognitive_validity','confidence_truth','learning_benefit'),'bin_counts':tuple(counts),'bin_successes':tuple(success),'signed_calibration_units':tuple(gaps)}

@pytest.mark.parametrize('pair',[(0,0),(0,1),(1,0),(1,1),(10,0),(10,1)])
@pytest.mark.parametrize('count',[1,20])
def test_caps(pair,count):
    rows=(pair,)*count;result=calibration(rows)
    assert result==oracle(rows)
    assert result['bin_counts'] is not rows

def test_oracle():
    for n in (1,2,3):
        for rows in itertools.product(((0,0),(0,1),(1,0),(5,1),(10,0),(10,1)),repeat=n):assert calibration(rows)==oracle(rows)

def refuse(rows,message):
    with pytest.raises(ValueError) as e:calibration(rows)
    assert str(e.value)==message

def test_refusals():
    for bad in ((),((0,0),)*21,[],[(0,0)]*21,{}, {'extra':0},Items(((0,0),)),None):refuse(bad,'rows: tuple of 1 to 20 confidence-bit pairs required')
    for i in (0,1,19):
        for bad in ((),(0,), (0,0,0),[0,0],{'confidence':0,'correct':0,'extra':0},Items((0,0)),None):
            rows=[(0,0)]*20;rows[i]=bad
            refuse(tuple(rows),f'rows[{i}]: pair (confidence, correct) required')
        for bad in (-1,11,True,False,Number(1),1.0,None,'é','Ж','ａ'):
            rows=[(0,0)]*20;rows[i]=(bad,None)
            refuse(tuple(rows),f'rows[{i}].confidence: integer 0 to 10 required')
        for bad in (-1,2,True,False,Number(1),1.0,None,'é','Ж','ａ'):
            rows=[(0,0)]*20;rows[i]=(0,bad)
            refuse(tuple(rows),f'rows[{i}].correct: integer zero or one required')

def test_singleton():
    assert calibration(((0,1),))=={'abstract_calibration_validated':False,'not_claimed':('metacognitive_validity','confidence_truth','learning_benefit'),'bin_counts':(1,0,0,0,0,0,0,0,0,0,0),'bin_successes':(1,0,0,0,0,0,0,0,0,0,0),'signed_calibration_units':(10,0,0,0,0,0,0,0,0,0,0)}

def test_fresh():
    result=calibration(((0,1),));result['bin_counts']=('caller',)
    assert calibration(((0,1),))==oracle(((0,1),))

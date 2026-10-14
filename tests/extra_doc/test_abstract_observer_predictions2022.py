import itertools,pytest
from sugarcode.extra_doc.abstract_observer_predictions2022 import audit
class Number(int):pass
class Items(tuple):pass

def oracle(actual,predictions):
    errors=[];counts=[];perfect=[]
    for i,row in enumerate(predictions):
        missing=[];correct=0
        for j,(a,b) in enumerate(zip(actual,row)):
            if a==b:correct+=1
            else:missing.append(j)
        errors.append(tuple(missing));counts.append(correct)
        if correct==len(actual):perfect.append(i)
    return {'abstract_observer_predictions_validated':False,'not_claimed':('reflexivity','observer_theory','epistemic_validity'),'error_positions':tuple(errors),'correct_counts':tuple(counts),'perfect_observers':tuple(perfect)}

@pytest.mark.parametrize('actual',[(0,),(1,),(0,)*20,(1,)*20,(0,1)*10])
@pytest.mark.parametrize('count',[1,10])
def test_caps(actual,count):
    predictions=(actual,)*count
    result=audit(actual,predictions);assert result==oracle(actual,predictions)
    assert result['error_positions'] is not predictions

def test_oracle():
    for n in (1,2,3):
        choices=tuple(itertools.product((0,1),repeat=n))
        for actual in choices:
            for predictions in itertools.product(choices,repeat=2):assert audit(actual,predictions)==oracle(actual,predictions)

def refuse(args,message):
    with pytest.raises(ValueError) as e:audit(*args)
    assert str(e.value)==message

def test_refusals():
    for bad in ((),(0,)*21,[],[0]*21,{}, {'extra':0},Items((0,)),None):refuse((bad,None),'actual: tuple of 1 to 20 integer bits required')
    for bad in ((),((0,),)*11,[],[(0,)]*11,{}, {'extra':0},Items(((0,),)),None):refuse(((0,),bad),'predictions: tuple of 1 to 10 sequences required')
    for i in (0,1,9):
        for bad in ((),(0,)*21,(0,)*19,[0]*20,{'extra':0},Items((0,)*20),None):
            rows=[(0,)*20]*10;rows[i]=bad
            refuse(((0,)*20,tuple(rows)),f'predictions[{i}]: tuple matching actual length required')
        for j in (0,1,19):
            for bad in (-1,2,True,False,Number(1),1.0,None,'é','Ж','ａ'):
                actual=[0]*20;actual[j]=bad
                refuse((tuple(actual),None),f'actual[{j}]: integer zero or one required')
                rows=[(0,)*20]*10;row=[0]*20;row[j]=bad;rows[i]=tuple(row)
                refuse(((0,)*20,tuple(rows)),f'predictions[{i}][{j}]: integer zero or one required')

def test_singleton():
    assert audit((1,),((0,),))=={'abstract_observer_predictions_validated':False,'not_claimed':('reflexivity','observer_theory','epistemic_validity'),'error_positions':((0,),),'correct_counts':(0,),'perfect_observers':()}

def test_fresh():
    a=audit((0,),((0,),));a['error_positions']=('caller',)
    assert audit((0,),((0,),))==oracle((0,),((0,),))

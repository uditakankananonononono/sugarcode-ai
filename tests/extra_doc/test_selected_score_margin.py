import itertools,re,pytest
from sugarcode.extra_doc.selected_score_margin import margins
class Number(int):pass
class Items(tuple):pass

def oracle(scores,selected,threshold):
    deltas=[];below=[]
    for pos,index in enumerate(selected):
        value=scores[index];deltas.append(value-threshold)
        if value<threshold:below.append(pos)
    return {'selected_score_margin_validated':False,
            'not_claimed':('post_selection_inference','significance','selection_bias_correction'),
            'margins':tuple(deltas),'below_positions':tuple(below),'all_meet':len(below)==0}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:margins(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for n in (1,2,3):
        for scores in itertools.product((-1,0,1),repeat=n):
            for m in (1,2,3):
                for indices in itertools.product(range(n),repeat=m):
                    for threshold in (-1,0,1):assert margins(scores,indices,threshold)==oracle(scores,indices,threshold)

def test_caps_positions():
    scores=tuple(range(30))
    for indices in ((0,)*30,(29,)*30,tuple(range(30))):
        for threshold in (-1000,0,29,1000):assert margins(scores,indices,threshold)==oracle(scores,indices,threshold)
    assert margins((-1000,1000),(0,1),0)==oracle((-1000,1000),(0,1),0)

def test_types_bounds_order():
    for j,(name,kind) in enumerate((('scores','values'),('selected','positions'))):
        for bad in ((),(None,)*31,[0],Items((0,)),None,'é'):
            args=[(0,),(0,),None];args[j]=bad
            refuse(args,f'{name}: tuple of 1 to 30 {kind} required')
    refuse(((None,),None,None),'selected: tuple of 1 to 30 positions required')
    for pos in (0,1,29):
        for bad in (-1001,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            scores=[0]*30;scores[pos]=bad
            refuse((tuple(scores),(0,),None),f'scores[{pos}]: whole number -1000 to 1000 required')
        for bad in (-1,30,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            indices=[0]*30;indices[pos]=bad
            refuse(((0,)*30,tuple(indices),None),f'selected[{pos}]: position 0 to scores length minus 1 required')
    for bad in (-1001,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((0,),(0,),bad),'threshold: whole number -1000 to 1000 required')

import itertools,re,pytest
from sugarcode.extra_doc.fold_complements import complements
class Number(int):pass
class Items(tuple):pass

def oracle(assignments,folds):
    held=[[] for _ in range(folds)];training=[[] for _ in range(folds)]
    for i,fold in enumerate(assignments):
        held[fold].append(i)
        for f in range(folds):
            if f!=fold:training[f].append(i)
    return {'fold_complements_validated':False,
            'not_claimed':('model_fitting','overfitting_prevention','estimate_validity'),
            'held_positions':tuple(tuple(p) for p in held),'training_positions':tuple(tuple(p) for p in training),'held_counts':tuple(len(p) for p in held)}

def refuse(args,message):
    with pytest.raises(ValueError) as exc:complements(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    for folds in (2,3,4):
        for n in (2,3,4,5):
            for seq in itertools.product(range(folds),repeat=n):
                if len(set(seq))==folds:assert complements(seq,folds)==oracle(seq,folds)

def test_caps_and_missing_fold():
    seq=tuple(i%8 for i in range(30));assert complements(seq,8)==oracle(seq,8)
    for missing in (0,1,7):
        seq=tuple(i for i in range(8) if i!=missing)
        refuse((seq,8),f'folds[{missing}]: at least one held-out position required')

def test_types_bounds_order():
    for bad in ((),(0,),(None,)*31,[0,1],Items((0,1)),None,'é'):
        refuse((bad,None),'assignments: tuple of 2 to 30 fold indices required')
    for bad in (0,1,9,True,False,None,Number(2),2.0,'é','ａ','Ж'):
        refuse(((None,None),bad),'folds: whole number 2 to 8 required')
    for pos in (0,1,29):
        for bad in (-1,8,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            seq=[0]*30;seq[pos]=bad
            refuse((tuple(seq),8),f'assignments[{pos}]: fold index 0 to folds minus 1 required')

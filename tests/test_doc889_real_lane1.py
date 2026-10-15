import random,pytest
from itertools import product
from sugarcode.extra_doc import version889 as m

def exact(a,b):
 assert type(a) is type(b)
 if type(b) is dict:
  assert list(a)==list(b)
  for k in b:exact(a[k],b[k])
 elif type(b) in (list,tuple):
  assert len(a)==len(b)
  for x,y in zip(a,b):exact(x,y)
 elif type(b) is bool:assert a is b
 else:assert a==b

def test_independent_truth_set_intersections():
 rng=random.Random(889)
 for _ in range(150):
  width=rng.randint(1,4);universe=list(product((0,1),repeat=width));hs=list(product((-1,0,1),repeat=width));truth={h:{b for b in universe if all(h[j] in (-1,b[j]) for j in range(width))} for h in hs};obs=[(rng.choice(universe),rng.randrange(2)) for i in range(rng.randint(1,12))];live=set(hs)
  for b,y in obs:live.intersection_update({h for h in hs if (b in truth[h])==bool(y)})
  survivors=[h for h in hs if h in live];pred=[]
  for b in universe:
   count=sum(b in truth[h] for h in survivors);pred.append((b,0 if survivors and count==0 else 1 if survivors and count==len(survivors) else None))
  exact(m.eliminate(width,obs),dict(hypotheses=survivors,predictions=pred,inconsistent=not bool(survivors),generalization_validated=False))
 assert m.eliminate(1,[((0,),0),((0,),1)])['inconsistent'] is True
class T(tuple):pass
class L(list):pass
class I(int):pass

def test_validation_caps_order():
 for v in (True,1.0,I(1),None,0,5):
  with pytest.raises(ValueError,match='width must'):m.eliminate(v,None)
 for v in (None,(),L([((0,),0)]),[],[((0,),0)]*13):
  with pytest.raises(ValueError,match='observations must'):m.eliminate(1,v)
 for v in (None,[],T(((0,),0)),((0,),),((0,),0,0)):
  with pytest.raises(ValueError,match='observation must'):m.eliminate(1,[v])
 for v in (None,[0],T((0,)),(),(0,0)):
  with pytest.raises(ValueError,match='bits must be exact aligned'):m.eliminate(1,[(v,0)])
 for v in (True,1.0,I(1),None,-1,2):
  with pytest.raises(ValueError,match='bits must be exact binary'):m.eliminate(1,[((v,),0)])
  with pytest.raises(ValueError,match='outcome must'):m.eliminate(1,[((0,),v)])
 for w in (1,4):
  for b in (0,1):
   for y in (0,1):assert m.eliminate(w,[((b,)*w,y)]*12)
 with pytest.raises(ValueError,match='bits must be exact binary'):m.eliminate(1,[((True,),0),None])
 assert m.SCOPE=='PARTIAL: exact finite binary-conjunction hypothesis elimination'
 assert m.NOT_CLAIMED==('valid labels','experiment selection','generalization','production readiness')

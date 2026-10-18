import itertools as it
import copy
import pytest
from sugarcode.extra_doc import concept491_weighing as m


def physical(w,h):
    # Explicit genuine weight10 and counterfeit weight9or11.
    weights=[10]*len(w);weights[h[0]]+=h[1]
    left=sum(weights[i] for i in range(len(w)) if w[i]==1)
    right=sum(weights[i] for i in range(len(w)) if w[i]==-1)
    return (left>right)-(left<right)


def all_weighings(n):
    return tuple(w for w in it.product((-1,0,1),repeat=n) if w.count(-1)==w.count(1))


def naive_possible(hs,menu,depth):
    if len(hs)<=1:return True
    if depth==0:return False
    return any(all(naive_possible(tuple(h for h in hs if physical(w,h)==o),menu,depth-1) for o in (-1,0,1)) for w in menu)


def check_certificate(tree,hs,menu,depth):
    if tree[0]=='leaf':
        assert len(hs)<=1 and tree==('leaf',hs[0] if hs else None)
    else:
        assert depth>0 and tree[0]=='test' and type(tree[1])is int
        assert len(tree[2])==3
        for outcome,child in zip((-1,0,1),tree[2]):check_certificate(child,tuple(h for h in hs if physical(menu[tree[1]],h)==outcome),menu,depth-1)


def test_exhaustive_outcomes_partitions_profiles():
    for n in range(1,5):
        hs=tuple(it.product(range(n),(-1,1)))
        for w in all_weighings(n):
            for h in hs:assert m.weighing_outcome(n,h,w)==physical(w,h)
            for subset_mask in range(1<<len(hs)):
                subset=tuple(h for i,h in enumerate(hs) if subset_mask & 1<<i)
                expected=tuple(tuple(h for h in subset if physical(w,h)==o) for o in (-1,0,1))
                assert m.hypothesis_partition(n,subset,w)==expected
                sizes=tuple(map(len,expected))
                assert m.weighing_information_profile(n,subset,w)==(sizes,max(sizes),sum(s*s for s in sizes))


def test_transcripts_and_robust_oracles():
    n=3;hs=tuple(it.product(range(n),(-1,1)));ws=all_weighings(n)
    for measurements in it.product(ws,repeat=2):
        for outcomes in it.product((-1,0,1),repeat=2):
            transcript=tuple(zip(measurements,outcomes))
            distances={h:sum(physical(w,h)!=o for w,o in transcript) for h in hs}
            expected=tuple(h for h in hs if distances[h]==0)
            assert m.consistent_hypotheses(n,hs,transcript)==expected
            assert m.transcript_consistent(n,transcript)is bool(expected)
            for budget in range(3):assert m.robust_hypotheses(n,hs,transcript,budget)==tuple(h for h in hs if distances[h]<=budget)


def test_finite_menu_discrimination_and_adaptive_oracles():
    for n in (1,2,3):
        hs=tuple(it.product(range(n),(-1,1)));ws=all_weighings(n)
        menus=tuple(it.combinations(ws,min(3,len(ws))))+((),)
        for menu in menus:
            for mask in range(1<<len(hs)):
                subset=tuple(h for i,h in enumerate(hs) if mask & 1<<i)
                scores=[]
                for w in menu:
                    sizes=[sum(physical(w,h)==o for h in subset) for o in (-1,0,1)];scores.append((max(sizes),sum(x*x for x in sizes)))
                assert m.best_weighings(n,subset,menu)==tuple(i for i,s in enumerate(scores) if s==min(scores))
                pairs=tuple((i,j) for i,j in it.combinations(range(len(subset)),2) if all(physical(w,subset[i])==physical(w,subset[j]) for w in menu))
                assert m.indistinguishable_pairs(n,subset,menu)==pairs
                separating=[]
                for size in range(len(menu)+1):
                    for ids in it.combinations(range(len(menu)),size):
                        if all(any(physical(menu[k],subset[i])!=physical(menu[k],subset[j]) for k in ids) for i,j in it.combinations(range(len(subset)),2)):separating.append(ids)
                    if separating:break
                assert m.minimum_nonadaptive_tests(n,subset,menu)==(tuple(separating) if separating else None)
                for depth in range(3):
                    certificate=m.adaptive_depth_certificate(n,subset,menu,depth)
                    assert (certificate is not None)==naive_possible(subset,menu,depth)
                    if certificate is not None:check_certificate(certificate,subset,menu,depth)


def refuse(fn,args,code):
    saved=copy.deepcopy(args)
    with pytest.raises(ValueError) as exc:fn(*args)
    assert str(exc.value)=='W491:'+code
    assert args==saved


def test_validation_order_and_caps():
    class I(int):pass
    class T(tuple):pass
    hs=((0,-1),(0,1));w=(1,-1);menu=(w,);transcript=((w,0),)
    calls=[(m.weighing_outcome,(hs[0],w)),(m.hypothesis_partition,(hs,w)),(m.consistent_hypotheses,(hs,transcript)),(m.transcript_consistent,(transcript,)),(m.weighing_information_profile,(hs,w)),(m.best_weighings,(hs,menu)),(m.indistinguishable_pairs,(hs,menu)),(m.minimum_nonadaptive_tests,(hs,menu)),(m.robust_hypotheses,(hs,transcript,0)),(m.adaptive_depth_certificate,(hs,menu,0))]
    for fn,tail in calls:
        for n,code in ((True,'type:n'),(I(2),'type:n'),(0,'bound:n'),(7,'bound:n')):refuse(fn,(n,)+tail,code)
    for fn,tail in ((m.hypothesis_partition,(w,)),(m.consistent_hypotheses,(transcript,)),(m.weighing_information_profile,(w,)),(m.best_weighings,(menu,)),(m.indistinguishable_pairs,(menu,)),(m.minimum_nonadaptive_tests,(menu,)),(m.robust_hypotheses,(transcript,0)),(m.adaptive_depth_certificate,(menu,0))):
        for bad,code in ((None,'type:hypotheses'),(T(()),'type:hypotheses'),((None,)*13,'length:hypotheses'),((None,),'shape:hypothesis'),((T((0,1)),),'shape:hypothesis'),(((True,1),),'type:hypothesis:entry'),(((0,I(1)),),'type:hypothesis:entry'),(((-1,1),),'bound:hypothesis:entry'),(((2,1),),'bound:hypothesis:entry'),(((0,0),),'bound:hypothesis:entry'),(((0,2),),'bound:hypothesis:entry'),(((0,1),(0,1)),'duplicate:hypothesis'),(((-1,1),(0,True)),'type:hypothesis:entry')):refuse(fn,(2,bad)+tail,code)
    for bad,code in ((None,'shape:weighing'),((0,),'shape:weighing'),(T((1,-1)),'shape:weighing'),((True,-1),'type:weighing:entry'),((2,-2),'bound:weighing:entry'),((1,0),'unbalanced:pans')):
        refuse(m.weighing_outcome,(2,(0,1),bad),code)
        refuse(m.hypothesis_partition,(2,hs,bad),code)
    for fn in (m.best_weighings,m.indistinguishable_pairs,m.minimum_nonadaptive_tests,m.adaptive_depth_certificate):
        tail=(0,) if fn is m.adaptive_depth_certificate else ()
        for bad,code in ((None,'type:menu'),((None,)*7,'length:menu'),((None,),'shape:weighing'),((w,w),'duplicate:weighing')):refuse(fn,(2,hs,bad)+tail,code)
    for bad,code in ((None,'type:transcript'),((None,)*9,'length:transcript'),((None,),'shape:transcript:row'),(((w,True),),'type:outcome'),(((w,2),),'bound:outcome'),(((w,-2),),'bound:outcome')):
        refuse(m.consistent_hypotheses,(2,hs,bad),code);refuse(m.transcript_consistent,(2,bad),code)
    for fn,head,label,hi in ((m.robust_hypotheses,(2,hs,transcript),'error_budget',8),(m.adaptive_depth_certificate,(2,hs,menu),'depth',3)):
        for bad,code in ((True,'type:'),(I(0),'type:'),(-1,'bound:'),(hi+1,'bound:')):refuse(fn,head+(bad,),code+label)
    all_hs=tuple(it.product(range(6),(-1,1)));ws=all_weighings(6)[:6]
    assert len(all_hs)==12 and len(ws)==6
    assert len(m.robust_hypotheses(6,all_hs,tuple((ws[0],0) for _ in range(8)),8))==12
    m.minimum_nonadaptive_tests(6,all_hs,ws)
    m.adaptive_depth_certificate(6,all_hs,ws,3)
    assert m.weighing_outcome(6,(5,-1),(1,1,1,-1,-1,-1))==1
    assert m.CLAIMS=={'agi_like_intelligence':False,'physical_validity':False,'production_ready':False}
    assert m.SCOPE=='PARTIAL exact finite balance-scale hypothesis discrimination'
    assert m.NOT_CLAIMED==('AGI-like intelligence','physical weighing validity','global strategy optimality','production readiness')


def test_exact_certificate_ties_mixed_errors_and_purity():
    hs=((0,-1),(0,1));menu=((1,-1),(-1,1))
    assert m.adaptive_depth_certificate(2,hs,menu,1)==('test',0,(('leaf',(0,-1)),('leaf',None),('leaf',(0,1))))
    assert m.adaptive_depth_certificate(2,(),(),3)==('leaf',None)
    assert m.adaptive_depth_certificate(2,((1,1),),(),0)==('leaf',(1,1))
    refuse(m.weighing_outcome,(2,(-1,True),None),'type:hypothesis:entry')
    refuse(m.best_weighings,(2,((0,1),),((2,-2),(True,0))),'type:weighing:entry')
    refuse(m.robust_hypotheses,(2,hs,((((1,-1),True)),),True),'type:outcome')
    refuse(m.adaptive_depth_certificate,(2,hs,(None,),True),'shape:weighing')
    for fn,args in ((m.best_weighings,(2,hs,menu)),(m.minimum_nonadaptive_tests,(2,hs,menu)),(m.adaptive_depth_certificate,(2,hs,menu,3))):
        before=copy.deepcopy(args);first=fn(*args);assert args==before and fn(*args)==first

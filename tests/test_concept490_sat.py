import itertools as it
import copy
import pytest
from sugarcode.extra_doc import concept490_sat as m


def truth(n, cnf):
    out=[]
    for bits in it.product((False,True),repeat=n):
        if all(any(bits[abs(x)-1] if x>0 else not bits[abs(x)-1] for x in c) for c in cnf):
            out.append(sum(int(b)*2**i for i,b in enumerate(bits)))
    return tuple(sorted(out))


def canonical(cnf):
    return tuple(sorted(set(tuple(sorted(c,key=lambda x:(abs(x),x))) for c in cnf)))


def check(n, cnf):
    models=truth(n,cnf)
    assert m.sat_models(n,cnf)==models
    assert m.sat_count(n,cnf)==len(models)
    assert m.sat_hamming_profile(n,cnf)==tuple(sum(bin(mask).count('1')==k for mask in models) for k in range(n+1))
    assert m.sat_backbone(n,cnf)==(tuple(a if all(mask & 2**(a-1) for mask in models) else -a for a in range(1,n+1) if all(mask & 2**(a-1) for mask in models) or all(not mask & 2**(a-1) for mask in models)) if models else None)
    for mask in range(2**n):
        assert m.sat_evaluate(n,cnf,mask) is (mask in models)
    subsets=[indices for k in range(1,len(cnf)+1) for indices in it.combinations(range(len(cnf)),k)]
    unsat=[s for s in subsets if not truth(n,tuple(cnf[i] for i in s))]
    expected=tuple(sorted(s for s in unsat if not any(set(t)<set(s) for t in unsat)))
    assert m.sat_minimal_unsat_cores(n,cnf)==expected
    literals=tuple(range(-n,0))+tuple(range(1,n+1))
    expected=[]
    for a in literals:
        antecedents=[mask for mask in models if bool(mask & 2**(abs(a)-1))==(a>0)]
        for b in literals:
            if abs(a)!=abs(b) and antecedents and all(bool(mask & 2**(abs(b)-1))==(b>0) for mask in antecedents):expected.append((a,b))
    assert m.sat_forced_implications(n,cnf)==tuple(expected)
    for partial in ((),)+tuple((a,) for a in literals):
        fixed={abs(a):a>0 for a in partial}
        expected=canonical(tuple(tuple(x for x in c if abs(x) not in fixed) for c in cnf if not any(abs(x) in fixed and fixed[abs(x)]==(x>0) for x in c)))
        assert m.sat_restrict(n,cnf,partial)==expected


def test_exhaustive_binary_clause_families():
    for n in range(3):
        clauses=tuple(tuple(i+1 if sign==1 else -i-1 for i,sign in enumerate(pattern) if sign) for pattern in it.product((0,-1,1),repeat=n))
        for size in range(min(3,len(clauses))+1):
            for cnf in it.combinations(clauses,size):check(n,cnf)
    for cnf in (((1,2),(-1,3),(-2,-3)),((1,),(2,),(-1,-2)),((),),(),((1,2),(-1,2),(1,-2),(-1,-2))):check(3,cnf)


def test_propagation_independent_round_simulation():
    menu=((),(1,),(-1,),(2,),(-2,),(1,2),(1,-2),(-1,2),(-1,-2))
    for size in range(4):
        for cnf in it.combinations(menu,size):
            residual=[set(c) for c in cnf];assigned={};conflict=False
            while True:
                if any(not c for c in residual):conflict=True;break
                units={next(iter(c)) for c in residual if len(c)==1}
                if not units:break
                if any(-a in units for a in units):conflict=True;break
                for a in units:assigned[abs(a)]=a>0
                residual=[{a for a in c if -a not in units} for c in residual if not c & units]
            result=m.sat_unit_propagate(2,cnf)
            if conflict:assert result is None
            else:assert result==(canonical(tuple(tuple(c) for c in residual)),tuple(a if v else -a for a,v in sorted(assigned.items())))


def test_equivalence_exhaustive():
    menu=((),((),),((1,),),((-1,),),((1,2),),((-1,-2),),((2,),),((1,),(-2,)))
    for left,right in it.product(menu,repeat=2):
        a,b=set(truth(2,left)),set(truth(2,right));diff=sorted(a^b)
        assert m.sat_equivalent(2,left,right)==((False,diff[0]) if diff else (True,None))


def refuse(fn,args,code):
    saved=copy.deepcopy(args)
    with pytest.raises(ValueError) as exc:fn(*args)
    assert str(exc.value)=='S490:'+code
    assert args==saved


def test_validation_every_route():
    class I(int):pass
    class T(tuple):pass
    names=('sat_evaluate','sat_models','sat_count','sat_restrict','sat_unit_propagate','sat_backbone','sat_hamming_profile','sat_minimal_unsat_cores','sat_equivalent','sat_forced_implications')
    for name in names:
        fn=getattr(m,name);tail=(0,) if name=='sat_evaluate' else (((),) if name in ('sat_restrict','sat_equivalent') else ())
        for n,code in ((True,'type:n'),(I(1),'type:n'),(1.0,'type:n'),(-1,'bound:n'),(11,'bound:n')):refuse(fn,(n,None)+tail,code)
        for cnf,code in ((None,'type:cnf'),([], 'type:cnf'),(T(()),'type:cnf'),((None,)*9,'length:cnf'),((None,),'type:clause'),((T(()),),'type:clause'),((tuple(range(11)),),'length:clause'),(((True,),),'type:literal'),(((I(1),),),'type:literal'),(((0,),),'bound:literal'),(((3,),),'bound:literal'),(((-3,),),'bound:literal'),(((1,1),),'duplicate:variable'),(((1,-1),),'duplicate:variable'),(((1,),(1,)),'duplicate:clause'),(((1,2),(2,1)),'duplicate:clause'),(((0,),(True,)),'type:literal')):refuse(fn,(2,cnf)+tail,code)
    for bad,code in ((True,'type:mask'),(-1,'bound:mask'),(4,'bound:mask'),(0.0,'type:mask')):refuse(m.sat_evaluate,(2,(),bad),code)
    for partial,code in ((None,'type:partial'),((None,)*3,'length:partial'),((True,),'type:partial:literal'),((0,),'bound:partial:literal'),((3,),'bound:partial:literal'),((-3,),'bound:partial:literal'),((1,1),'duplicate:partial'),((1,-1),'duplicate:partial')):refuse(m.sat_restrict,(2,(),partial),code)
    refuse(m.sat_equivalent,(2,(),None),'type:cnf')


def test_caps_endpoints_and_scope():
    cnf=tuple((i,) for i in range(1,9))
    assert m.sat_count(10,cnf)==4
    assert m.sat_models(0,())==(0,)
    assert m.sat_count(10,())==1024
    assert m.sat_evaluate(10,(),1023) is True
    refuse(m.sat_evaluate,(10,(),1024),'bound:mask')
    assert m.sat_count(10,(tuple(range(1,11)),))==1023
    assert m.sat_restrict(10,(tuple(range(1,11)),),tuple(range(-10,0)))==((),)
    assert m.sat_unit_propagate(10,cnf)==((),tuple(range(1,9)))
    assert m.sat_minimal_unsat_cores(10,((1,),(-1,),(2,),(-2,),(3,),(-3,),(4,),(-4,)))==((0,1),(2,3),(4,5),(6,7))
    assert m.CLAIMS=={'agi_like_intelligence':False,'production_ready':False,'unbounded_solver':False}
    assert all(type(v)is bool and v is False for v in m.CLAIMS.values())
    assert m.SCOPE=='PARTIAL exact finite CNF counting, conditioning and certificates'
    assert m.NOT_CLAIMED==('AGI-like intelligence','unbounded SAT solving','production readiness','proof-system completeness')


@pytest.fixture(autouse=True)
def bounded_solver_trace(monkeypatch):
    import sys
    for name in ('sat_count','sat_unit_propagate','sat_backbone','sat_minimal_unsat_cores','sat_forced_implications'):
        original=getattr(m,name)
        def guarded(*args,original=original):
            count=0
            def trace(frame,event,arg):
                nonlocal count
                if frame.f_code.co_filename!=m.__file__:return None
                if event=='line':
                    count+=1
                    if count>500000:raise AssertionError('bounded SAT traversal exceeded step budget')
                return trace
            old=sys.gettrace();sys.settrace(trace)
            try:return original(*args)
            finally:sys.settrace(old)
        monkeypatch.setattr(m,name,guarded)

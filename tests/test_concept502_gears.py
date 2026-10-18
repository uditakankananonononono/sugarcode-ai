import itertools as it
from fractions import Fraction as F
from math import gcd
import pytest
from sugarcode.extra_doc import concept502_gears as m


def oracle(teeth,signs):
    # Direct endpoint tooth quotient and parity, no iterative ratio propagation.
    out=[]
    for i,t in enumerate(teeth):
        negative=sum(s==-1 for s in signs[:i])%2
        out.append(F((-1 if negative else 1)*teeth[0],t))
    return tuple(out)


def check(teeth,signs):
    ratios=oracle(teeth,signs);assert m.ratio_vector(teeth,signs)==ratios
    for drive in (-20,-1,0,1,20):assert m.velocity_vector(teeth,signs,drive)==tuple(drive*r for r in ratios)
    # Brute-force return search bounded by lcm of tooth counts.
    limit=1
    for t in teeth:limit=limit*t//gcd(limit,t)
    period=next(k for k in range(1,limit+1) if all((k*teeth[0])%t==0 for t in teeth))
    assert m.primitive_turn_cycle(teeth,signs)==(period,tuple(int(period*r) for r in ratios))
    assert m.signed_tooth_products(teeth,signs)==tuple(teeth[0]*(-1 if sum(s==-1 for s in signs[:i])%2 else 1) for i in range(len(teeth)))
    assert m.reverse_chain_certificate(teeth,signs)is True
    for i,j in it.product(range(len(teeth)),repeat=2):assert m.pair_transfer(teeth,signs,i,j)==F(teeth[i],teeth[j])*(-1 if sum(s==-1 for s in signs[min(i,j):max(i,j)])%2 else 1)
    for s in (-1,1):assert m.closure_residual(teeth,signs,s)==teeth[0]*(1-s*(-1 if sum(x==-1 for x in signs)%2 else 1))
    assert m.synchronized_pairs(teeth,signs)==tuple((i,j) for i in range(len(teeth)) for j in range(i+1,len(teeth)) if teeth[i]==teeth[j] and sum(s==-1 for s in signs[i:j])%2==0)
    for cap in (0,1,20):assert m.integer_drive_options(teeth,signs,cap)==tuple(k for k in range(1,cap+1) if all(k*teeth[0]%t==0 for t in teeth))
    for turns in (0,1,2,99,100):assert m.phase_return_certificate(teeth,signs,turns)is all(turns*teeth[0]%t==0 for t in teeth)


def test_exhaustive_small_chains_and_endpoints():
    for n in range(2,5):
        for teeth in it.product(range(1,4),repeat=n):
            for signs in it.product((-1,1),repeat=n-1):check(teeth,signs)
    for t,s in (((40,1),(1,)),((1,40),(-1,)),((40,)*8,(-1,)*7),((2,3,4,5,6,8,10,12),(1,-1,1,-1,-1,1,1))):check(t,s)


def refuse(fn,args,code):
    with pytest.raises(ValueError) as exc:fn(*args)
    assert str(exc.value)=='G502:'+code


def test_input_contract_scope_and_purity():
    class I(int):pass
    class T(tuple):pass
    routes=((m.ratio_vector,()),(m.velocity_vector,(0,)),(m.primitive_turn_cycle,()),(m.signed_tooth_products,()),(m.reverse_chain_certificate,()),(m.pair_transfer,(0,0)),(m.closure_residual,(1,)),(m.synchronized_pairs,()),(m.integer_drive_options,(0,)),(m.phase_return_certificate,(0,)))
    for fn,tail in routes:
        for teeth,signs,code in ((None,None,'type:teeth'),(T((1,1)),None,'type:teeth'),((1,),None,'length:teeth'),((True,)*9,None,'length:teeth'),((True,1),None,'type:tooth'),((I(1),1),None,'type:tooth'),((0,1),None,'bound:tooth'),((41,1),None,'bound:tooth'),((1,1),None,'shape:signs'),((1,1),T((1,)),'shape:signs'),((1,1),(True,),'type:sign'),((1,1),(I(1),),'type:sign'),((1,1),(0,),'bound:sign'),((1,1),(2,),'bound:sign')):refuse(fn,(teeth,signs)+tail,code)
    for fn,label,lo,hi in ((m.velocity_vector,'drive',-20,20),(m.integer_drive_options,'cap',0,20),(m.phase_return_certificate,'turns',0,100),(m.closure_residual,'closing_sign',-1,1)):
        for value,code in ((True,'type:'+label),(I(1),'type:'+label),(lo-1,'bound:'+label),(hi+1,'bound:'+label)):refuse(fn,((1,1),(1,),value),code)
    refuse(m.closure_residual,((1,1),(1,),0),'zero:closing_sign')
    for i in (0,1):
        for value,code in ((True,'type:'),(-1,'bound:'),(2,'bound:')):
            args=[0,0];args[i]=value;refuse(m.pair_transfer,((1,1),(1,))+tuple(args),code+('source' if i==0 else 'destination'))
    assert m.CLAIMS=={'agi_like_intelligence':False,'engineering_validity':False,'production_ready':False}
    assert m.SCOPE=='PARTIAL abstract signed tooth-ratio chain fixtures, rational-constraint adjacency disclosed'
    assert m.NOT_CLAIMED==('AGI-like intelligence','engineering validity','physical mechanism feasibility','power or load analysis','production readiness')

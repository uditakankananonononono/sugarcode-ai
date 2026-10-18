import itertools as it
import random
import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import concept493_sedenion as m

# Independent signed basis table doubling from 1D, then bilinear expansion.
def table(n):
    if n==1:return {(0,0):(1,0)}
    old=table(n//2);h=n//2;out={}
    for i,j in it.product(range(n),repeat=2):
        if i<h and j<h:s,k=old[i,j];out[i,j]=(s,k)
        elif i<h<=j:s,k=old[j-h,i];out[i,j]=(s,k+h)
        elif j<h<=i:s,k=old[i-h,j];out[i,j]=(s*(1 if j==0 else -1),k+h)
        else:s,k=old[j-h,i-h];out[i,j]=(-s*(1 if j-h==0 else -1),k)
    return out
T=table(16)


def mul(a,b):
    v=[F(0)]*16
    for i,x in enumerate(a):
        if not x:continue
        for j,y in enumerate(b):
            if y:s,k=T[i,j];v[k]+=s*x*y
    return tuple(v)


def norm(a):return sum(x*x for x in a)
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def catalogue():return tuple(tuple(1 if k==i else sign if k==j else 0 for k in range(16)) for i,j in it.combinations(range(16),2) for sign in (-1,1))


def rank(matrix):
    # Independent column elimination using existing pivot vectors as a basis.
    basis={}
    for column in zip(*matrix):
        v=list(map(F,column))
        for pivot,b in sorted(basis.items()):
            ratio=v[pivot];v=[x-ratio*y for x,y in zip(v,b)]
        p=next((i for i,x in enumerate(v) if x),None)
        if p is not None:
            q=v[p];basis[p]=[x/q for x in v]
    return len(basis)


def test_basis_products_and_random_failure_oracles():
    basis=tuple(tuple(int(i==j) for i in range(16)) for j in range(16));zero=(0,)*16
    for a,b in it.product(basis,repeat=2):assert m.zero_product_certificate(a,b)==(mul(a,b),False)
    rng=random.Random(493);saw_norm=saw_alt=saw_moufang=False
    for _ in range(80):
        a,b,c=(tuple(rng.randint(-2,2) for i in range(16)) for j in range(3))
        expected=mul(a,b)
        assert m.zero_product_certificate(a,b)==(expected,bool(any(a) and any(b) and not any(expected)))
        defect=norm(expected)-norm(a)*norm(b);assert m.norm_defect(a,b)==defect;saw_norm|=bool(defect)
        alt=(sub(mul(mul(a,a),b),mul(a,mul(a,b))),sub(mul(mul(b,a),a),mul(b,mul(a,a))))
        assert m.alternativity_defect(a,b)==alt;saw_alt|=any(alt[0]) or any(alt[1])
        defect=sub(mul(mul(a,b),mul(c,a)),mul(a,mul(mul(b,c),a)))
        assert m.moufang_defect(a,b,c)==defect;saw_moufang|=any(defect)
    assert saw_norm and saw_alt and saw_moufang


def test_zero_divisors_kernel_rank_and_catalogue_oracles():
    cat=catalogue();zero=(0,)*16;basis=tuple(tuple(int(i==j) for i in range(16)) for j in range(16))
    samples=(zero,)+basis+(cat[0],cat[20],cat[40],cat[60],cat[100],cat[140],cat[180],cat[220])
    found=False
    for a in samples:
        products=[mul(a,b) for b in cat]
        expected=next((b for b,p in zip(cat,products) if not any(p)),None) if any(a) else None
        assert m.zero_divisor_witness(a)==expected
        expected_all=tuple(b for b,p in zip(cat,products) if not any(p) and not any(mul(b,a))) if any(a) else ()
        assert m.signed_basis_pair_zero_divisors(a)==expected_all
        found|=bool(expected_all)
        for left,basis_fn,dim_fn in ((True,m.left_kernel_basis,m.left_annihilator_dimension),(False,m.right_kernel_basis,m.right_annihilator_dimension)):
            cols=[mul(a,e) if left else mul(e,a) for e in basis];matrix=tuple(zip(*cols));kernel=basis_fn(a)
            assert len(kernel)==16-rank(matrix)==dim_fn(a)
            assert all(type(v)is tuple and len(v)==16 and all(type(x)is F for x in v) for v in kernel)
            assert rank(tuple(zip(*kernel)))==len(kernel) if kernel else True
            for v in kernel:assert (mul(a,v) if left else mul(v,a))==zero
    assert found


def test_all_validations_caps_scope():
    class I(int):pass
    class T(tuple):pass
    one=(1,)+(0,)*15;zero=(0,)*16
    names={'zero_product_certificate':2,'left_kernel_basis':1,'right_kernel_basis':1,'left_annihilator_dimension':1,'right_annihilator_dimension':1,'norm_defect':2,'alternativity_defect':2,'moufang_defect':3,'zero_divisor_witness':1,'signed_basis_pair_zero_divisors':1}
    for name,arity in names.items():
        fn=getattr(m,name)
        for pos in range(arity):
            for bad,code in ((None,'shape:sedenion'),([0]*16,'shape:sedenion'),(T(zero),'shape:sedenion'),((0,)*15,'shape:sedenion'),((0,)*17,'shape:sedenion'),((True,)+(0,)*15,'type:coordinate'),((I(0),)+(0,)*15,'type:coordinate'),((0.0,)+(0,)*15,'type:coordinate'),((3,)+(0,)*15,'bound:coordinate'),((-3,)+(0,)*15,'bound:coordinate')):
                args=[one]*arity;args[pos]=bad;saved=copy.deepcopy(args)
                with pytest.raises(ValueError) as exc:fn(*args)
                assert str(exc.value)=='S493:'+code and args==saved
            for endpoint in (-2,2):
                args=[one]*arity;args[pos]=(endpoint,)*16;fn(*args)
        if arity>1:
            with pytest.raises(ValueError,match='^S493:type:coordinate$'):fn((3,)+(0,)*15,(True,)+(0,)*15,*([one]*(arity-2)))
    assert m.zero_product_certificate(zero,one)==(zero,False)
    assert m.left_annihilator_dimension(zero)==16
    assert m.right_annihilator_dimension(one)==0
    assert m.CLAIMS=={'agi_like_intelligence':False,'production_ready':False,'global_zero_divisor_decision':False}
    assert m.SCOPE=='PARTIAL sedenion zero-divisor and failed-composition certificates, adjacent octonions disclosed'
    assert m.NOT_CLAIMED==('AGI-like intelligence','new octonion arithmetic','global zero-divisor decision','physical validity','production readiness')

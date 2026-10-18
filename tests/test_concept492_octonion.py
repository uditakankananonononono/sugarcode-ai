import itertools as it
import random
import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import concept492_octonion as m

# Independent signed basis multiplication table from oriented Fano triples.
TRIPLES=((1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5))
TABLE={(0,i):(1,i) for i in range(8)}
TABLE.update({(i,0):(1,i) for i in range(8)})
for i in range(1,8):TABLE[i,i]=(-1,0)
for a,b,c in TRIPLES:
    for x,y,z in ((a,b,c),(b,c,a),(c,a,b)):TABLE[x,y]=(1,z);TABLE[y,x]=(-1,z)


def mul(a,b):
    result=[F(0)]*8
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            sign,k=TABLE[i,j];result[k]+=sign*x*y
    return tuple(result)


def conj(a):return (a[0],)+tuple(-x for x in a[1:])


def sub(a,b):return tuple(x-y for x,y in zip(a,b))


def test_all_basis_and_nonassociative_oracles():
    basis=tuple(tuple(int(i==j) for i in range(8)) for j in range(8));zero=(0,)*8
    for a,b in it.product(basis,repeat=2):
        assert m.octonion_multiply(a,b)==mul(a,b)
        assert m.octonion_commutator(a,b)==sub(mul(a,b),mul(b,a))
        assert m.octonion_alternativity_certificate(a,b)==(zero,zero,zero)
    nonzero=False
    for a,b,c in it.product(basis,repeat=3):
        expected=sub(mul(mul(a,b),c),mul(a,mul(b,c)))
        assert m.octonion_associator(a,b,c)==expected
        nonzero|=any(expected)
        expected_pair=(mul(mul(a,b),mul(c,a)),mul(a,mul(mul(b,c),a)))
        assert m.octonion_moufang_certificate(a,b,c)==expected_pair
        assert expected_pair[0]==expected_pair[1]
    assert nonzero


def test_random_exact_vectors_inverse_division_and_matrix_oracles():
    rng=random.Random(492);one=(1,)+(0,)*7;zero=(0,)*8
    for _ in range(180):
        a,b,c=(tuple(rng.randint(-8,8) for _ in range(8)) for __ in range(3))
        assert m.octonion_multiply(a,b)==mul(a,b)
        assert m.octonion_conjugate(a)==conj(a)
        norm=sum(x*x for x in a)
        assert m.octonion_norm_squared(a)==norm
        assert sum(x*x for x in mul(a,b))==norm*sum(x*x for x in b)
        inverse=m.octonion_inverse(a)
        assert all(type(x)is F for x in inverse)
        assert mul(a,inverse)==one and mul(inverse,a)==one
        quotient=m.octonion_right_divide(a,b)
        assert mul(quotient,b)==a
        matrix=m.octonion_left_matrix(a)
        assert tuple(sum(row[j]*b[j] for j in range(8)) for row in matrix)==mul(a,b)
        assert m.octonion_associator(a,b,c)==sub(mul(mul(a,b),c),mul(a,mul(b,c)))
        assert m.octonion_commutator(a,b)==sub(mul(a,b),mul(b,a))
        assert m.octonion_alternativity_certificate(a,b)==(zero,zero,zero)
        lhs,rhs=m.octonion_moufang_certificate(a,b,c)
        assert lhs==mul(mul(a,b),mul(c,a)) and rhs==mul(a,mul(mul(b,c),a)) and lhs==rhs


def refuse(fn,args,code):
    saved=copy.deepcopy(args)
    with pytest.raises(ValueError) as exc:fn(*args)
    assert str(exc.value)=='O492:'+code
    assert args==saved


def test_exact_shapes_types_caps_and_precedence():
    class I(int):pass
    class T(tuple):pass
    zero=(0,)*8;one=(1,)+(0,)*7
    names={'octonion_multiply':2,'octonion_conjugate':1,'octonion_norm_squared':1,'octonion_inverse':1,'octonion_associator':3,'octonion_commutator':2,'octonion_left_matrix':1,'octonion_right_divide':2,'octonion_alternativity_certificate':2,'octonion_moufang_certificate':3}
    for name,arity in names.items():
        fn=getattr(m,name)
        for pos in range(arity):
            for bad,code in ((None,'shape:octonion'),([0]*8,'shape:octonion'),(T(zero),'shape:octonion'),((0,)*7,'shape:octonion'),((0,)*9,'shape:octonion'),((True,)+(0,)*7,'type:coordinate'),((I(0),)+(0,)*7,'type:coordinate'),((0.0,)+(0,)*7,'type:coordinate'),((float('nan'),)+(0,)*7,'type:coordinate'),((9,)+(0,)*7,'bound:coordinate'),((-9,)+(0,)*7,'bound:coordinate')):
                args=[one]*arity;args[pos]=bad;refuse(fn,tuple(args),code)
            for endpoint in (-8,8):
                args=[one]*arity;args[pos]=(endpoint,)*8;out=fn(*args);assert type(out)in (tuple,int)
        if arity>1:refuse(fn,((9,)+(0,)*7,(True,)+(0,)*7)+(one,)*(arity-2),'type:coordinate')
    refuse(m.octonion_inverse,(zero,),'zero:inverse')
    refuse(m.octonion_right_divide,(one,zero),'zero:denominator')
    refuse(m.octonion_right_divide,((9,)+(0,)*7,zero),'bound:coordinate')
    assert m.octonion_inverse(one)==tuple(map(F,one))
    assert m.octonion_right_divide(zero,one)==tuple(map(F,zero))
    assert m.CLAIMS=={'agi_like_intelligence':False,'production_ready':False,'geometric_validity':False}
    assert m.SCOPE=='PARTIAL bounded exact octonion nonassociativity fixtures, quaternion adjacency disclosed'
    assert m.NOT_CLAIMED==('AGI-like intelligence','new quaternion algebra','geometric validity','production readiness')


def test_left_matrix_exact_dimensions_and_integer_output():
    a=(1,2,3,4,5,6,7,8)
    matrix=m.octonion_left_matrix(a)
    assert type(matrix)is tuple and len(matrix)==8
    assert all(type(row)is tuple and len(row)==8 for row in matrix)
    assert all(type(x)is int for row in matrix for x in row)
    expected=tuple(tuple(int(v) for v in mul(a,tuple(int(j==k) for j in range(8)))) for k in range(8))
    assert matrix==tuple(zip(*expected))

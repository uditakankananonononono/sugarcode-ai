from fractions import Fraction
import itertools
import pytest
from sugarcode.extra_doc.gibbs1034 import sweep


def test_independent_joint_table_oracle():
    for cells in itertools.product((1,3),repeat=4):
        weights=[list(cells[:2]),list(cells[2:])];joint=dict(zip(itertools.product((0,1),repeat=2),cells))
        for y,u,v in itertools.product((0,1),(Fraction(0),Fraction(1,2),Fraction(3,4)),(Fraction(0),Fraction(1,2),Fraction(3,4))):
            px=Fraction(sum(m for (a,b),m in joint.items() if a==1 and b==y),sum(m for (a,b),m in joint.items() if b==y));x=int(u<px)
            py=Fraction(sum(m for (a,b),m in joint.items() if a==x and b==1),sum(m for (a,b),m in joint.items() if a==x));new_y=int(v<py)
            got=sweep(weights,(0,y),((u.numerator,u.denominator),(v.numerator,v.denominator)))
            assert got['state']==(x,new_y) and got['conditionals']==((px.numerator,px.denominator),(py.numerator,py.denominator))
            assert got['claim']=='PARTIAL' and got['convergence_validated'] is False

class L(list):pass
class T(tuple):pass
class I(int):pass
@pytest.mark.parametrize('weights,state,draws,message',[
 (L([[1,1],[1,1]]),(0,0),((0,1),(0,1)),'weights must be an exact two by two list'),
 ([[1,1],[1]],(0,0),((0,1),(0,1)),'weights must be an exact two by two list'),
 *[([[x,1],[1,1]],(0,0),((0,1),(0,1)),'weights must be integers in 1..100') for x in (True,I(1),0,101)],
 *[([[1,1],[1,1]],x,((0,1),(0,1)),'state must be an exact tuple of binary integers') for x in (T((0,0)),(True,0),(I(0),0),(0,2))],
 ([[1,1],[1,1]],(0,0),T(((0,1),(0,1))),'draws must be an exact tuple of two fractions'),
 *[([[1,1],[1,1]],(0,0),(x,(0,1)),'draws must be exact integer fractions with 0<=num<den<=100') for x in (T((0,1)),(True,2),(I(0),2),(-1,2),(2,2),(0,101))],
])
def test_invalid(weights,state,draws,message):
    with pytest.raises(ValueError) as exc:sweep(weights,state,draws)
    assert str(exc.value)==message


def test_equal_draw_chooses_zero_and_maximum():
    assert sweep([[100,100],[100,100]],(1,1),((1,2),(1,2)))['state']==(0,0)

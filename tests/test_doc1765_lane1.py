import random
import pytest
from sugarcode.extra_doc.game1765 import pure_equilibria
class L(list):pass
class T(tuple):pass
class I(int):pass


def test_independent_unilateral_deviation_oracle():
    rng=random.Random(1765)
    for _ in range(100):
        height=rng.randint(2,6);width=rng.randint(2,6);m=[[(rng.randint(-3,3),rng.randint(-3,3)) for j in range(width)] for i in range(height)]
        rb=[(j,[i for i in range(height) if all(m[i][j][0]>=m[k][j][0] for k in range(height))]) for j in range(width)]
        cb=[(i,[j for j in range(width) if all(m[i][j][1]>=m[i][k][1] for k in range(width))]) for i in range(height)]
        eq=[(i,j) for i in range(height) for j in range(width) if all(m[i][j][0]>=m[k][j][0] for k in range(height)) and all(m[i][j][1]>=m[i][k][1] for k in range(width))]
        assert pure_equilibria(m)=={'equilibria':eq,'row_best':rb,'col_best':cb,'claim':'PARTIAL','behavior_validated':False}

@pytest.mark.parametrize('matrix,message',[
 *[(x,'matrix must be an exact list with 2..10 rows') for x in (None,L([[(0,0)]*2]*2),tuple([[(0,0)]*2]*2),[],[[(0,0)]*2],[[(0,0)]*2]*11)],
 *[([x,[(0,0)]*2],'rows must be exact lists with 2..10 cells') for x in (None,L([(0,0)]*2),((0,0),(0,0)),[],[(0,0)],[(0,0)]*11)],
 ([[(0,0)]*2,[(0,0)]*3],'matrix rows must have equal widths'),
 *[([[x,(0,0)],[(0,0)]*2],'cell must be a two-payoff tuple') for x in (None,[0,0],T((0,0)),(0,),(0,0,0))],
 *[([[(x,0),(0,0)],[(0,0)]*2],'payoffs must be exact integers in -1000..1000') for x in (None,True,I(0),1.5,-1001,1001)],
 *[([[(0,x),(0,0)],[(0,0)]*2],'payoffs must be exact integers in -1000..1000') for x in (None,True,I(0),1.5,-1001,1001)],
])
def test_invalid(matrix,message):
    with pytest.raises(ValueError) as exc:pure_equilibria(matrix)
    assert str(exc.value)==message


def test_caps_all_ties_and_matching_pennies_no_equilibrium():
    got=pure_equilibria([[(-1000,1000)]*10 for i in range(10)]);assert got['equilibria']==[(i,j) for i in range(10) for j in range(10)]
    assert pure_equilibria([[(1,-1),(-1,1)],[(-1,1),(1,-1)]])['equilibria']==[]
